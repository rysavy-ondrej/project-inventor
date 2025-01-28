from pathlib import Path
from code_tests.timeout import function_timeout, TimeoutException
from main_modules import cleaner
import pytest
from unittest.mock import patch, MagicMock, ANY
from database.daoaggregator import DAOAggregator


@pytest.fixture
def mock_sub_db():
    mock_db = MagicMock()
    mock_db.table = MagicMock(__tablename__="table")
    mock_db.delete_old_records.return_value = 0
    return mock_db


@pytest.mark.parametrize(
    "rows_deleted",
    [
        0,
        1,
        10,
    ]
)
def test_delete_old_records_for_table(mock_sub_db, rows_deleted):
    with patch("utils.configuration.config.get", return_value=10):
        with patch("utils.logs.info", return_value="doesnt_matter") as mock_log:
            mock_sub_db.delete_old_records.return_value = rows_deleted
            cleaner.delete_old_records_for_table(mock_sub_db, 1000)
    mock_sub_db.delete_old_records.assert_called_with(990)
    if rows_deleted > 0:
        mock_log.assert_called_once()
    else:
        mock_log.assert_not_called()


def test_delete_old_records():
    with patch("main_modules.cleaner.delete_old_records_for_table", return_value="doesnt_matter") as mock_delete:
        with patch("time.time", return_value=123) as mock_time:
            db = DAOAggregator()
            cleaner.delete_old_records(db)
    mock_time.assert_called_once()
    mock_delete.assert_called_with(ANY, 123)
    assert mock_delete.call_count == 10


def test_clean_database():
    with patch("main_modules.cleaner.delete_old_records", return_value="doesnt_matter") as mock_delete:
        with patch("utils.logs.debug", return_value="doesnt_matter") as mock_log:
            cleaner.clean_database()
    mock_delete.assert_called_once()
    mock_log.assert_called_once()


def test_infinite_loop_for_cleaning_database():
    with patch("main_modules.cleaner.clean_database", return_value="doesnt_matter") as mock_clean_database:
        with patch("utils.configuration.config.get", return_value=0.1):
            func = function_timeout(timeout=2.0)(cleaner.infinite_loop_for_cleaning_database)
            try:
                func()
            except TimeoutException:
                pass
    call_count = mock_clean_database.call_count
    assert 10 < call_count < 22


def test_main():
    with patch("utils.configuration.config.load_config", return_value='doesnt_matter') as mock_load_config:
        with patch("utils.logs.setup_logging", return_value='doesnt_matter') as mock_setup_logging:
            with patch("main_modules.initialization.pre_running_check", return_value='doesnt_matter') as mock_pre_running_check:
                with patch("main_modules.cleaner.infinite_loop_for_cleaning_database", return_value='doesnt_matter') as mock_infinite_loop:
                    cleaner.main(Path("."))
    mock_load_config.assert_called_once()
    mock_setup_logging.assert_called_once()
    mock_pre_running_check.assert_called_once()
    mock_infinite_loop.assert_called_once()
