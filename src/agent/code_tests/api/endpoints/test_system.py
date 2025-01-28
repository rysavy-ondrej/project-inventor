import time

import pytest
import zlib
import base64
import requests

from code_tests.api.connection import call_endpoint
import api.schemas.all as schemas

DOMAIN = "http://127.0.0.1:20001"


@pytest.mark.parametrize("method, endpoint, data", [
    ("GET", "/system/config/all", None),
    ("GET", "/system/orchestrators", None),
    ("GET", "/system/logs?since=1970-01-01", None),
    ("GET", "/system/logs/stats?minutes=10", None),
    ("GET", "/system/accounting?since=1970-01-01", None),
    ("PATCH", "/system/config", {"tests_0": {"test": "Fail"}}),
])
def test_system_missing_root_password(method, endpoint, data):
    status_code, data_raw = call_endpoint(DOMAIN, endpoint, method=method, data=data)
    assert status_code == 403


def test_system_config():
    status_code, data_raw = call_endpoint(DOMAIN, "/system/config", "GET")
    assert status_code == 200

    data = schemas.Config(**data_raw)
    assert "public" in data.options
    assert len(data.options.keys()) == 1
    assert "version" in data.options["public"]


def test_system_config_patch():
    option_section = "tests_" + str(time.time())
    option_name = "test"
    option_value_1 = "True"
    option_value_2 = "False"

    # create new section
    data = {option_section: {option_name: option_value_1}}
    status_code, data_raw = call_endpoint(DOMAIN, "/system/config", "PATCH", "root", data=data)
    assert status_code == 200
    data = schemas.ConfigChanges(**data_raw)
    action = data.options[option_section][option_name]
    assert action == "added"

    # check if it was properly created
    status_code, data_raw = call_endpoint(DOMAIN, "/system/config/all", "GET", "root")
    data = schemas.Config(**data_raw)
    value = data.options[option_section][option_name]
    assert value == option_value_1

    # update value
    data = {option_section: {option_name: option_value_2}}
    status_code, data_raw = call_endpoint(DOMAIN, "/system/config", "PATCH", "root", data=data)
    assert status_code == 200
    data = schemas.ConfigChanges(**data_raw)
    action = data.options[option_section][option_name]
    assert action == "updated"

    # check if it was properly updated
    status_code, data_raw = call_endpoint(DOMAIN, "/system/config/all", "GET", "root")
    data = schemas.Config(**data_raw)
    value = data.options[option_section][option_name]
    assert value == option_value_2


def test_system_config_all():
    status_code, data_raw = call_endpoint(DOMAIN, "/system/config/all", "GET", "root")
    assert status_code == 200

    data = schemas.Config(**data_raw)
    assert "public" in data.options
    assert "version" in data.options["public"]
    assert "api" in data.options
    assert "server_ip" in data.options["api"]


def test_system_orchestrators():
    status_code, data_raw = call_endpoint(DOMAIN, "/system/orchestrators", "GET", "root")
    assert status_code == 200

    data = schemas.Orchestrators(**data_raw)
    orchestrator_found = False
    for orchestrator in data.orchestrators:
        if orchestrator.name == "code_tests":
            orchestrator_found = True
            print(orchestrator)
            break
    assert orchestrator_found is True


def test_system_orchestrators_updating_last_seen():
    status_code, data_raw = call_endpoint(DOMAIN, "/system/orchestrators", "GET", "root")
    data = schemas.Orchestrators(**data_raw)
    orchestrator_before = None
    for orchestrator in data.orchestrators:
        if orchestrator.name == "code_tests":
            orchestrator_before = orchestrator
            break

    status_code, data_raw = call_endpoint(DOMAIN, "/system/orchestrators", "GET", "root")
    data = schemas.Orchestrators(**data_raw)
    orchestrator_now = None
    for orchestrator in data.orchestrators:
        if orchestrator.name == "code_tests":
            orchestrator_now = orchestrator
            break

    assert orchestrator_before is not None
    assert orchestrator_now is not None
    assert orchestrator_before.last_seen < orchestrator_now.last_seen


