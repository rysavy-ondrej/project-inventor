from typing import Dict

from pydantic import BaseModel, Field

from api.schemas.result import Results


class MultiResult(BaseModel):
    results: Dict[int, Results] = Field(
        description="Test results for the specified test."
    )
    last_checked_id: int = Field(description="ID of the test.")


class MultiResultCreate(BaseModel):
    key: str = Field(
        description="Authorization key used to download results from multiple tests at once."
    )


class MultiResultId(BaseModel):
    id_multi_result: int = Field(description="ID of the multi result.")


class MultiResultTestsIds(BaseModel):
    test_ids: str = Field(description="List of test IDs related to the multi result.")


class MultiResultAddTestInput(BaseModel):
    id_test: int = Field(description="ID of the test.", alias='fk_tests')
    hash: str = Field(description="Hash calculated from the multi results key.")
