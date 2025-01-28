import time

from fastapi import APIRouter, Depends, HTTPException, Request, status

import aaa.authentication as authentication
import aaa.authorization as authorization
import api.schemas.all as schemas
from database import daoaggregator
from database.daoaggregator import DAOAggregator
from utils import enums
from utils.configuration import config

router = APIRouter(
    prefix="/test",
    tags=["Tests"],
    dependencies=[
        Depends(authentication.get_data_from_auth_token),
        Depends(authorization.authorization_headers),
    ],
)


def find_test(db: DAOAggregator, id_test: int) -> schemas.Test:
    test = db.tests.get_by_id(id_test)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Test doesn't exist"
        )
    return test


@router.get(
    "/all",
    response_model=schemas.Tests,
    summary="Retrieve all the tests specified on the agent.",
)
async def get_test_all(
    request: Request, db: DAOAggregator = Depends(daoaggregator.get_dao_aggregator)
) -> schemas.Tests:
    await authorization.authorize_request(request, config.authorization_root_password)
    tests_db = db.tests.get_all()
    tests_api = [schemas.Test(**t.__dict__) for t in tests_db]
    endpoint_result = schemas.Tests(tests=tests_api)
    return endpoint_result


@router.get(
    "/{id_test}",
    response_model=schemas.Test,
    summary="Retrieve information about the test.",
)
async def get_test(
    id_test: int, request: Request, db: DAOAggregator = Depends(daoaggregator.get_dao_aggregator)
) -> schemas.Test:
    test = find_test(db, id_test)
    await authorization.authorize_request(
        request, config.authorization_root_password, test.key_ro
    )
    endpoint_result = schemas.Test(**test.__dict__)
    return endpoint_result


@router.get(
    "/{id_test}/full",
    response_model=schemas.TestFullInfo,
    summary="Retrieve information from all tables about the test.",
)
async def get_test_full(
    id_test: int, request: Request, db: DAOAggregator = Depends(daoaggregator.get_dao_aggregator)
) -> schemas.TestFullInfo:
    test = find_test(db, id_test)
    await authorization.authorize_request(
        request, config.authorization_root_password, test.key_ro
    )

    requests = db.requests.get_all_by_test_id(test.id_test)
    requests_api = [schemas.Request(**r.__dict__) for r in requests]

    events = db.events.get_all_by_test_id(test.id_test)
    events_api = [schemas.Event(**e.__dict__) for e in events]

    runs = db.runs.get_all_by_test_id(test.id_test)
    runs_api = [schemas.Run(**r.__dict__) for r in runs]

    results = db.results.get_all_by_test_id(test.id_test)
    results_api = [schemas.Result(**r.__dict__) for r in results]

    old_params = db.old_params.get_all_by_test_id(test.id_test)
    old_params_api = [schemas.OldParams(**o.__dict__) for o in old_params]

    endpoint_result = schemas.TestFullInfo(
        test=test.__dict__,
        requests=requests_api,
        events=events_api,
        runs=runs_api,
        results=results_api,
        old_params=old_params_api,
    )
    return endpoint_result


@router.get(
    "/{id_test}/results",
    response_model=schemas.Results,
    summary="Returns the results for the specified test.",
)
async def get_test_results(
    id_test: int,
    request: Request,
    params: schemas.ResultsRequest = Depends(),
    db: DAOAggregator = Depends(daoaggregator.get_dao_aggregator),
) -> schemas.Results:
    test = find_test(db, id_test)
    await authorization.authorize_request(
        request, config.authorization_root_password, test.key_ro
    )
    db.tests.update_last_downloaded_time(id_test, time.time())
    results = db.results.get_all_since_id(id_test, params.since_id)
    results_api = [schemas.Result(**r.__dict__) for r in results]
    endpoint_result = schemas.Results(results=results_api)
    return endpoint_result


@router.get(
    "/{id_test}/events",
    response_model=schemas.Events,
    summary="Returns all the planned events for the specified test.",
)
async def get_test_events(
    id_test: int, request: Request, db: DAOAggregator = Depends(daoaggregator.get_dao_aggregator)
) -> schemas.Events:
    test = find_test(db, id_test)
    await authorization.authorize_request(
        request, config.authorization_root_password, test.key_ro
    )
    events_db = db.events.get_all_by_test_id(id_test)
    events_api = [schemas.Event(**e.__dict__) for e in events_db]
    endpoint_result = schemas.Events(events=events_api)
    return endpoint_result


