from pathlib import Path
from code_tests.timeout import function_timeout, TimeoutException
from main_modules import calendar
import pytest
from unittest.mock import patch, MagicMock
from utils import enums
import api.schemas.all as schemas


@pytest.fixture
def mock_db():
    mock_instance = MagicMock()
    mock_instance.events.create = MagicMock()
    mock_instance.events.get_all_until_run_threshold.return_value = []
    mock_instance.events.delete = MagicMock()
    mock_instance.tests.get_by_id.return_value = MagicMock(version=1)
    mock_instance.requests.delete = MagicMock()
    mock_instance.runs.create = MagicMock()
    return mock_instance


@pytest.fixture
def mock_test():
    mock_instance = MagicMock()
    mock_instance.id_test = 1
    mock_instance.version = 2
    mock_instance.state = enums.TestState.enabled
    return mock_instance


@pytest.fixture
def mock_event():
    mock_instance = MagicMock()
    mock_instance.id_test = 1
    mock_instance.run_at = 1000
    mock_instance.id_event = 10
    mock_instance.source = enums.EventSource.calendar
    mock_event.recovery_attempt = 0
    return mock_instance


@pytest.fixture
def mock_request():
    mock_instance = MagicMock()
    mock_instance.id_test = 1
    mock_instance.reason = enums.RequestReason.new
    mock_instance.id_request = 20
    mock_instance.recovery_attempt = 3
    return mock_instance


@pytest.mark.parametrize(
    "run_at, source, recovery_attempt, transaction_finished",
    [
        (1000, enums.EventSource.calendar, 0, None),
        (0, enums.EventSource.calendar, 0, None),  # running at time zero is allowed
        (1000, enums.EventSource.recovery, 0, None),  # different source
        (1000, enums.EventSource.calendar, 1, None),  # first recovery attempt
        (1000, enums.EventSource.calendar, 1000, None),  # high recovery attempt
        (1000, enums.EventSource.calendar, 0, False),  # unfinished transaction
    ]
)
def test_insert_into_calendar(mock_db, mock_test, run_at, source: enums.EventSource, recovery_attempt, transaction_finished):
    with patch("utils.logs.debug") as mock_logs:
        calendar.insert_into_calendar(mock_db, mock_test, run_at, source, recovery_attempt, transaction_finished)

    mock_db.events.create.assert_called_once_with(id_test=1, data=schemas.EventCreate(run_at=run_at, source=source.value, recovery_attempt=recovery_attempt), transaction_finished=transaction_finished)
    mock_logs.assert_called_once()


@pytest.mark.parametrize(
    "scheduling_interval, scheduling_until, previous_run, now, expected_result",
    [
        (None, 1500, 900, 1000, None),
        (200, 1100, 1000, 1000, None),
        (100, 2500, 900, 2000, 2000),

        (999999, 1500, 900, 1000, None),
        (0, 1500, 900, 1000, None),  # interval is zero, should not be scheduled
        (110.5, 1500, 900, 1000, 1010.5),

        (100, 0, 900, 1000, None),  # current run is behind the scheduling_until
        (100, 1500.5, 900, 1000, 1000),

        (100, 1500, 0, 1000, 1000),
        (100, 1500, 999999, 1000, None),
        (100, 1500, 900.5, 1000, 1000.5),

        (100, 1500, 900, 0, 1000),
        (100, 1500, 900, 1000.5, 1000.5),
        (100, 1500, 900, 999999, None),

        (100, 1500, 900, 1000, 1000)
    ]
)
def test_ProcessEvents__calculate_next_event_time(mock_test, scheduling_interval, scheduling_until, previous_run, now, expected_result):
    mock_test.scheduling_interval = scheduling_interval
    mock_test.scheduling_until = scheduling_until

    x = calendar.ProcessEvents()
    x._now = now
    result = x._calculate_next_event_time(mock_test, previous_run)
    assert result == expected_result


@pytest.mark.parametrize(
    "previous_run, next_event_time, event_planned",
    [
        (900, 1000, True),
        (1000, 1000, True),
        (0, 0, True),
        (1000, None, False)
    ]
)
def test_ProcessEvents__plan_next_event(mock_db, mock_test, previous_run, next_event_time, event_planned):
    with patch.object(calendar.ProcessEvents, "_calculate_next_event_time", return_value=next_event_time) as mock_calculate_next_event_time:
        with patch("main_modules.calendar.insert_into_calendar", return_value="doesnt_matter") as mock_insert_into_calendar:
            processor = calendar.ProcessEvents()
            processor._db = mock_db
            processor._plan_next_event(mock_test, previous_run)

    mock_calculate_next_event_time.assert_called_once()
    if event_planned:
        mock_insert_into_calendar.assert_called_once_with(mock_db, mock_test, next_event_time, enums.EventSource.calendar, transaction_finished=False)
    else:
        mock_insert_into_calendar.assert_not_called()


