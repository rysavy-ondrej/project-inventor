import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

import aaa.accounting as accounting
import aaa.authentication as authentication
import api.schemas.all as schemas
import database.daoaggregator as daoaggregator
from utils.configuration import config

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/token", response_model=schemas.Token)
async def post_token(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: daoaggregator.DAOAggregator = Depends(daoaggregator.get_dao_aggregator),
) -> schemas.Token:
    try:
        expected_password = config.authentication_password
        authentication.verify_login(
            form_data.username, form_data.password, expected_password
        )
        db.orchestrators.create_or_update(form_data.username, time.time())
        access_token = authentication.create_auth_token(
            form_data.username,
            request.client.host,
            config.authentication_token_validity_int,
        )
        endpoint_result = schemas.Token(access_token=access_token)
    except HTTPException as exception:
        accounting.record(
            form_data.username,
            request,
            f"ip={request.client.host}",
            exception.status_code,
        )
        raise exception
    accounting.record(
        form_data.username, request, f"ip={request.client.host}", status.HTTP_200_OK
    )
    return endpoint_result


@router.get(
    "/time",
    response_model=schemas.Time,
    summary="Returns the current time on the agent.",
)
async def get_time() -> schemas.Time:
    endpoint_result = schemas.Time(time=time.time())
    return endpoint_result
