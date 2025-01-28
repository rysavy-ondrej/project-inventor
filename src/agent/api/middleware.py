import time
from typing import Any, Callable

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

import aaa.accounting as accounting
import aaa.authentication as authentication
import database.daoaggregator as daoaggregator
from utils.exceptions import TransactionError


async def middleware_accounting(
    request: Request, call_next: Callable, orchestrator_name: str
) -> Any:
    body_bytes = await request.body()
    body = body_bytes.decode("utf-8").replace("\n", "\\n")
    try:
        response = await call_next(request)
    except HTTPException as exception:
        accounting.record(orchestrator_name, request, body, exception.status_code)
        raise exception
    accounting.record(orchestrator_name, request, body, response.status_code)
    return response


async def get_orchestrator_name_from_token(request: Request) -> str:
    bearer_token: str = request.headers.get("Authorization").split("Bearer")[1].strip()
    token_data = await authentication.get_data_from_auth_token(request, bearer_token)
    orchestrator_name = token_data.orchestrator_name
    return orchestrator_name


def user_is_authenticated(request: Request) -> bool:
    return "Bearer" in request.headers.get("Authorization", "")


async def process_request(
    request: Request,
    call_next: Callable,
) -> Any:
    if user_is_authenticated(request):
        orchestrator_name = await get_orchestrator_name_from_token(request)
        db = daoaggregator.get_dao_aggregator()
        db.orchestrators.update(orchestrator_name, time.time())
        db.close()
        response = await middleware_accounting(request, call_next, orchestrator_name)
    else:
        response = await call_next(request)
    return response


class Accounting(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Any:
        try:
            return await process_request(request, call_next)
        except TransactionError:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={'message': "Could not get data from the token."})
