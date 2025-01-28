import hashlib
import json
import urllib.parse
from pathlib import Path
import string
import time
import random
from typing import Dict, Optional
import requests
import configparser
from aaa import encryption

AUTH_TOKEN = None
SERVER_TIME_DIFF = 0
CACHED_PASSWORDS = {}


def get_time_on_server(domain):
    endpoint = f"/auth/time"
    response = requests.get(domain + endpoint)
    data = response.json()
    return float(data["time"])


def calculate_time_difference_with_server(domain):
    global SERVER_TIME_DIFF
    server_time = get_time_on_server(domain)
    time_diff = server_time - time.time()
    SERVER_TIME_DIFF = time_diff


def get_current_server_time():
    global SERVER_TIME_DIFF
    return str(time.time() + SERVER_TIME_DIFF)


def get_path_to_config_file():
    folder_name = "persistent_data"
    config_file = "config.ini"
    current_path = Path.cwd()

    while True:
        if (current_path / folder_name).exists():
            return current_path / folder_name / config_file
        else:
            parent_path = current_path.parent
            if current_path == parent_path:  # If the current path is the root directory
                raise Exception(f"Unable to find folder '{folder_name}' that contains the configuration file.")
            current_path = parent_path


def get_value_from_config_file(section: str, option: str):
    config_file = get_path_to_config_file()
    config = configparser.ConfigParser()
    config.read(config_file)
    value = config.get(section, option)
    return value


def get_password(password_type: Optional[str]):
    global CACHED_PASSWORDS
    if password_type not in CACHED_PASSWORDS:
        if password_type == "login":
            password = get_value_from_config_file("authentication", "password")
        elif password_type == "root":
            password = get_value_from_config_file("authorization", "root_password")
        elif password_type == "new_tests":
            password = get_value_from_config_file("authorization", "new_tests_password")
        elif password_type is None:
            password = ""
        else:
            password = password_type
        CACHED_PASSWORDS[password_type] = password

    return CACHED_PASSWORDS[password_type]


def request_auth_token_from_server(domain: str):
    username = "code_tests"
    password = get_password("login")
    hashing_value = username + password
    hashed_password = hashlib.sha256(hashing_value.encode("utf-8")).hexdigest()
    endpoint = "/auth/token"
    data = {"grant_type": "password", "username": username, "password": hashed_password}
    response = requests.post(domain + endpoint, data=data)
    data = response.json()
    return data["access_token"]


def get_random_nonce():
    timestamp_part = str(time.time())
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    auth_nonce = timestamp_part + random_part
    return auth_nonce


def get_auth_token(domain):
    global AUTH_TOKEN
    if AUTH_TOKEN is None:
        calculate_time_difference_with_server(domain)
        AUTH_TOKEN = request_auth_token_from_server(domain)
    return AUTH_TOKEN


def call_endpoint(domain: str, endpoint: str, method: str, password_type: Optional[str] = None, data: Optional[Dict] = None):
    auth_token = get_auth_token(domain)
    request_time = get_current_server_time()
    request_nonce = get_random_nonce()

    if method in ["POST", "PATCH"]:
        body_str = json.dumps(data, sort_keys=True) if data else ""
        params_str = ""
    else:
        body_str = ""
        params_str = urllib.parse.urlencode(data, doseq=True) if data else ""

    message = (
        method
        + endpoint
        + params_str
        + body_str
        + request_time
        + request_nonce
        + get_password(password_type)
    )
    auth_hmac = encryption.calculate_hash(message)

    headers = {
        "Authorization": f"Bearer {auth_token}",
        "authorization-time": request_time,
        "authorization-hmac": auth_hmac,
        "authorization-nonce": request_nonce,
        "Content-Type": "application/json",
        "accept": "application/json"
    }
    if method == "GET":
        response = requests.get(domain + endpoint, params=data, headers=headers)
    elif method == "POST":
        response = requests.post(domain + endpoint, json=data, headers=headers)
    elif method == "PATCH":
        response = requests.patch(domain + endpoint, json=data, headers=headers)
    elif method == "DELETE":
        response = requests.delete(domain + endpoint, json=data, headers=headers)
    else:
        raise Exception(f"Unknown method {method}")
    data = response.json()
    return response.status_code, data
