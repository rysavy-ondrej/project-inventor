from typing import List
from pydantic import BaseModel, Field


class OldParamsBase(BaseModel):
    id_test: int = Field(description="ID of the test.", alias='fk_tests')
    version: int = Field(description="Version of the test.")
    changed: float = Field(description="Timestamp when the test was changed.")
    test_params: str = Field(
        description="Parameters of the test for the specified version."
    )


class OldParams(OldParamsBase):
    id_old_params: int = Field(description="ID of the old parameter record.")


class OldParamsList(BaseModel):
    old_params: List[OldParams] = Field(description="List of old test parameters.")
