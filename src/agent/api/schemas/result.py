from typing import List, Optional

from fastapi import Path
from pydantic import BaseModel, Field

from utils import enums


class ResultBase(BaseModel):
    id_test: int = Field(description="ID of the test.", alias='fk_tests')
    version: int = Field(
        description="Version of the test, that was used to run the test."
    )
    planned: float = Field(description="Time when the test was planned to start.")
    started: float = Field(description="Time when the test actually started.")
    finished: float = Field(description="Time when the execution of the test finished.")
    status: enums.ResultStatus = Field(
        description="Specifies with what status the test has finished."
    )
    recovery_attempt: int = Field(
        description="How many times the test failed before this test."
    )
    data: Optional[str] = Field(
        None, description="Contains all the result data from the test."
    )


class Result(ResultBase):
    id_result: int = Field(description="ID of the result.")


class ResultsRequest(BaseModel):
    since_id: int = Path(
        description="Specifies the last result ID from which to retrieve test results. Record with the specified ID wont be returned."
    )


class Results(BaseModel):
    results: List[Result] = Field(description="Test results for the specified test.")
