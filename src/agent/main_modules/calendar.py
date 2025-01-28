import time
from pathlib import Path
from typing import Optional

import api.schemas.all as schemas
import database.models.all as models
import main_modules.initialization as initialization
from database.daoaggregator import DAOAggregator
from utils import enums, logs
from utils.configuration import config


def insert_into_calendar(db: DAOAggregator,
                         test: models.Test,
                         run_at: float,
                         source: enums.EventSource,
                         recovery_attempt: int = 0,
                         transaction_finished: Optional[bool] = None
    ) -> None:
    if test.state != enums.TestState.enabled:
        logs.debug(f"(test {test.id_test}) new event not planned, because the state is {test.state}.")
        return
    logs.debug(f"(test {test.id_test}) new event planned at {logs.friendly_time(run_at)}.")
    data = schemas.EventCreate(run_at=run_at, source=source.value, recovery_attempt=recovery_attempt)
    db.events.create(
        id_test=test.id_test,
        data=data,
        transaction_finished=transaction_finished,
    )


class ProcessEvents:
    def __init__(self) -> None:
        self._now = 0
        self._db = None

    def _calculate_next_event_time(
        self, test: models.Test, previous_run: float
    ) -> Optional[float]:
        if test.scheduling_interval is None or test.scheduling_interval == 0:
            logs.debug(f"(test {test.id_test}) - scheduling interval is not set.")
            return None

        next_event_time = previous_run + test.scheduling_interval

        if next_event_time < self._now:
            logs.debug(f"(test {test.id_test}) - not possible to schedule event in the past.")
            next_event_time = self._now

        if test.scheduling_until is not None and next_event_time > test.scheduling_until:
            logs.debug(f"(test {test.id_test}) - scheduled time is after scheduling limit.")
            return None

        return next_event_time

    def _plan_next_event(self, test: models.Test, previous_run: float) -> None:
        """
        Warning, the function keeps uncommited SQL queries in the connection.
        """
        next_event_time = self._calculate_next_event_time(test, previous_run)
        if next_event_time is not None:
            logs.debug(f"(test {test.id_test}) - new event planned at {logs.friendly_time(next_event_time)}.")
            insert_into_calendar(self._db, test, next_event_time, enums.EventSource.calendar, transaction_finished=False)
        else:
            logs.debug(f"(test {test.id_test}) - new event is not planned.")


class RequestsForNewEvents(ProcessEvents):

    def __init__(self, db: DAOAggregator):
        super().__init__()
        self._db = db
        self._now = time.time()

    def process_all_requests(self) -> None:
        requests = self._db.requests.get_all()
        if len(requests):
            logs.debug(f"Found {len(requests)} new requests - tests: {','.join(str(r.id_test) for r in requests)}.")
        for request in self._db.requests.get_all():
            self._process_request(request)

    def _process_request(
        self,
        request: models.Request,
    ) -> None:
        logs.debug(f"(test {request.id_test}) - processing a new request.")
        test = self._db.tests.get_by_id(request.id_test)
        match request.reason:
            case enums.RequestReason.new:
                self._process_new_request(request, test)
            case enums.RequestReason.update:
                self._process_update_request(request, test)
            case enums.RequestReason.failed:
                self._process_recovery_request(request, test)
        self._db.requests.delete(request.id_request)

    def _process_new_request(
        self,
        request: models.Request,
        test: models.Test,
    ) -> None:
        if test.scheduling_from is not None and self._now < test.scheduling_from:
            logs.debug(f"(test {request.id_test}) - request for a new event in the future.")
            # Test should start in the future, so we are just inserting the event into the calendar at the scheduling_from time.
            insert_into_calendar(self._db, test, test.scheduling_from, enums.EventSource.request)
        else:
            logs.debug(f"(test {request.id_test}) - request for a new event now, also creating a run.")
            self._plan_next_event(test, self._now)

    def _process_update_request(
        self,
        request: models.Request,
        test: models.Test,
    ) -> None:
        if test.state in [enums.TestState.disabled, enums.TestState.deleted]:
            logs.debug(f"(test {request.id_test}) - new state {test.state}, removing all events from the calendar.")
            self._db.events.delete(request.id_test)
        elif test.state == enums.TestState.enabled:
            logs.debug(f"(test {request.id_test}) - re-enabling the test, creating a new event.")
            # re-enabling the test behaves the same as a new request
            self._process_new_request(request, test)

    def _process_recovery_request(
        self,
        request: models.Request,
        test: models.Test,
    ) -> None:
        # Note: Recovery requests have already the recovery_attempt incremented from the tests_manager.
        if test.recovery_attempt_limit is None:
            logs.debug(f"(test {request.id_test}) - recovery limit is not set.")
            return
        if request.recovery_attempt > test.recovery_attempt_limit:
            logs.debug(f"(test {request.id_test}) - reached the recovery limit.")
            return
        recovery_test_time = self._now + test.recovery_interval
        # Here we are not checking if the recovery time is before the scheduling_until. Technically, it is possible, but it's okay if that happens.
        if test.scheduling_until is not None and recovery_test_time > test.scheduling_until:
            logs.debug(f"(test {request.id_test}) - planned recovery time is after scheduling until.")
            return
        insert_into_calendar(self._db, test, recovery_test_time, enums.EventSource.recovery, request.recovery_attempt)


class PlannedEvents(ProcessEvents):
    def __init__(self, db: DAOAggregator):
        super().__init__()
        self._now = time.time()
        self._db = db

    def process_all_events(
        self,
    ) -> None:
        events = self._db.events.get_all_until_run_threshold(self._now)
        if len(events):
            logs.debug(f"Found {len(events)} events to be executed - tests: {','.join(str(e.id_test) for e in events)}.")

        for event in events:
            self._process_one_event(event)

    def _process_one_event(
        self,
        event: models.Event,
    ) -> None:
        logs.debug(f"(test {event.id_test}) - processing an event from the calendar.")
        test = self._db.tests.get_by_id(event.id_test)
        self._start_a_new_run(test, event, transaction_finished=False)

        if event.source != enums.EventSource.recovery:
            logs.debug(f"(test {event.id_test}) - planning a normal (repeating) event into the calendar.")
            self._plan_next_event(test, event.run_at)
        else:
            logs.debug(f"(test {event.id_test}) - new event is not planned as current processed event is a recovery event.")
        self._db.events.delete(event.id_event, transaction_finished=True)

    def _start_a_new_run(
            self,
            test: models.Test,
            event: models.Event,
            transaction_finished: Optional[bool] = None,
    ) -> None:
        already_planned_run = self._db.runs.get_all_by_test_id_and_state(test.id_test, enums.RunState.waiting)
        if len(already_planned_run) > 0:
            logs.warning(f"(test {test.id_test}) - new run not created because there is already waiting one.")
            return

        self._db.runs.create(
            test.id_test,
            test.version,
            enums.RunState.waiting,
            event.run_at,
            event.recovery_attempt,
            transaction_finished,
        )
        logs.debug(f"(test {test.id_test}) - created a run.")


def process_events():
    db = DAOAggregator()

    new_events = RequestsForNewEvents(db)
    new_events.process_all_requests()

    planned_events = PlannedEvents(db)
    planned_events.process_all_events()

    db.close()


def infinite_loop_for_processing_events():
    while True:
        process_events()
        time.sleep(0.1)


def main(persistent_folder: Path) -> None:
    config.load_config(persistent_folder / "config.ini")
    logs.setup_logging("calendar")
    initialization.pre_running_check()
    infinite_loop_for_processing_events()
