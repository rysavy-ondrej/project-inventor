import pytest
from unittest.mock import patch
import api.logs_processing
from datetime import datetime
from pathlib import Path
from mock_open import MockOpen

from utils import enums
from utils.exceptions import TransactionError


@pytest.mark.parametrize(
    "file_content, expected_lines",
    [
        ("", []),  # empty file
        ("line1", ["line1"]),  # one line one chunk
        ("line1line1", ["line1line1"]),  # one line multiple chunks
        ("line1\nline2line2\nline3line3line3", ["line3line3line3", "line2line2", "line1"]),  # multiple lines, multiple chunks
        ("line1\n", ["line1"]),  # one line, \n at the end
    ]
)
def test_reverse_readline(file_content, expected_lines):
    mock_open = MockOpen()
    mock_open[Path("file")].read_data = file_content
    mock_open[Path("bad_file")].side_effect = IOError()

    result = []
    with patch("api.logs_processing.open", mock_open):
        for line in api.logs_processing.reverse_readline(Path("file"), buf_size=6):  # very low buf_size to test merging chunks into messages
            result.append(line)
    assert result == expected_lines


def test_reverse_readline_wrong_file():
    mock_open = MockOpen()
    mock_open[Path("bad_file")].side_effect = IOError()

    exception = False
    result = []
    try:
        with patch("api.logs_processing.open", mock_open):
            for line in api.logs_processing.reverse_readline(Path("bad_file")):  # very low buf_size to test merging chunks into messages
                result.append(line)
    except OSError:
        exception = True
    assert result == []
    assert exception is True


@pytest.mark.parametrize(
    "log_line, expected_severity",
    [
        ("2024-02-28 21:54:56,003 | manager  |    DEBUG | main_tests_manager.py            | start_new_tests                                                  |  91 | Starting new test based on the run - 1", "debug"),  # Debug log
        ("2024-03-01 17:38:51,496 | api      |     INFO | aaa\\accounting.py                | record                                           |  28 | GET /system/config, params:, body:, status_code=200", "info"),  # Info log
        ("2024-03-04 17:21:09,102 | api      |  WARNING | configuration.py                 | _exception_handler                               |  43 | Unable to find option 'authorization_new_tests' in the 'system' section of the configuration file.", "warning"),  # Warning log
        ("2024-02-29 21:35:59,734 | manager  |    ERROR | configuration.py                 | __getattr__                                      | 111 | The configuration contains invalid value for the option api/syslog. Expected type port.", "error"),  # Error log
        ("2024-02-29 21:25:51,134 | manager  | CRITICAL | database\\models.py               | verify_models_with_database                      | 186 | Database doesn't contain all the required table columns (old_params/blabla).", "critical"),  # Critical log
        ("This is a weird log line", "unknown"),
        ("", "unknown"),
    ]
)
@patch('utils.logs.error')
def test_detect_log_severity(mock_logs_error, log_line, expected_severity):
    result = api.logs_processing.detect_log_severity(log_line)
    assert result == expected_severity

    # If severity is unknown, check that logs.error was called
    if expected_severity == "unknown":
        mock_logs_error.assert_called_once()
    else:
        mock_logs_error.assert_not_called()


