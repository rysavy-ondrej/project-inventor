from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from fastapi import Request, HTTPException, status

import aaa.authorization


def test_authorization_headers():
    aaa.authorization.authorization_headers("", "", "")
    assert True


@pytest.mark.parametrize(
    "authorization_hmac, request_body, request_json, json_called, password, result",
    [
        ("009022fa9d508e4c0b7748c4f590b7a29c854a736afcd8c8c48465b0603bc66d", b'{"key": "value"}', {"key": "value"}, True, "my_secret_password", True),  # valid with body
        ("83f1c744f204e7eec81bb0861a2a94962f3404089fcf95bbfa05cecdd6be7a4c", b'', {}, False, "my_secret_password", True),  # valid with empty body
        ("wrong_hmac_value", b'{"key": "value"}', {"key": "value"}, True, "my_secret_password", False),  # wrong hmac value
        ("009022fa9d508e4c0b7748c4f590b7a29c854a736afcd8c8c48465b0603bc66d", b'{"key": "value"}', {"key": "value"}, True, "wrong_password", False),  # wrong password
    ]
)
@pytest.mark.asyncio(loop_scope="function")
async def test_verify_hmac_valid(authorization_hmac, request_body, request_json, json_called, password, result):
    mock_request = MagicMock()
    mock_request.headers = {
        "authorization-time": "1625190000",
        "authorization-hmac": authorization_hmac,
        "authorization-nonce": "random_nonce"
    }
    mock_request.scope = {
        "method": "GET",
        "path": "/api/data",
        "query_string": b"param1=value1&param2=value2"
    }

    mock_request.body = AsyncMock(return_value=request_body)
    mock_request.json = AsyncMock(return_value=request_json)

    expected_password = "my_secret_password"

    result = await aaa.authorization.verify_hmac(mock_request, expected_password)

    if json_called:
        mock_request.json.assert_called_once()
    else:
        mock_request.json.assert_not_called()

    assert result is result


@pytest.mark.parametrize(
    "time_from_header, current_time, validity_limit, exception_detail",
    [
        (1000, 1001, 100, None),  # valid scenario (int format)
        (1000.1, 1001, 100, None),  # valid scenario (float format)
        ("1000.1", 1001, 100, None),  # valid scenario (float in str format)
        (None, 1001, 100, "Missing request time for authorization."),  # no time in header
        ("wrong", 1001, 100, "Request time for authorization has wrong format."),  # wrong time format
        (100, 1001, 100, "Wrong request time (diff 901.0s)."),  # old time in header
        (2000, 1001, 100, "Wrong request time (diff -999.0s)."),  # future time in header
    ]
)
def test_verify_request_time(time_from_header, current_time, validity_limit, exception_detail):
    mock_request = MagicMock()
    mock_request.headers.get.return_value = time_from_header

    with patch("utils.configuration.config.get", return_value=validity_limit):
        with patch("time.time", return_value=current_time):
            if exception_detail:
                with pytest.raises(HTTPException) as exception_info:
                    aaa.authorization.verify_request_time(mock_request)
                assert exception_info.value.status_code == status.HTTP_403_FORBIDDEN
                assert exception_info.value.detail == exception_detail
            else:
                aaa.authorization.verify_request_time(mock_request)


@pytest.mark.parametrize(
    "request_nonce, return_nonce, return_time, db_create_called",
    [
        ("test_nonce", [], 123456789, ("test_nonce", 123456789)),  # unused nonce
        ("test_nonce", ["test_nonce"], 123456789, None),  # already used nonce
        ("", [], 123456789, ("", 123456789)),  # no nonce in header, not used yet
    ]
)
def test_verify_request_nonce(request_nonce, return_nonce, return_time, db_create_called):
    mock_request = MagicMock(spec=Request)
    mock_request.headers.get.return_value = request_nonce

    mock_dao_aggregator = MagicMock()
    mock_dao_aggregator.nonces.get_by_nonce.return_value = return_nonce

    with patch("database.daoaggregator.get_dao_aggregator", return_value=mock_dao_aggregator):
        with patch("time.time", return_value=return_time):
            if len(return_nonce):
                with pytest.raises(HTTPException) as exception_info:
                    aaa.authorization.verify_request_nonce(mock_request)
                assert exception_info.value.status_code == status.HTTP_403_FORBIDDEN
            else:
                aaa.authorization.verify_request_nonce(mock_request)

    if db_create_called is None:
        mock_dao_aggregator.nonces.create.assert_not_called()
    else:
        mock_dao_aggregator.nonces.create.assert_called_once_with(*db_create_called)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "hmac_header, test_key, root_key, hmac_test_key_result, hmac_root_key_result, expected_warning, should_raise_exception",
    [
        # Case 1: Development mode (hmac_header is "xdev")
        ("xdev", None, "root_key", None, None, None, False),

        # Case 2: Test key matches
        ("test_hmac", "test_key", "root_key", True, False, None, False),

        # Case 3: Test key does not match, root key matches
        ("test_hmac", "test_key", "root_key", False, True, "The authorization token doesn't match the value expected by the test.", False),

        # Case 4: Test key does not match, root key does not match
        ("test_hmac", "test_key", "root_key", False, False, "The authorization token doesn't match the value expected by the test.", True),

        # Case 5: No test key, root key matches
        ("test_hmac", None, "root_key", False, True, None, False),

        # Case 6: No test key, root key does not match
        ("test_hmac", None, "root_key", False, False, None, True),
    ],
)
async def test_authorize_request(
    hmac_header,
    test_key,
    root_key,
    hmac_test_key_result,
    hmac_root_key_result,
    expected_warning,
    should_raise_exception,
):
    # Mock the dependencies
    with patch("aaa.authorization.verify_request_time") as mock_verify_request_time, \
         patch("aaa.authorization.verify_request_nonce") as mock_verify_request_nonce, \
         patch("aaa.authorization.verify_hmac", new_callable=AsyncMock) as mock_verify_hmac, \
         patch("utils.logs.warning") as mock_logs_warning:

        # Set up the mock request
        mock_request = MagicMock()
        mock_request.headers.get.return_value = hmac_header

        # Setup verify_hmac mock responses
        mock_verify_hmac.side_effect = lambda req, key: (
            hmac_test_key_result if key == test_key else hmac_root_key_result
        )

        if should_raise_exception:
            with pytest.raises(HTTPException) as exc_info:
                await aaa.authorization.authorize_request(mock_request, root_key=root_key, test_key=test_key)
            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert exc_info.value.detail == "Wrong authorization token."
        else:
            await aaa.authorization.authorize_request(mock_request, root_key=root_key, test_key=test_key)

        # Verify no exception is raised and the correct warnings are logged
        if expected_warning:
            mock_logs_warning.assert_called_with(expected_warning)
        else:
            mock_logs_warning.assert_not_called()

        if hmac_header != "xdev":
            mock_verify_request_time.assert_called_once()
            mock_verify_request_nonce.assert_called_once()

            # Ensure verify_hmac was called with the correct keys
            if test_key:
                mock_verify_hmac.assert_any_call(mock_request, test_key)
                if expected_warning:
                    mock_verify_hmac.assert_any_call(mock_request, root_key)
