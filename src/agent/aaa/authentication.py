import time

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

import aaa.encryption as encryption
import api.schemas.all as schemas

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
token_key = ""


def create_auth_token(
    orchestrator_name: str, orchestrator_ip: str, token_validity: int
) -> str:
    expiration = int(time.time()) + token_validity
    data = schemas.TokenData(
        orchestrator_name=orchestrator_name,
        orchestrator_ip=orchestrator_ip,
        expiration=expiration,
    )
    encoded_data = encryption.encrypt(data.model_dump(), token_key)
    return encoded_data


async def get_data_from_auth_token(
    request: Request, token: str = Depends(oauth2_scheme)
) -> schemas.TokenData:
    data = encryption.decrypt(token, token_key)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not get data from the token.",
        )
    token_data = schemas.TokenData(**data)
    if str(request.client.host) != token_data.orchestrator_ip:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The token was assigned to a different IP.",
        )
    return token_data


def verify_login(username: str, password: str, expected_password: str) -> None:
    expected_hash = encryption.calculate_hash(username + expected_password)
    if expected_hash != password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong login information."
        )
