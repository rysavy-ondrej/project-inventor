from aaa import encryption
from code_tests.api.connection import call_endpoint
import api.schemas.all as schemas
from utils import enums

DOMAIN = "http://127.0.0.1:20001"


def test_multi_results():
    existing_test_id = 1
    multi_result_key = "multikey"

    test_data = {
      "key": multi_result_key
    }

    # create new multi results record
    status_code, data_raw = call_endpoint(DOMAIN, "/multi-results/init", "POST", password_type="", data=test_data)
    data = schemas.MultiResultId(**data_raw)
    multi_result_id = data.id_multi_result
    assert multi_result_id > 0

    # multi results is not mapped with any test, it must return empty results
    request_data = {"since_id": 0}
    status_code, data_raw = call_endpoint(DOMAIN, f"/multi-results/{multi_result_id}", "GET", password_type="multikey", data=request_data)
    assert status_code == 200
    data = schemas.MultiResult(**data_raw)
    assert data.last_checked_id > 0
    assert data.results == {}

    # map a non-existing test to multi test record
    request_data = {
        "fk_tests": 0,
        "hash": "string"
    }
    status_code, data_raw = call_endpoint(DOMAIN, f"/multi-results/{multi_result_id}", "POST", password_type="multikey", data=request_data)
    assert status_code == 404

    # map an existing test with a wrong test key to multi test record
    request_data = {
        "fk_tests": existing_test_id,
        "hash": "string"
    }
    status_code, data_raw = call_endpoint(DOMAIN, f"/multi-results/{multi_result_id}", "POST", password_type="multikey", data=request_data)
    assert status_code == 403

    # map an existing test to wrong multi test record
    request_data = {
        "fk_tests": existing_test_id,
        "hash": "string"
    }
    status_code, data_raw = call_endpoint(DOMAIN, f"/multi-results/999999", "POST", password_type="RO", data=request_data)
    assert status_code == 404

    # map an existing test to multi test record with wrong multi result hash
    request_data = {
        "fk_tests": existing_test_id,
        "hash": "string"
    }
    status_code, data_raw = call_endpoint(DOMAIN, f"/multi-results/{multi_result_id}", "POST", password_type="RO", data=request_data)
    assert status_code == 403

    multitest_hash = encryption.calculate_hash(
        f"{multi_result_key}{multi_result_id}{existing_test_id}"
    )

    # map an existing test to multi test record with correct hash
    request_data = {
        "fk_tests": existing_test_id,
        "hash": multitest_hash
    }
    status_code, data_raw = call_endpoint(DOMAIN, f"/multi-results/{multi_result_id}", "POST", password_type="RO", data=request_data)
    data = schemas.MultiResultTestsIds(**data_raw)
    assert status_code == 200
    assert data.test_ids == str(existing_test_id)

    # multi results is not mapped with any test, it must return one result
    request_data = {"since_id": 0}
    status_code, data_raw = call_endpoint(DOMAIN, f"/multi-results/{multi_result_id}", "GET", password_type="multikey", data=request_data)
    assert status_code == 200
    data = schemas.MultiResult(**data_raw)
    assert data.last_checked_id > 0
    expected_result = {1: schemas.Results(results=[schemas.Result(fk_tests=1, version=1, planned=1.0, started=2.0, finished=3.0, status=enums.ResultStatus.success, recovery_attempt=0, data='{"data":"ok"}', id_result=1)])}
    assert data.results == expected_result

    # map already mapped test to multi test record with correct multi result hash
    request_data = {
        "fk_tests": existing_test_id,
        "hash": multitest_hash
    }
    status_code, data_raw = call_endpoint(DOMAIN, f"/multi-results/{multi_result_id}", "POST", password_type="RO", data=request_data)
    data = schemas.MultiResultTestsIds(**data_raw)
    assert status_code == 200
    assert data.test_ids == str(existing_test_id)

    # map another existing test to multi test record with wrong multi result hash
    another_existing_test_id = 2
    multitest_hash = encryption.calculate_hash(
        f"{multi_result_key}{multi_result_id}{another_existing_test_id}"
    )
    request_data = {
        "fk_tests": another_existing_test_id,
        "hash": multitest_hash
    }
    status_code, data_raw = call_endpoint(DOMAIN, f"/multi-results/{multi_result_id}", "POST", password_type="RO", data=request_data)
    data = schemas.MultiResultTestsIds(**data_raw)
    assert status_code == 200
    assert data.test_ids == f"{existing_test_id},{another_existing_test_id}"

    # multi results is not mapped with any test, it must return two results
    request_data = {"since_id": 0}
    status_code, data_raw = call_endpoint(DOMAIN, f"/multi-results/{multi_result_id}", "GET", password_type="multikey", data=request_data)
    assert status_code == 200
    data = schemas.MultiResult(**data_raw)
    assert data.last_checked_id > 0
    expected_result = {1: schemas.Results(results=[schemas.Result(fk_tests=1, version=1, planned=1.0, started=2.0, finished=3.0, status=enums.ResultStatus.success, recovery_attempt=0, data='{"data":"ok"}', id_result=1)]),
                       2: schemas.Results(results=[])}
    assert data.results == expected_result

    # requesting a non existing multi result
    request_data = {"since_id": 0}
    status_code, data_raw = call_endpoint(DOMAIN, f"/multi-results/987654321", "GET", password_type="multikey", data=request_data)
    assert status_code == 404
