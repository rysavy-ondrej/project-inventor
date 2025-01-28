import json
import time
from typing import Optional

from fastapi import Header, HTTPException, Request, status

import aaa.encryption as encryption
import database.daoaggregator
from utils import logs
from utils.configuration import config


def authorization_headers(
    authorization_time: str = Header(),
    authorization_hmac: str = Header(),
    authorization_nonce: str = Header(),
) -> None:
    """
    Empty function that just groups all the headers that are needed for the authorization, so it's not necessary to specify all of them everytime.
    """
    pass


async def verify_hmac(request: Request, expected_password: str) -> bool:
    request_time = request.headers.get("authorization-time", "")
    request_hmac = request.headers.get("authorization-hmac", "")
    request_nonce = request.headers.get("authorization-nonce", "")
    method = request.scope.get("method", "")
    path = request.scope.get("path", "")
    params = request.scope.get("query_string", b"").decode("utf-8")
    body = await request.body()
    if len(body):
        body_json = await request.json()
        body_str = json.dumps(body_json, sort_keys=True)
    else:
        body_str = ""

    message = (
        method
        + path
        + params
        + body_str
        + request_time
        + request_nonce
        + expected_password
    )
    expected_hmac = encryption.calculate_hash(message)
    return request_hmac == expected_hmac


def verify_request_time(request: Request) -> None:
    hmac_time = request.headers.get("authorization-time", None)
    if hmac_time is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing request time for authorization.",
        )

    try:
        hmac_time = float(hmac_time)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Request time for authorization has wrong format.",
        )

    now = time.time()
    if hmac_time > now or hmac_time + config.authorization_request_validity_int < now:
        diff = now - hmac_time
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Wrong request time (diff {diff}s).",
        )


def verify_request_nonce(request: Request) -> None:
    request_nonce = request.headers.get("authorization-nonce", "")
    db = database.daoaggregator.get_dao_aggregator()
    found = db.nonces.get_by_nonce(request_nonce)
    if len(found):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The nonce has already been used.",
        )
    db.nonces.create(request_nonce, time.time())


async def authorize_request(
    request: Request, root_key: str, test_key: Optional[str] = None
) -> None:
    if (
        request.headers.get("authorization-hmac", None) == "xdev"
    ):  # TODO: temporary for developing purposes
        return

    verify_request_time(request)
    verify_request_nonce(request)

    if test_key:
        if await verify_hmac(request, test_key):
            return
        else:
            logs.warning(
                "The authorization token doesn't match the value expected by the test."
            )

    if await verify_hmac(request, root_key):
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Wrong authorization token."
    )
