from code_tests.api.connection import call_endpoint
import api.schemas.all as schemas
from utils import enums

DOMAIN = "http://127.0.0.1:20001"


def test_create_and_get_test():
    test_data = {
      "description": "test_description",
      "key_ro": "test_key_ro",
      "key_rw": "test_key_rw",
      "name": "code_test",
      "recovery_attempt_limit": 1,
      "recovery_interval": 2,
      "scheduling_from": 3,
      "scheduling_interval": 4,
      "scheduling_until": 999999999,
      "state": "enabled",
      "test_params": 'test_params',
      "timeout": 5,
      "version": 6
    }

    # retrieve the non-existing test
    status_code, data_raw = call_endpoint(DOMAIN, f"/test/987654321", "GET", password_type="test_key_ro")
    assert status_code == 404

    # create a new test
    status_code, data_raw = call_endpoint(DOMAIN, "/test", "POST", password_type="new_tests", data=test_data)
    assert status_code == 200
    data = schemas.Test(**data_raw)
    for key in test_data.keys():
        value = getattr(data, key)
        if key == "state":
            assert str(value) == "TestState.enabled"
        else:
            assert value == test_data[key]
    id_test = data.id_test

    # retrieve the test with no password
    status_code, data_raw = call_endpoint(DOMAIN, f"/test/{id_test}", "GET", password_type="")
    assert status_code == 403

    # retrieve the test with read-only password
    status_code, data_raw = call_endpoint(DOMAIN, f"/test/{id_test}", "GET", password_type="test_key_ro")
    assert status_code == 200

    # retrieve the test with read-write password
    status_code, data_raw = call_endpoint(DOMAIN, f"/test/{id_test}", "GET", password_type="test_key_rw")
    assert status_code == 403

    # retrieve the test with root password and check the content
    status_code, data_raw = call_endpoint(DOMAIN, f"/test/{id_test}", "GET", password_type="root")
    assert status_code == 200
    data = schemas.Test(**data_raw)
    for key in test_data.keys():
        value = getattr(data, key)
        if key == "state":
            assert str(value) == "TestState.enabled"
        else:
            assert value == test_data[key]

    change_data = {
      "description": "test_description_updated",
      "recovery_attempt_limit": 10,
      "recovery_interval": 20,
      "scheduling_from": 30,
      "scheduling_interval": 40,
      "scheduling_until": 888888888,
      "state": "enabled",
      "test_params": 'test_params_updated',
      "timeout": 50,
      "version": 7
    }

    # update with read-only password should not work
    status_code, data_raw = call_endpoint(DOMAIN, f"/test/{id_test}", "PATCH", password_type="test_key_ro", data=change_data)
    assert status_code == 403

    # update with read-write password
    status_code, data_raw = call_endpoint(DOMAIN, f"/test/{id_test}", "PATCH", password_type="test_key_rw", data=change_data)
    assert status_code == 200

    # check that the test has been updated
    status_code, data_raw = call_endpoint(DOMAIN, f"/test/{id_test}", "GET", password_type="root")
    assert status_code == 200
    data = schemas.Test(**data_raw)
    for key in change_data.keys():
        value = getattr(data, key)
        if key == "state":
            assert str(value) == "TestState.enabled"
        else:
            assert value == change_data[key]

    # create a new test - enabled
    test_data["state"] = "enabled"
    status_code, data_raw = call_endpoint(DOMAIN, "/test", "POST", password_type="new_tests", data=test_data)
    assert status_code == 200
    data = schemas.Test(**data_raw)
    id_test = data.id_test

    status_code, data_raw = call_endpoint(DOMAIN, f"/test/{id_test}/full", "GET", password_type="test_key_ro")
    assert status_code == 200
    data = schemas.TestFullInfo(**data_raw)
    assert len(data.requests) == 1
    request = data.requests[0]
    assert request.id_test == id_test
    assert request.reason == enums.RequestReason.new
    assert request.recovery_attempt == 0
    assert request.id_test == id_test

    # update test - change state
    change_data = {
      "description": test_data["description"],
      "recovery_attempt_limit": test_data["recovery_attempt_limit"],
      "recovery_interval": test_data["recovery_interval"],
      "scheduling_from": test_data["scheduling_from"],
      "scheduling_interval": test_data["scheduling_interval"],
      "scheduling_until": test_data["scheduling_until"],
      "state": "disabled",
      "test_params": test_data["test_params"],
      "timeout": test_data["timeout"],
      "version": test_data["version"]
    }
    status_code, data_raw = call_endpoint(DOMAIN, f"/test/{id_test}", "PATCH", password_type="test_key_rw", data=change_data)
    assert status_code == 200

    status_code, data_raw = call_endpoint(DOMAIN, f"/test/{id_test}/full", "GET", password_type="test_key_ro")
    assert status_code == 200
    data = schemas.TestFullInfo(**data_raw)
    assert len(data.requests) == 2
    request = data.requests[1]
    assert request.id_test == id_test
    assert request.reason == enums.RequestReason.update
    assert request.recovery_attempt == 0
    assert request.id_test == id_test

    status_code, data_raw = call_endpoint(DOMAIN, f"/test/{id_test}", "GET", password_type="test_key_ro")
    assert status_code == 200
    data = schemas.Test(**data_raw)
    assert data.version == 6