@pytest.mark.parametrize(
    "requests_count",
    [
        0,
        1,
        5,
    ]
)
def test_RequestsForNewEvents_process_all_requests(mock_db, mock_request, requests_count):
    returned_requests = [mock_request for _ in range(requests_count)]
    mock_db.requests.get_all.return_value = returned_requests

    with patch.object(calendar.RequestsForNewEvents, "_process_request", return_value=None) as mock_process_request:
        processor = calendar.RequestsForNewEvents(mock_db)
        processor.process_all_requests()

    assert mock_process_request.call_count == requests_count


@pytest.mark.parametrize(
    "request_reason, function_name",
    [
        (enums.RequestReason.new, "_process_new_request"),
        (enums.RequestReason.update, "_process_update_request"),
        (enums.RequestReason.failed, "_process_recovery_request"),
    ]
)
def test_RequestsForNewEvents_process_request(mock_db, mock_request, request_reason, function_name):
    mock_request.reason = request_reason
    with patch.object(calendar.RequestsForNewEvents, function_name, return_value=None) as mock_process_function:
        processor = calendar.RequestsForNewEvents(mock_db)
        processor._process_request(mock_request)

    mock_db.requests.delete.assert_called_once_with(mock_request.id_request)
    assert mock_process_function.call_count == 1


@pytest.mark.parametrize(
    "now, scheduling_from, scheduling_interval, scheduling_until, create_run, next_event_at",
    [
        # Basic scheduling from now with a valid interval and future end time
        (1, 0, 5, 100, True, 6),

        # No scheduling interval - still should be executed
        (1, 0, None, 100, True, None),

        # Zero scheduling interval (edge case) - should NOT be scheduled (immediate reschedule could cause trouble when looping)
        (1, 0, 0, 100, True, None),

        # Scheduling with no end time
        (1, 0, 5, None, True, 0),

        # Start time in the future (no immediate execution)
        (1, 10, 5, 100, False, 10),

        # Scheduling end time is in the past (nothing executed nor scheduled)
        (1000, 0, 5, 100, True, None),

        # Schedule from is not specified
        (1, None, 5, 100, True, 6),

        # Edge case where scheduling starts and ends at the same time (executed, not scheduled)
        (1, 1, 5, 1, True, None),

        # Very large interval
        (1, 0, 999999, None, True, 1000000),
    ]
)
def test_RequestsForNewEvents_process_new_request(mock_db, mock_test, mock_request, now, scheduling_from, scheduling_interval, scheduling_until, create_run, next_event_at):
    mock_test.scheduling_from = scheduling_from
    mock_test.scheduling_until = scheduling_until

    with patch("main_modules.calendar.insert_into_calendar", return_value="doesnt_matter") as mock_insert_into_calendar:
        with patch.object(calendar.RequestsForNewEvents, "_plan_next_event", return_value=None) as mock_plan_next_event:
            processor = calendar.RequestsForNewEvents(mock_db)
            processor._now = now
            processor._process_new_request(mock_request, mock_test)

    if not create_run:
        mock_plan_next_event.assert_not_called()
        mock_insert_into_calendar.assert_called_once_with(mock_db, mock_test, next_event_at, enums.EventSource.request)
    else:
        mock_insert_into_calendar.assert_not_called()
        mock_plan_next_event.assert_called_once_with(mock_test, now)


@pytest.mark.parametrize(
    "state, delete_planned_events, plan_new_event",
    [
        (enums.TestState.enabled, False, True),
        (enums.TestState.disabled, True, False),
        (enums.TestState.deleted, True, False),
        (enums.TestState.migrating_from, False, False),
        (enums.TestState.migrating_to, False, False),
    ]
)
def test_RequestsForNewEvents_process_update_request(mock_db, mock_test, mock_request, state, delete_planned_events, plan_new_event):
    mock_test.state = state

    with patch.object(calendar.RequestsForNewEvents, "_process_new_request", return_value=None) as mock_process_new_request:
        processor = calendar.RequestsForNewEvents(mock_db)
        processor._process_update_request(mock_request, mock_test)

    if delete_planned_events:
        mock_db.events.delete.assert_called_once_with(1)

    if plan_new_event:
        mock_process_new_request.assert_called_once()
    else:
        mock_process_new_request.assert_not_called()

@pytest.mark.parametrize(
    "now, recovery_attempt_limit, recovery_interval, scheduling_until, recovery_event_at",
    [
        # Recovery attempts allowed, scheduling until future time
        (1000, 3, 300, 2000, 1300),

        # No recovery attempts allowed
        (1000, 0, 300, 2000, None),

        # Recovery interval is None - don't plan anything
        (1000, 3, 0, 2000, None),

        # Recovery interval is zero (edge case) - same as None, don't plan anything
        (1000, 3, 0, 2000, None),

        # Scheduling ends before the next recovery attempt
        (1000, 3, 300, 1100, None),

        # No scheduling end time - plan normally
        (1000, 3, 300, None, 1300),

        # Max recovery attempts reached
        (1000, 2, 300, 2000, None),

        # No recovery
        (1000, None, 300, 2000, None),
    ]
)
def test_RequestsForNewEvents_process_recovery_request(mock_db, mock_test, mock_request, now, recovery_attempt_limit, recovery_interval, scheduling_until, recovery_event_at):
    mock_test.recovery_attempt_limit = recovery_attempt_limit
    mock_test.recovery_interval = recovery_interval
    mock_test.scheduling_until = scheduling_until

    with patch("main_modules.calendar.insert_into_calendar", return_value="doesnt_matter") as mock_insert_into_calendar:
        processor = calendar.RequestsForNewEvents(mock_db)
        processor._now = now
        processor._process_recovery_request(mock_request, mock_test)

    if recovery_event_at:
        mock_insert_into_calendar.assert_called_once_with(mock_db, mock_test, recovery_event_at, enums.EventSource.recovery, mock_request.recovery_attempt)


