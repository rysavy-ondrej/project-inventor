from datetime import datetime
from pathlib import Path
from unittest.mock import patch, ANY, MagicMock, call

import pytest

from code_tests.timeout import function_timeout, TimeoutException
from database.dao.generic import RecordsCounter
from database.daoaggregator import DAOAggregator
from main_modules import stats

@pytest.mark.parametrize(
    "records_values, call_count",
    [
        ([], 1),
        ([("cat1", 1)], 2),
        ([("cat1", 1), ("cat2", 2), ("cat3", 3)], 4),
    ]
)
def test_calculate_statistics_for_table(records_values, call_count):
    mock_db = MagicMock()
    mock_db.stats.create = MagicMock()

    records = RecordsCounter()
    expected_calls = []
    records_summary = 0
    for records_value in records_values:
        records.add(records_value[0], records_value[1])
        expected_calls.append(call(123, "name", records_value[0], records_value[1]))
        records_summary += records_value[1]

    mock_sub_db = MagicMock()
    mock_sub_db.table.__tablename__ = "name"
    mock_sub_db.count_records_in_table.return_value = records

    stats.calculate_statistics_for_table(mock_db, mock_sub_db, 123)

    mock_db.stats.create.assert_has_calls(expected_calls, any_order=True)
    assert mock_db.stats.create.call_count == call_count


def test_calculate_statistics_for_tables():
    with patch("main_modules.stats.calculate_statistics_for_table", return_value="doesnt_matter") as mock_calculate:
        with patch("time.time", return_value=123) as mock_time:
            db = DAOAggregator()
            stats.calculate_statistics_for_tables(db)
    mock_time.assert_called_once()
    mock_calculate.assert_called_with(db, ANY, 123)
    assert mock_calculate.call_count == 9


@pytest.mark.parametrize(
    "minute, second, expected_sleep",
    [
        (30, 45, 1755),
        (59, 59, 1),
        (58, 30, 90),
        (0, 0, 3600)
    ]
)
def test_wait_until_next_hour(minute, second, expected_sleep):
    custom_datetime = datetime(2024, 11, 22, 15, minute, second, 0)
    with patch('main_modules.stats.datetime', wraps=datetime) as mock_datetime:
        mock_datetime.now.return_value = custom_datetime
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        with patch("time.sleep", return_value="doesnt_matter") as mock_sleep:
            stats.wait_until_next_hour()
    mock_sleep.assert_called_once_with(expected_sleep)


def test_calculate_statistics_for_database():
    with patch("main_modules.stats.calculate_statistics_for_tables", return_value="doesnt_matter") as mock_stats:
        with patch("utils.logs.debug", return_value="doesnt_matter") as mock_log:
            stats.calculate_statistics_for_database()
    mock_stats.assert_called_once()
    mock_log.assert_called_once()


def test_infinite_loop_for_calculating_database_statistics():
    with patch("main_modules.stats.wait_until_next_hour", return_value="doesnt_matter"):
        with patch("main_modules.stats.calculate_statistics_for_database", return_value="doesnt_matter") as mock_stats:
            with patch("utils.configuration.config.get", return_value=0.1):
                func = function_timeout(timeout=2.0)(stats.infinite_loop_for_calculating_database_statistics)
                try:
                    func()
                except TimeoutException:
                    pass
    call_count = mock_stats.call_count
    assert 10 < call_count < 22


def test_main():
    with patch("utils.configuration.config.load_config", return_value='doesnt_matter') as mock_load_config:
        with patch("utils.logs.setup_logging", return_value='doesnt_matter') as mock_setup_logging:
            with patch("main_modules.initialization.pre_running_check", return_value='doesnt_matter') as mock_pre_running_check:
                with patch("main_modules.stats.infinite_loop_for_calculating_database_statistics", return_value='doesnt_matter') as mock_infinite_loop:
                    stats.main(Path("."))
    mock_load_config.assert_called_once()
    mock_setup_logging.assert_called_once()
    mock_pre_running_check.assert_called_once()
    mock_infinite_loop.assert_called_once()