def test_get_all_tests():
    # retrieve all tests with not password
    status_code, data_raw = call_endpoint(DOMAIN, f"/test/all", "GET", password_type="")
    assert status_code == 403

    # retrieve all tests with root password
    status_code, data_raw = call_endpoint(DOMAIN, f"/test/all", "GET", password_type="root")
    assert status_code == 200
    data = schemas.Tests(**data_raw)
    assert data.tests[0].name == 'test'


def test_get_test_full():
    id_test = 1
    # retrieve all information about test with not password
    status_code, data_raw = call_endpoint(DOMAIN, f"/test/{id_test}/full", "GET", password_type="")
    assert status_code == 403

    # retrieve all information about test with root password
    status_code, data_raw = call_endpoint(DOMAIN, f"/test/{id_test}/full", "GET", password_type="RO")
    assert status_code == 200
    data = schemas.TestFullInfo(**data_raw)
    assert data.test.name == "test"
    assert data.requests[0].id_test == 1
    assert data.events[0].id_test == 1
    assert data.runs[0].id_test == 1
    assert data.results[0].id_test == 1
    assert data.old_params[0].id_test == 1


def test_get_test_results():
    id_test = 1
    params = {"since_id": 0}
    # retrieve all test results with not password
    status_code, data_raw = call_endpoint(DOMAIN, f"/test/{id_test}/results", "GET", password_type="", data=params)
    assert status_code == 403

    # retrieve all test results with RO password
    status_code, data_raw = call_endpoint(DOMAIN, f"/test/{id_test}/results", "GET", password_type="RO", data=params)
    assert status_code == 200
    data = schemas.Results(**data_raw)
    assert data.results[0].id_result == 1


def test_get_test_events():
    id_test = 1
    # retrieve all test events with not password
    status_code, data_raw = call_endpoint(DOMAIN, f"/test/{id_test}/events", "GET", password_type="")
    assert status_code == 403

    # retrieve all test events with RO password
    status_code, data_raw = call_endpoint(DOMAIN, f"/test/{id_test}/events", "GET", password_type="RO")
    assert status_code == 200
    data = schemas.Events(**data_raw)
    assert data.events[0].id_event == 1


def test_get_test_old_params():
    id_test = 1
    version = 1
    # retrieve specific test old params with not password
    status_code, data_raw = call_endpoint(DOMAIN, f"/test/{id_test}/old_params/{version}", "GET", password_type="")
    assert status_code == 403

    # retrieve specific test old params with RO password
    status_code, data_raw = call_endpoint(DOMAIN, f"/test/{id_test}/old_params/{version}", "GET", password_type="RO")
    assert status_code == 200
    data = schemas.OldParams(**data_raw)
    assert data.id_old_params == 1

    # retrieve all old params with RO password
    status_code, data_raw = call_endpoint(DOMAIN, f"/test/{id_test}/old_params", "GET", password_type="RO")
    assert status_code == 200
    data = schemas.OldParamsList(**data_raw)
    assert len(data.old_params) == 2
    assert data.old_params[0].id_old_params == 1
    assert data.old_params[1].id_old_params == 2


def test_post_test_request():
    id_test = 1

    # create an event for test with not password
    status_code, data_raw = call_endpoint(DOMAIN, f"/test/{id_test}/request", "POST", password_type="")
    assert status_code == 403

    # create an event for test with RO password
    status_code, data_raw = call_endpoint(DOMAIN, f"/test/{id_test}/request", "POST", password_type="RO")
    assert status_code == 403

    # create an event for test with RW password
    status_code, data = call_endpoint(DOMAIN, f"/test/{id_test}/request", "POST", password_type="RW")
    assert status_code == 200
    added_request_id = data

    # retrieve all information about test with root password
    status_code, data_raw = call_endpoint(DOMAIN, f"/test/{id_test}/full", "GET", password_type="RO")
    assert status_code == 200
    data = schemas.TestFullInfo(**data_raw)
    last_request_id = getattr(data.requests[-1], "id_request", None)
    assert added_request_id == last_request_id
