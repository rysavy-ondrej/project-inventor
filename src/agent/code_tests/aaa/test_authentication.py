from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from fastapi import HTTPException

import aaa.authentication


@pytest.mark.parametrize(
    "orchestrator_name, orchestrator_ip, token_validity, current_time, token_key, expected",
    [
        ("Orchestrator", "192.168.1.1", 3600, 1000, "token", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJvcmNoZXN0cmF0b3JfbmFtZSI6Ik9yY2hlc3RyYXRvciIsIm9yY2hlc3RyYXRvcl9pcCI6IjE5Mi4xNjguMS4xIiwiZXhwaXJhdGlvbiI6NDYwMH0.T21I4Bx3qs-TzZ51Se5OGYl8Dhr8uewjZsvApMYVYtM"),  # valid case
        ("Orchestrator", "192.168.1.1", 3600, 1000, "", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJvcmNoZXN0cmF0b3JfbmFtZSI6Ik9yY2hlc3RyYXRvciIsIm9yY2hlc3RyYXRvcl9pcCI6IjE5Mi4xNjguMS4xIiwiZXhwaXJhdGlvbiI6NDYwMH0.IsJUCDn1ufjoi9fCENcyUy2u8UVGGL_rPKL0ZUwAa98"),  # empty token key
    ]
)
def test_create_auth_token(orchestrator_name, orchestrator_ip, token_validity, current_time, token_key, expected):
    with patch("time.time", return_value=current_time):
        with patch("aaa.authentication.token_key", token_key):
            result = aaa.authentication.create_auth_token(orchestrator_name, orchestrator_ip, token_validity)
    assert result == expected


@pytest.mark.asyncio
@patch('aaa.encryption.decrypt')
@patch('api.schemas.token.TokenData')
@pytest.mark.parametrize(
    "decrypted_data, client_ip, expected_exception",
    [
        ({"orchestrator_ip": "127.0.0.1", "orchestrator_name": "orchestrator", "expiration": 123456}, "127.0.0.1", None),  # valid case
        (None, "127.0.0.1", HTTPException),  # invalid token data
        ({"orchestrator_ip": "127.0.0.1", "orchestrator_name": "orchestrator", "expiration": 123456}, "192.168.1.1", HTTPException),  # IP mismatch
    ]
)
async def test_get_data_from_auth_token(mock_token_data, mock_decrypt, decrypted_data, client_ip, expected_exception):
    # Mock the request object
    mock_request = MagicMock()
    mock_request.client.host = client_ip

    # Set the side effect of the mock_decrypt function
    mock_decrypt.return_value = decrypted_data

    # Set the side effect for the TokenData constructor
    if decrypted_data:
        mock_token_data.return_value = mock_token_data(**decrypted_data)

    if expected_exception:
        with pytest.raises(expected_exception):
            await aaa.authentication.get_data_from_auth_token(mock_request)
    else:
        result = await aaa.authentication.get_data_from_auth_token(mock_request)
        assert result.model_dump() == decrypted_data


@patch('aaa.encryption.calculate_hash')
@pytest.mark.parametrize(
    "username, hashed_password, expected_password, expected_exception",
    [
        ("user1", "hashed_user1password", "password", None),  # valid credentials
        ("user3", "wrong_hash", "password", HTTPException),  # invalid password hash
        ("user4", "hashed_user4password", "wrongpass", HTTPException),  # wrong expected password
    ]
)
def test_verify_login(mock_calculate_hash, username, hashed_password, expected_password, expected_exception):
    mock_calculate_hash.side_effect = lambda value: "hashed_" + value

    if expected_exception:
        with pytest.raises(expected_exception):
            aaa.authentication.verify_login(username, hashed_password, expected_password)
    else:
        aaa.authentication.verify_login(username, hashed_password, expected_password)
