import hashlib
import json
import time

import requests
from fastapi import status
from http.client import responses
from urllib.parse import urlencode
import string
import random


class AgentApi:
    def __init__(self, url: str, username: str, password: str, debug=True):
        self._url = url if not url.endswith("/") else url[:-1]
        self._username = username
        self._password = password
        self._token = ""
        self._time_diff = 0
        self._debug = debug
        self._authenticate()

    def calculate_time_diff(self):
        code, response = self.request("GET", "/auth/time", password=None)
        if code == 200:
            self._time_diff = response["time"] - time.time()

    def _authenticate(self) -> None:
        url = self._url + "/auth/token"
        hashing_value = self._username + self._password
        hashed_password = hashlib.sha256(hashing_value.encode("utf-8")).hexdigest()
        data = {"username": self._username, "password": hashed_password}
        response = requests.post(url, data=data)
        if response.status_code != status.HTTP_200_OK:
            raise Exception("Unable to authentication on Agent")
        self._token = response.json()["access_token"]
        self.calculate_time_diff()

    def _call_request(self, method, endpoint, params, data, expected_password):
        if data:
            data = json.dumps(data, sort_keys=True)

        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self._token}"
        }

        if expected_password is not None:
            expected_server_time = str(time.time() + self._time_diff)
            random_nonce = ''.join(
                random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=16))
            params_str = urlencode(params) if params is not None else ""
            data_str = str(data) if data is not None else ""

            message = (
                    method
                    + endpoint
                    + params_str
                    + data_str
                    + expected_server_time
                    + random_nonce
                    + expected_password
            )
            hmac = hashlib.sha256(message.encode("utf-8")).hexdigest()
            headers["authorization-time"] = expected_server_time
            headers["authorization-hmac"] = hmac
            headers["authorization-nonce"] = random_nonce


        return requests.request(method, self._url + endpoint, params=params, data=data, headers=headers)

    def request(self, method, endpoint, password, params=None, data=None) -> tuple[int, dict]:
        response = self._call_request(method, endpoint, params, data, password)
        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            self._authenticate()
            response = self._call_request(method, endpoint, params, data, password)
        if self._debug:
            print(f"{method} {endpoint} - {responses[response.status_code]} ({response.status_code})")
            print(json.dumps(response.json(), indent=4, sort_keys=True))
            print("")
        return response.status_code, response.json()