@pytest.mark.parametrize(
    "events_count",
    [
        0,
        1,
        5,
    ]
)
def test_PlannedEvents_process_all_events(mock_db, mock_event, events_count):
    returned_events = [mock_event for _ in range(events_count)]
    mock_db.events.get_all_until_run_threshold.return_value = returned_events

    with patch.object(calendar.PlannedEvents, "_process_one_event", return_value=None) as mock_process_one_event:
        processor = calendar.PlannedEvents(mock_db)
        processor.process_all_events()

    assert mock_process_one_event.call_count == events_count


@pytest.mark.parametrize(
    "event_source, planned_events_count",
    [
        (enums.EventSource.recovery, 0),
        (enums.EventSource.calendar, 1),
        (enums.EventSource.request, 1),
    ]
)
def test_PlannedEvents_process_one_event(mock_db, mock_test, mock_event, event_source, planned_events_count):
    mock_event.source = event_source
    mock_db.tests.get_by_id.return_value = mock_test

    with patch.object(calendar.PlannedEvents, "_start_a_new_run", return_value=None) as mock_start_a_new_run:
        with patch.object(calendar.PlannedEvents, "_plan_next_event", return_value=None) as mock_plan_next_event:
            processor = calendar.PlannedEvents(mock_db)
            processor._process_one_event(mock_event)

    mock_start_a_new_run.assert_called_once_with(mock_test, mock_event, transaction_finished=False)
    assert mock_plan_next_event.call_count == planned_events_count
    mock_db.events.delete.assert_called_once_with(mock_event.id_event, transaction_finished=True)


@pytest.mark.parametrize(
    "run_at, transaction_finished, already_planned_run",
    [
        (1000, True, False),
        (1000, False, False),
        (1000, True, True),
        (1000, False, True),
        (0, True, False),  # running at time zero is allowed
    ]
)
def test_PlannedEvents_start_a_new_run(mock_db, mock_test, mock_event, run_at, transaction_finished, already_planned_run):
    db_get_result = ["something"] if already_planned_run else []
    mock_db.runs.get_all_by_test_id_and_state.return_value = db_get_result
    mock_event.run_at = run_at

    with patch("utils.logs.debug"):
        with patch("utils.logs.warning") as mock_logs_warning:
            processor = calendar.PlannedEvents(mock_db)
            processor._start_a_new_run(mock_test, mock_event, transaction_finished=transaction_finished)

    mock_db.runs.get_all_by_test_id_and_state.assert_called_once()
    if already_planned_run:
        mock_logs_warning.assert_called_once()
        mock_db.runs.create.assert_not_called()
    else:
        mock_logs_warning.assert_not_called()
        mock_db.runs.create.assert_called_once_with(mock_test.id_test,
                                                    mock_test.version,
                                                    enums.RunState.waiting,
                                                    mock_event.run_at,
                                                    mock_event.recovery_attempt,
                                                    transaction_finished)


def test_process_events():
    with patch.object(calendar.RequestsForNewEvents, "process_all_requests", return_value=None) as mock_new_events:
        with patch.object(calendar.PlannedEvents, "process_all_events", return_value=None) as mock_planned_events:
            calendar.process_events()
    mock_new_events.assert_called_once()
    mock_planned_events.assert_called_once()


def test_main():
    with patch("utils.configuration.config.load_config", return_value='doesnt_matter') as mock_load_config:
        with patch("utils.logs.setup_logging", return_value='doesnt_matter') as mock_setup_logging:
            with patch("main_modules.initialization.pre_running_check", return_value='doesnt_matter') as mock_pre_running_check:
                with patch("main_modules.calendar.infinite_loop_for_processing_events", return_value='doesnt_matter') as mock_infinite_loop:
                    calendar.main(Path("."))
    mock_load_config.assert_called_once()
    mock_setup_logging.assert_called_once()
    mock_pre_running_check.assert_called_once()
    mock_infinite_loop.assert_called_once()


def test_infinite_loop_for_processing_events_loop_test():
    with patch("main_modules.calendar.process_events", return_value="doesnt_matter") as mock_process_events:
        func = function_timeout(timeout=1.0)(calendar.infinite_loop_for_processing_events)
        try:
            func()
        except TimeoutException:
            pass
    call_count = mock_process_events.call_count
    assert 5 < call_count < 12