@pytest.mark.parametrize(
    "delta_minutes, expected_time_str",
    [
        (0, "2024-09-05 12:00:00"),  # No time delta (current time)
        (10, "2024-09-05 11:50:00"),  # 10 minutes ago
        (60, "2024-09-05 11:00:00"),  # 1 hour ago
        (1440, "2024-09-04 12:00:00"),  # 1 day ago
        (-30, "2024-09-05 12:30:00"),  # Future time (negative delta)
    ]
)
def test_get_threshold_time(delta_minutes, expected_time_str):
    with patch('api.logs_processing.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2024, 9, 5, 12, 0, 0)
        result = api.logs_processing.get_threshold_time(delta_minutes)
    assert result == expected_time_str


@pytest.mark.parametrize(
    "read_lines, threshold_time, expected_result",
    [
        (
                ["2024-02-28 10:54:56,001 | DEBUG | data", "2024-02-28 10:54:56,001 | data"],
                "2024-02-28 00:00:58,002",
                None
        ),
        (
                [],
                "2024-02-28 11:55:58,002",
                {'critical': 0, 'debug': 0, 'error': 0, 'info': 0, 'unknown': 0, 'warning': 0}
        ),
        (
                ["2024-02-28 14:58:59,005 | INFO | data", "2024-02-28 13:57:58,004 | DEBUG | data", "2024-02-28 12:56:59,003 | ERROR | data", "2024-02-28 11:55:58,002 | ERROR | data", "2024-02-28 10:54:56,001 | DEBUG | data"],
                "2024-02-28 14:59:00",
                {'critical': 0, 'debug': 0, 'error': 0, 'info': 0, 'unknown': 0, 'warning': 0}
        ),
        (
                ["2024-02-28 14:58:59,005 | INFO | data", "2024-02-28 13:57:58,004 | DEBUG | data", "2024-02-28 12:56:59,003 | ERROR | data", "2024-02-28 11:55:58,002 | ERROR | data", "2024-02-28 10:54:56,001 | DEBUG | data"],
                "2024-02-28 14:58:58",
                {'critical': 0, 'debug': 0, 'error': 0, 'info': 1, 'unknown': 0, 'warning': 0}
        ),
        (
                ["2024-02-28 14:58:59,005 | INFO | data", "2024-02-28 13:57:58,004 | DEBUG | data", "2024-02-28 12:56:59,003 | ERROR | data", "2024-02-28 11:55:58,002 | ERROR | data", "2024-02-28 10:54:56,001 | DEBUG | data"],
                "2024-02-28 13:57:00",
                {'critical': 0, 'debug': 1, 'error': 0, 'info': 1, 'unknown': 0, 'warning': 0}
        ),
        (
                ["2024-02-28 14:58:59,005 | INFO | data", "2024-02-28 13:57:58,004 | DEBUG | data", "2024-02-28 12:56:59,003 | ERROR | data", "2024-02-28 11:55:58,002 | ERROR | data", "2024-02-28 10:54:56,001 | DEBUG | data"],
                "2024-02-28 12:56:00",
                {'critical': 0, 'debug': 1, 'error': 1, 'info': 1, 'unknown': 0, 'warning': 0}
        ),
        (
                ["2024-02-28 14:58:59,005 | INFO | data", "2024-02-28 13:57:58,004 | DEBUG | data", "2024-02-28 12:56:59,003 | ERROR | data", "2024-02-28 11:55:58,002 | ERROR | data", "2024-02-28 10:54:56,001 | DEBUG | data"],
                "2024-02-28 11:55:00",
                {'critical': 0, 'debug': 1, 'error': 2, 'info': 1, 'unknown': 0, 'warning': 0}
        ),
        (
                ["2024-02-28 14:58:59,005 | INFO | data", "2024-02-28 13:57:58,004 | DEBUG | data", "2024-02-28 12:56:59,003 | ERROR | data", "2024-02-28 11:55:58,002 | ERROR | data", "2024-02-28 10:54:56,001 | DEBUG | data"],
                "2024-02-28 10:54:00",
                {'critical': 0, 'debug': 2, 'error': 2, 'info': 1, 'unknown': 0, 'warning': 0}
        ),
    ]
)
@patch('utils.logs.error')
def test_statistics(mock_error, read_lines, threshold_time, expected_result):
    with patch('api.logs_processing.reverse_readline') as mock_reverse_readline:
        mock_reverse_readline.return_value = iter(read_lines)
        with patch("api.logs_processing.get_threshold_time", return_value=threshold_time):
            result = api.logs_processing.statistics(Path("."), 0)  # parameters are not used

    if expected_result is None:
        mock_error.assert_called()
    else:
        assert result == expected_result


@pytest.mark.parametrize(
    "read_lines, since, include_since, expected_result",
    [
        ([], "2024-02-28 11:55:58", False, []),
        (["2024-02-16 data", "2024-02-14 data", "2024-02-12 data", "2024-02-10 data"], "2024-02-09", True, ["2024-02-16 data", "2024-02-14 data", "2024-02-12 data", "2024-02-10 data"]),
        (["2024-02-16 data", "2024-02-14 data", "2024-02-12 data", "2024-02-10 data"], "2024-02-10", True, ["2024-02-16 data", "2024-02-14 data", "2024-02-12 data", "2024-02-10 data"]),
        (["2024-02-16 data", "2024-02-14 data", "2024-02-12 data", "2024-02-10 data"], "2024-02-13", True, ["2024-02-16 data", "2024-02-14 data"]),
        (["2024-02-16 data", "2024-02-14 data", "2024-02-12 data", "2024-02-10 data"], "2024-02-16", True, ["2024-02-16 data"]),
        (["2024-02-16 data", "2024-02-14 data", "2024-02-12 data", "2024-02-10 data"], "2024-02-17", True, []),
        (["2024-02-16 data", "2024-02-14 data", "2024-02-12 data", "2024-02-10 data"], "2024-02-09", False, ["2024-02-16 data", "2024-02-14 data", "2024-02-12 data", "2024-02-10 data"]),
        (["2024-02-16 data", "2024-02-14 data", "2024-02-12 data", "2024-02-10 data"], "2024-02-10", False, ["2024-02-16 data", "2024-02-14 data", "2024-02-12 data"]),
        (["2024-02-16 data", "2024-02-14 data", "2024-02-12 data", "2024-02-10 data"], "2024-02-13", False, ["2024-02-16 data", "2024-02-14 data"]),
        (["2024-02-16 data", "2024-02-14 data", "2024-02-12 data", "2024-02-10 data"], "2024-02-17", False, []),
    ]
)
def test_find_lines_from_datetime(read_lines, since, include_since, expected_result):
    with patch('api.logs_processing.reverse_readline') as mock_reverse_readline:
        mock_reverse_readline.return_value = iter(read_lines)
        result = api.logs_processing.find_lines_from_datetime(Path("."), since, include_since)

    assert result == expected_result


@pytest.mark.parametrize(
    "data, algorithm, expected_result",
    [
        ("", enums.CompressionAlg.zlib_base85, "c$@<O00001"),
        ("data", enums.CompressionAlg.zlib_base85, "c$`Z~EJ*|a1ONe>"),
        ("`~!@#$%^&*()_+{}|:\"<>?-=[]\;',./'`", enums.CompressionAlg.zlib_base85, "c$`b9Q*=;PQH@j6($I|8uCA@IQnInL*R_p~jj>kO(bHE?005b;2(A"),
        ("data", "unsupported", None),
    ]
)
def test_compress_data(data, algorithm, expected_result):
    exception_raised = False
    result = None
    try:
        result = api.logs_processing.compress_data(data, algorithm)
    except TransactionError:
        exception_raised = True
    if expected_result:
        assert result == expected_result
        assert exception_raised is False
    else:
        assert exception_raised is True


@pytest.mark.parametrize(
    "data, line, max_size, expected",
    [
        ("Hello", " World", 12, True),  # len("Hello World") == 11, less than max_size
        ("Hello", " World", 11, True),  # len("Hello World") == 11, equal to max_size
        ("Hello", " World", 10, False),  # len("Hello World") == 11, exceeds max_size
        ("Hello", "", 6, True),  # No line to add, less than max_size
        ("Hello", "", 5, True),  # No line to add, equal to max_size
        ("Hello", "", 4, False),  # No line to add, exceeds max_size
        ("", "World", 6, True),  # empty data, line less than max_size
        ("", "World", 5, True),  # empty data, line equal to max_size
        ("", "World", 4, False),  # empty data, line exceeds max_size
    ]
)
def test_adding_line_doesnt_reach_limit(data, line, max_size, expected):
    result = api.logs_processing.adding_line_doesnt_reach_limit(data, line, max_size)
    assert result == expected


@pytest.mark.parametrize(
    "lines, max_size, expected_lines, expected_last_datetime, expected_more_data",
    [
        # Test 1: Empty input
        ([], 1_000_000, "", None, False),

        # Test 2: One line within limit
        ([
             "2001-01-01 00:00:00,000 INFO First line"
         ],
         1_000_000,
         "2001-01-01 00:00:00,000 INFO First line\n",
         "2001-01-01 00:00:00,000",
         False),

        # Test 3: Multiple lines, all within limit
        ([
             "2002-01-01 00:00:00,000 INFO Second line",
             "2001-01-01 00:00:00,000 INFO First line",
         ],
         1_000_000,
         "2001-01-01 00:00:00,000 INFO First line\n2002-01-01 00:00:00,000 INFO Second line\n",
         "2002-01-01 00:00:00,000",
         False),

        # Test 4: Multiple lines, exceeding limit
        ([
             "2003-01-01 00:00:00,000 INFO Third line",
             "2002-01-01 00:00:00,000 INFO Second line",
             "2001-01-01 00:00:00,000 INFO First line",
         ],
         100,  # Set max_size small so not all lines fit
         "2001-01-01 00:00:00,000 INFO First line\n2002-01-01 00:00:00,000 INFO Second line\n",
         "2002-01-01 00:00:00,000",
         True),

        # Test 5: One line over the limit
        (["2001-01-01 00:00:00,000 INFO First line"],
         36,  # Line length exceeds the limit
         "",
         None,
         True),
    ]
)
def test_select_lines_until_limit_is_reached(lines, max_size, expected_lines, expected_last_datetime, expected_more_data):
    result = api.logs_processing.select_lines_until_limit_is_reached(lines, max_size)

    assert result.lines == expected_lines
    assert result.last_datetime == expected_last_datetime
    assert result.more_data == expected_more_data


@pytest.mark.parametrize(
    "read_lines, since, max_size, compression_alg, expected_result",
    [
        (
                [
                    "2024-02-16 00:00:00,000 data",
                    "2024-02-14 00:00:00,000 data",
                    "2024-02-12 00:00:00,000 data",
                    "2024-02-10 00:00:00,000 data"
                ],
                "2024-02-12 00:00:00,000",
                1000,
                None,
                api.logs_processing.ExtractedLines("2024-02-14 00:00:00,000 data\n2024-02-16 00:00:00,000 data\n", "2024-02-16 00:00:00,000", False)
        ),
        (
                [
                    "2024-02-16 00:00:00,000 data",
                    "2024-02-14 00:00:00,000 data",
                    "2024-02-12 00:00:00,000 data",
                    "2024-02-10 00:00:00,000 data"
                ],
                "2024-02-11 00:00:00,000",
                60,
                enums.CompressionAlg.zlib_base85,
                api.logs_processing.ExtractedLines("c$_mbFf!3KFw!+NQZO*E0wWy*0|SMW#F9iVBbcNK7D)hFfDAb", "2024-02-14 00:00:00,000", True)
        ),
        (
                [
                    "2024-02-16 00:00:00,000 data",
                    "2024-02-14 00:00:00,000 data",
                    "2024-02-12 00:00:00,000 data",
                    "2024-02-10 00:00:00,000 data"
                ],
                "2024-02-12 00:00:00,000",
                56,
                None,
                api.logs_processing.ExtractedLines("2024-02-14 00:00:00,000 data\n", "2024-02-14 00:00:00,000", True)
        ),
    ]
)
def test_get_lines_from_file(read_lines, since, max_size, compression_alg, expected_result):
    with patch('api.logs_processing.reverse_readline') as mock_reverse_readline:
        mock_reverse_readline.return_value = iter(read_lines)
        result = api.logs_processing.get_lines_from_file(Path("."), since, max_size, compression_alg)

    assert result == expected_result
