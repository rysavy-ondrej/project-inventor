from pydantic import BaseModel, Field

from utils import enums


class RequestBase(BaseModel):
    id_test: int = Field(description="ID of the test.", alias='fk_tests')
    reason: enums.RequestReason = Field(
        description="Specifies why the request was created."
    )
    recovery_attempt: int = Field(
        description="Specifies the recovery counter, which recovery test it is."
    )
    added_time: float = Field(description="Time when the request has been added.")


class Request(RequestBase):
    id_request: int = Field(description="ID of the request.")