def test_system_logs_adding_new_records():
    params = {"since": "1970-01-01"}
    last_request = False
    first_last_datetime = None
    while last_request is False:
        status_code, data_raw = call_endpoint(DOMAIN, f"/system/logs", "GET", "root", data=params)
        data = schemas.Accounting(**data_raw)
        first_last_datetime = data.last_datetime
        params["since"] = first_last_datetime
        last_request = data.more_data is False

    status_code, data_raw = call_endpoint(DOMAIN, f"/system/logs/stats", "GET", "root", data={"minutes": 10})
    data = schemas.LogsStats(**data_raw)
    first_errors_count = data.error

    # simulate error on server by sending incorrect auth token
    response = requests.get(DOMAIN + f"/", headers={"Authorization": f"Bearer blablabla"})
    assert response.status_code == 401

    last_request = False
    second_last_datetime = None
    while last_request is False:
        status_code, data_raw = call_endpoint(DOMAIN, f"/system/logs", "GET", "root", data=params)
        data = schemas.Accounting(**data_raw)
        second_last_datetime = data.last_datetime
        params["since"] = second_last_datetime
        last_request = data.more_data is False

    status_code, data_raw = call_endpoint(DOMAIN, f"/system/logs/stats", "GET", "root", data={"minutes": 10})
    data = schemas.LogsStats(**data_raw)
    second_errors_count = data.error

    assert first_errors_count < second_errors_count
    assert first_last_datetime < second_last_datetime


@pytest.mark.parametrize("endpoint_part", [
    "logs",
    "accounting",
])
def test_system_accounting_compression(endpoint_part):
    params = {"since": "1970-01-01"}
    last_request = False
    uncompressed_size = 0
    while last_request is False:
        status_code, data_raw = call_endpoint(DOMAIN, f"/system/{endpoint_part}", "GET", "root", data=params)
        data = schemas.Accounting(**data_raw)
        uncompressed_size += len(data.data)
        params["since"] = data.last_datetime
        last_request = data.more_data is False

    params = {"since": "1970-01-01", "compression_alg": "zlib_base85"}
    last_request = False
    compressed_size = 0
    last_compressed_data = ""
    while last_request is False:
        status_code, data_raw = call_endpoint(DOMAIN, f"/system/{endpoint_part}", "GET", "root", data=params)
        data = schemas.Accounting(**data_raw)
        compressed_size += len(data.data)
        last_compressed_data = data.data
        params["since"] = data.last_datetime
        last_request = data.more_data is False

    assert uncompressed_size > compressed_size

    binary_data = base64.b85decode(last_compressed_data)
    decompressed_data = zlib.decompress(binary_data)
    assert len(decompressed_data) > compressed_size


@pytest.mark.parametrize("endpoint_part", [
    "logs",
    "accounting",
])
def test_system_accounting_max_size(endpoint_part):
    params = {"since": "1970-01-01", "max_size": 1}
    status_code, data_raw = call_endpoint(DOMAIN, f"/system/{endpoint_part}", "GET", "root", data=params)
    data = schemas.Accounting(**data_raw)
    assert len(data.data) == 0

    params = {"since": "1970-01-01", "max_size": 1000}
    status_code, data_raw = call_endpoint(DOMAIN, f"/system/{endpoint_part}", "GET", "root", data=params)
    data = schemas.Accounting(**data_raw)
    assert 0 < len(data.data) <= 1000


def test_system_accounting_adding_new_records():
    params = {"since": "1970-01-01"}
    last_request = False
    first_last_datetime = None
    while last_request is False:
        status_code, data_raw = call_endpoint(DOMAIN, f"/system/accounting", "GET", "root", data=params)
        data = schemas.Accounting(**data_raw)
        first_last_datetime = data.last_datetime
        params["since"] = first_last_datetime
        last_request = data.more_data is False

    last_request = False
    second_last_datetime = None
    while last_request is False:
        status_code, data_raw = call_endpoint(DOMAIN, f"/system/accounting", "GET", "root", data=params)
        data = schemas.Accounting(**data_raw)
        second_last_datetime = data.last_datetime
        params["since"] = second_last_datetime
        last_request = data.more_data is False

    assert first_last_datetime < second_last_datetime