@router.post(
    "/{id_test}/request",
    response_model=int,
    summary="Create a new test request for an event in the calendar.",
)
async def post_test_request(
    id_test: int,
    request: Request,
    db: DAOAggregator = Depends(daoaggregator.get_dao_aggregator),
) -> schemas.Events:
    test = find_test(db, id_test)
    await authorization.authorize_request(
        request, config.authorization_root_password, test.key_rw
    )
    request = db.requests.create(id_test, enums.RequestReason.new, 0, time.time())
    if not request:  # TODO: after moving from sqllite to postgresql, create a unit test that will check this by failing the integrity check
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to create a request"
        )
    return request.id_request


@router.get(
    "/{id_test}/old_params",
    response_model=schemas.OldParamsList,
    summary="Returns the previous test configuration for a given test and version.",
)
async def get_old_params(
    id_test: int,
    request: Request,
    db: DAOAggregator = Depends(daoaggregator.get_dao_aggregator),
) -> schemas.OldParamsList:
    test = find_test(db, id_test)
    await authorization.authorize_request(
        request, config.authorization_root_password, test.key_ro
    )
    old_params = db.old_params.get_all_by_test_id(id_test)
    old_params_api = [schemas.OldParams(**op.__dict__) for op in old_params]
    endpoint_result = schemas.OldParamsList(old_params=old_params_api)
    return endpoint_result


@router.get(
    "/{id_test}/old_params/{version}",
    response_model=schemas.OldParams,
    summary="Returns the all known previous test configurations for a given test.",
)
async def get_old_params_by_version(
    id_test: int,
    version: int,
    request: Request,
    db: DAOAggregator = Depends(daoaggregator.get_dao_aggregator),
) -> schemas.OldParams:
    test = find_test(db, id_test)
    await authorization.authorize_request(
        request, config.authorization_root_password, test.key_ro
    )
    old_params = db.old_params.get_by_test_id_and_version(id_test, version)
    if not old_params:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Specified old_params for the test doesn't exist."
        )
    endpoint_result = schemas.OldParams(**old_params.__dict__)
    return endpoint_result


@router.post("", response_model=schemas.Test, summary="Create a new test.")
async def post_test(
    request: Request,
    body: schemas.TestCreate,
    db: DAOAggregator = Depends(daoaggregator.get_dao_aggregator),
) -> schemas.Test:
    await authorization.authorize_request(
        request, config.authorization_new_tests_password
    )
    now = time.time()
    test = db.tests.create(body, created=now, transaction_finished=False)
    if not test:  # TODO: after moving from sqllite to postgresql, create a unit test that will check this by failing the integrity check
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to create test"
        )

    if body.state == enums.TestState.enabled:
        db.requests.create(
            test.id_test, enums.RequestReason.new, 0, now, transaction_finished=False
        )

    db.commit()

    endpoint_result = schemas.Test(**test.__dict__)
    return endpoint_result


@router.patch(
    "/{id_test}",
    response_model=schemas.Test,
    summary="Updates the test configuration.",
)
async def patch_test(
    id_test: int,
    request: Request,
    body: schemas.TestUpdate,
    db: DAOAggregator = Depends(daoaggregator.get_dao_aggregator),
) -> schemas.Test:
    test = find_test(db, id_test)
    await authorization.authorize_request(
        request, config.authorization_root_password, test.key_rw
    )
    now = time.time()

    if body.state != test.state:
        db.requests.create(
            test.id_test, enums.RequestReason.update, 0, now, transaction_finished=False
        )

    if body.test_params != test.test_params:
        new_version = test.version + 1
        db.old_params.create(
            test.id_test,
            test.version,
            now,
            test.test_params,
            transaction_finished=False,
        )
    else:
        new_version = test.version

    db.tests.update(
        id_test, **body.model_dump(), version=new_version, transaction_finished=True
    )
    updated_test = db.tests.get_by_id(id_test)
    endpoint_result = schemas.Test(**updated_test.__dict__)
    return endpoint_result
