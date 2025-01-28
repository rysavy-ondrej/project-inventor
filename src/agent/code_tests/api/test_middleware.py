from unittest.mock import patch, AsyncMock, MagicMock

import pytest
from fastapi import Request, status, HTTPException

import api.middleware
from utils.exceptions import TransactionError


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "body_data, call_result_code, expected_log_body, exception_code",
    [
        ("data", status.HTTP_200_OK, "data", None),
        ("data\ndata", status.HTTP_200_OK, "data\\ndata", None),
        ("", status.HTTP_400_BAD_REQUEST, "", None),
        ("data", None, "data", status.HTTP_400_BAD_REQUEST),
        ("data\ndata", None, "data\\ndata", status.HTTP_400_BAD_REQUEST),
    ]
)
async def test_middleware_accounting(body_data, call_result_code, expected_log_body, exception_code):
    orchestrator_name = "orchestrator_name"
    request = MagicMock()
    request.body = AsyncMock(return_value=body_data.encode("utf-8"))
    call_result = MagicMock()
    call_result.status_code = call_result_code
    call_next = AsyncMock(return_value=call_result)

    with patch("aaa.accounting.record") as mock_accounting:
        if exception_code is not None:
            call_next.side_effect = HTTPException(exception_code)
            with pytest.raises(HTTPException) as exception_info:
                await api.middleware.middleware_accounting(request, call_next, orchestrator_name)
            assert exception_info.value.status_code == exception_code
        else:
            result = await api.middleware.middleware_accounting(request, call_next, orchestrator_name)
            assert result.status_code == call_result.status_code
            mock_accounting.assert_called_once_with(orchestrator_name, request, expected_log_body, call_result_code)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "auth_header, orchestrator_name",
    [
        ("Bearer some_token", "orchestrator_name"),
        ("Bearer some_token", None),
    ]
)
async def test_get_orchestrator_name_from_token(auth_header, orchestrator_name):
    request = MagicMock(spec=Request)
    request.headers.get.return_value = auth_header

    token_data = MagicMock()
    token_data.orchestrator_name = orchestrator_name

    if orchestrator_name:
        with patch("aaa.authentication.get_data_from_auth_token", return_value=token_data):
            result = await api.middleware.get_orchestrator_name_from_token(request)
            assert str(result) == orchestrator_name
    else:
        with pytest.raises(HTTPException):
            with patch("aaa.authentication.get_data_from_auth_token", side_effect=HTTPException(status.HTTP_401_UNAUTHORIZED)):
                await api.middleware.get_orchestrator_name_from_token(request)


@pytest.mark.parametrize(
    "auth_header, expected_result",
    [
        # Test 1: Authorization header with Bearer token
        ("Bearer some_token", True),

        # Test 2: Authorization header with some other token type
        ("Basic some_token", False),

        # Test 3: Authorization header is an empty string
        ("", False),

        # Test 4: Authorization header with only Bearer
        ("Bearer", True),

        # Test 5: Authorization header with Bearer in the middle of the string
        ("Token Bearer other_data", True),
    ]
)
def test_user_is_authenticated(auth_header, expected_result):
    request = MagicMock(spec=Request)
    request.headers.get.return_value = auth_header

    result = api.middleware.user_is_authenticated(request)
    assert result == expected_result


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user_is_authenticated, orchestrator_name, accounting_result, call_next_result, expected_result",
    [
        (True, "orchestrator", "result1", "result2", "result1"),
        (False, "orchestrator", "result1", "result2", "result2"),
    ]
)
async def test_process_request(user_is_authenticated, orchestrator_name, accounting_result, call_next_result, expected_result):
    mock_request = MagicMock(spec=Request)
    call_next = AsyncMock(return_value=call_next_result)
    mock_dao_aggregator = MagicMock()
    mock_dao_aggregator.orchestrators.update.return_value = None
    current_time = 123456.7
    with patch("api.middleware.user_is_authenticated", return_value=user_is_authenticated):
        with patch("api.middleware.get_orchestrator_name_from_token", return_value=orchestrator_name):
            with patch("api.middleware.middleware_accounting", return_value=accounting_result):
                with patch("database.daoaggregator.get_dao_aggregator", return_value=mock_dao_aggregator):
                    with patch("time.time", return_value=current_time):
                        result = await api.middleware.process_request(mock_request, call_next)
                        assert result == expected_result


@pytest.mark.asyncio
async def test_dispatch_valid():
    expected_response = "successful_response"
    with patch("api.middleware.process_request", return_value=expected_response):
        request = AsyncMock(spec=Request)
        call_next = AsyncMock()

        middleware = api.middleware.Accounting(app=None)
        response = await middleware.dispatch(request, call_next)

        assert response == expected_response


@pytest.mark.asyncio(loop_scope="function")
async def test_dispatch_error():
    with patch("api.middleware.process_request") as mock_process_request:
        mock_process_request.side_effect = TransactionError()

        # Mock objects
        request = AsyncMock(spec=Request)  # Mock the Request object
        call_next = AsyncMock()  # Mock the call_next function

        # Instantiate the middleware and call dispatch
        middleware = api.middleware.Accounting(app=None)
        response = await middleware.dispatch(request, call_next)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
