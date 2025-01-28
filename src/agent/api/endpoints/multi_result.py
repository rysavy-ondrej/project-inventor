import time

from fastapi import APIRouter, Depends, HTTPException, Request, status

import aaa.authentication as authentication
import aaa.authorization as authorization
import api.schemas.all as schemas
from aaa import encryption
from database import daoaggregator
from database.daoaggregator import DAOAggregator
from utils.configuration import config

router = APIRouter(
    prefix="/multi-results",
    tags=["Multiple Results"],
    dependencies=[
        Depends(authentication.get_data_from_auth_token),
        Depends(authorization.authorization_headers),
    ],
)


@router.post(
    "/init",
    response_model=schemas.MultiResultId,
    summary="Create a new MultiResult record.",
)
async def post_multi_results_init(
    request: Request,
    body: schemas.MultiResultCreate,
    db: DAOAggregator = Depends(daoaggregator.get_dao_aggregator),
    token_data: schemas.TokenData = Depends(authentication.get_data_from_auth_token),
) -> schemas.MultiResultId:
    await authorization.authorize_request(request, "")
    db.multi_results.delete_by_orchestrator(token_data.orchestrator_name)
    # TODO: replace test_ids from string to list of integers (sqlite->postgresql)
    multi_result = db.multi_results.create(token_data.orchestrator_name, "", body)
    endpoint_result = schemas.MultiResultId(
        id_multi_result=multi_result.id_multi_result
    )
    return endpoint_result


@router.post(
    "/{multi_results_id}",
    response_model=schemas.MultiResultTestsIds,
    summary="Add a new test to the multi result record.",
)
async def post_multi_results(
    multi_results_id: int,
    request: Request,
    body: schemas.MultiResultAddTestInput,
    db: DAOAggregator = Depends(daoaggregator.get_dao_aggregator),
) -> schemas.MultiResultTestsIds:
    test = db.tests.get_by_id(body.id_test)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Test doesn't exist"
        )
    await authorization.authorize_request(
        request, config.authorization_root_password, test.key_ro
    )
    multi_result = db.multi_results.get_by_id(multi_results_id)
    if not multi_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Multi results record doesn't exist",
        )
    if body.hash != encryption.calculate_hash(
        f"{multi_result.key}{multi_result.id_multi_result}{body.id_test}"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Wrong multi tests hash value.",
        )
    test_ids = multi_result.test_ids
    # TODO: replace multi_results / test_ids from string to list of integers (sqlite->postgresql)
    if f",{body.id_test}," not in f",{test_ids},":
        if len(test_ids) > 0:
            test_ids += ","
        test_ids += str(body.id_test)
    db.multi_results.update_test_ids(multi_results_id, test_ids)
    endpoint_result = schemas.MultiResultTestsIds(test_ids=test_ids)
    return endpoint_result


@router.get(
    "/{multi_results_id}",
    response_model=schemas.MultiResult,
    summary="Retrieve the results related to the specified multi results record.",
)
async def get_multi_results(
    multi_results_id: int,
    request: Request,
    params: schemas.ResultsRequest = Depends(),
    db: DAOAggregator = Depends(daoaggregator.get_dao_aggregator),
) -> schemas.MultiResult:
    now = time.time()
    multi_result = db.multi_results.get_by_id(multi_results_id)
    if not multi_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Multi results record doesn't exist",
        )
    await authorization.authorize_request(
        request, config.authorization_root_password, multi_result.key
    )
    db.multi_results.update_last_used_time(multi_results_id, now)
    # TODO: replace test_ids from string to list of integers (sqlite->postgresql)
    test_ids = multi_result.test_ids.split(",")
    last_result_id = db.results.get_last_used_id()
    results_api = {}
    for id_test in test_ids:
        if len(id_test) == 0:
            continue
        id_test = int(id_test)
        db.tests.update_last_downloaded_time(id_test, now)
        results = db.results.get_all_in_id_range(
            id_test, params.since_id, last_result_id
        )
        results_api[id_test] = schemas.Results(results=[schemas.Result(**r.__dict__) for r in results])
    endpoint_result = schemas.MultiResult(
        results=results_api, last_checked_id=last_result_id
    )
    return endpoint_result
