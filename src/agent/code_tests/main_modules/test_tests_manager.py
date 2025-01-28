from pathlib import Path
from unittest.mock import patch, MagicMock

from code_tests.timeout import function_timeout, TimeoutException
from main_modules import tests_manager


def test_check_tests():
    mock_queue = MagicMock()
    with patch.object(tests_manager.TestsManager, "process_tests", return_value=None) as mock_test_manager:
        tests_manager.check_tests(mock_queue)
    mock_test_manager.assert_called_once()


def test_infinite_loop_for_checking_tests():
    with patch("main_modules.tests_manager.check_tests", return_value="doesnt_matter") as mock_check_tests:
        func = function_timeout(timeout=1.0)(tests_manager.infinite_loop_for_checking_tests)
        try:
            func()
        except TimeoutException:
            pass
    call_count = mock_check_tests.call_count
    assert 5 < call_count < 12


def test_main():
    with patch("utils.configuration.config.load_config", return_value='doesnt_matter') as mock_load_config:
        with patch("utils.logs.setup_logging", return_value='doesnt_matter') as mock_setup_logging:
            with patch("main_modules.initialization.pre_running_check", return_value='doesnt_matter') as mock_pre_running_check:
                with patch("main_modules.tests_manager.infinite_loop_for_checking_tests", return_value='doesnt_matter') as mock_infinite_loop:
                    tests_manager.main(Path("."))
    mock_load_config.assert_called_once()
    mock_setup_logging.assert_called_once()
    mock_pre_running_check.assert_called_once()
    mock_infinite_loop.assert_called_once()
