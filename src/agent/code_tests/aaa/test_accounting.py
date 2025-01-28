from pathlib import Path
import aaa.accounting
from utils import enums
from unittest.mock import patch, MagicMock
from fastapi import Request


def test_setup():
    logfile = '/path/to/logfile.log'
    with patch("builtins.open", return_value='doesnt_matter') as mock_open:
        with patch("utils.configuration.config.get", return_value=logfile):
            aaa.accounting.setup()

        mock_open.assert_called_once()


@patch('logging.getLogger')
def test_setup_no_logs_file(mock_get_logger):
    with patch("utils.configuration.config.get", return_value=None):
        aaa.accounting.setup()

    mock_get_logger.assert_not_called()


def test_record():
    mock_request = MagicMock(spec=Request)
    mock_request.method = "POST"
    mock_request.url.path = "/example/path"
    mock_request.query_params = {"param1": "value1"}

    orchestrator_name = "Orchestrator"
    body = "test body"
    status_code = 200

    with patch("utils.logs.info") as mock_logs, \
         patch("aaa.accounting.logger_accounting.info") as mock_logger:
        aaa.accounting.record(orchestrator_name, mock_request, body, status_code)

    # Check if logs.info was called with the correct message
    mock_logs.assert_called_once_with(
        "POST /example/path, params:{'param1': 'value1'}, body:test body, status_code=200"
    )

    # Check if logger_accounting.info was called with the correct message
    mock_logger.assert_called_once_with(
        "Orchestrator     | POST   | /example/path        |  200 | {'param1': 'value1'} | test body"
    )


def test_get_lines_from_file_default_max_size():
    file = Path("/path/to/file.log")
    since = "2024-01-01T00:00:00Z"
    max_size = 1000
    compression_alg = enums.CompressionAlg.zlib_base85

    with patch("api.logs_processing.get_lines_from_file") as mock_logs_processing:
        aaa.accounting.get_lines_from_file(file, since, max_size, compression_alg)

    mock_logs_processing.assert_called_once_with(file, since, max_size, compression_alg)
