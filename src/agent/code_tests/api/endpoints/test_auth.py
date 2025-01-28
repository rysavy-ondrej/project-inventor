import string
import time
import random

import pytest
import requests

from aaa import encryption

DOMAIN = "http://127.0.0.1:20001"


def test_auth_time():
    endpoint = f"/auth/time"
    response = requests.get(DOMAIN + endpoint)

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    data = response.json()
    assert isinstance(data, dict)
    assert "time" in data
    now = time.time()
    time_difference = abs(data["time"] - now)
    assert time_difference < 1.0


@pytest.mark.parametrize("username, password, status_code", [
    ("code_tests", "b829ad09267ed6aeba9eaa54c93e7f57223a13e0085e8ed9ab23e1c85bdf94e3", 200),
    ("code_tests", "incorrect_hash", 401),
    ("code_tests", "", 422),
    ("wrong_name", "b829ad09267ed6aeba9eaa54c93e7f57223a13e0085e8ed9ab23e1c85bdf94e3", 401),
])
def test_auth_token(username, password, status_code):
    endpoint = "/auth/token"
    data = {"grant_type": "password", "username": username, "password": password}
    response = requests.post(DOMAIN + endpoint, data=data)

    assert response.status_code == status_code
    assert response.headers["Content-Type"] == "application/json"
    data = response.json()
    assert isinstance(data, dict)
    if status_code == 200:
        assert "access_token" in data
        assert len(data["access_token"]) > 0
    else:
        assert "detail" in data


@pytest.fixture
def access_token():
    endpoint = "/auth/token"
    username = "code_tests"
    password = "b829ad09267ed6aeba9eaa54c93e7f57223a13e0085e8ed9ab23e1c85bdf94e3"
    data = {"grant_type": "password", "username": username, "password": password}
    response = requests.post(DOMAIN + endpoint, data=data)

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    data = response.json()
    assert isinstance(data, dict)
    assert "access_token" in data
    access_token = data["access_token"]
    assert len(access_token) > 0
    return access_token


@pytest.mark.parametrize("auth_time, auth_hmac, auth_nonce, expected_code", [
    ("correct", "correct", "correct", 200),
    ("too_old", "correct", "correct", 403),
    ("too_new", "correct", "correct", 403),
    ("correct", "incorrect", "correct", 403),
    ("correct", "correct", "reuse", 403),
    ("too_old", "xdev", "reuse", 200),
])
def test_authorization_headers(access_token, auth_time, auth_hmac, auth_nonce, expected_code):
    endpoint = f"/system/orchestrators"
    if auth_time == "too_old":
        auth_time = time.time() - + 1000000
    elif auth_time == "too_new":
        auth_time = time.time() + 1000000
    else:
        auth_time = time.time()
    auth_time = str(auth_time)

    if auth_nonce in ["reuse", "correct"]:
        timestamp_part = str(time.time())
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        new_auth_nonce = timestamp_part + random_part
        if auth_nonce == "reuse":
            # first do a valid request to save the nonce on the server
            test_authorization_headers(access_token, "correct", "correct", new_auth_nonce, 200)
            # now the auth_nonce has already been used
    else:
        new_auth_nonce = auth_nonce  # just use the value from argument

    if auth_hmac == "incorrect":
        auth_hmac = "incorrect_value"
    elif auth_hmac == "xdev":
        auth_hmac = "xdev"
    else:
        message = (
            "GET"
            + endpoint
            + ""  # params
            + ""  # body_str
            + auth_time
            + new_auth_nonce
            + "QUFuJv3uFXPSdlQ6byzKYg"  # root password
        )
        auth_hmac = encryption.calculate_hash(message)

    header = {"Authorization": f"Bearer {access_token}", "authorization-time": auth_time, "authorization-hmac": auth_hmac, "authorization-nonce": new_auth_nonce}
    response = requests.get(DOMAIN + endpoint, headers=header)

    assert response.status_code == expected_code
    assert response.headers["Content-Type"] == "application/json"
    data = response.json()
    assert isinstance(data, dict)
