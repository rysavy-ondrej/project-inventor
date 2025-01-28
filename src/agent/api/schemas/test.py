from typing import List, Optional

from pydantic import BaseModel, Field

from api.schemas.event import Event
from api.schemas.old_params import OldParams
from api.schemas.request import Request
from api.schemas.result import Result
from api.schemas.run import Run
from utils import enums


class TestBase(BaseModel):
    description: str = Field(description="Description of the test defined by the user.")
    state: enums.TestState = Field(description="State of the test.")
    test_params: str = Field(
        description="Parameters of the test that specifies how the test should be executed."
    )
    timeout: int = Field(
        description="Specifies in what time the test must finish, otherwise it will be terminated."
    )
    scheduling_interval: Optional[int] = Field(
        description="Interval in which the test should be scheduled, or None if the test is only one-time run."
    )
    scheduling_from: Optional[float] = Field(
        description="Time from when the test should be scheduled to execute."
    )
    scheduling_until: Optional[float] = Field(
        description="Time until when the test should be scheduled to execute."
    )
    recovery_interval: int = Field(
        description="Interval in which the recovery test should be scheduled."
    )
    recovery_attempt_limit: Optional[int] = Field(
        description="How many time the recovery test should be executed. Zero means no recovery test, None means infinite tests."
    )


class TestUpdate(TestBase):

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "description": "description",
                    "state": "disabled",
                    "test_params": "{}",
                    "timeout": 60,
                    "scheduling_interval": 60,
                    "scheduling_from": 1,
                    "scheduling_until": 123456,
                    "recovery_interval": 30,
                    "recovery_attempt_limit": 3,
                }
            ]
        }
    }


class TestCreate(TestBase):
    name: str = Field(description="Name of the test.")
    version: int = Field(description="The actual version of the test.")
    key_ro: str = Field(
        description="Authorization key used to identify the orchestrator that can read the data about the test."
    )
    key_rw: str = Field(
        description="Authorization key used to identify the orchestrator that can change the test parameters."
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "ping.1",
                    "version": 1,
                    "description": "description",
                    "state": "disabled",
                    "test_params": "{}",
                    "timeout": 60,
                    "scheduling_interval": 60,
                    "scheduling_from": 1,
                    "scheduling_until": 123456,
                    "recovery_interval": 30,
                    "recovery_attempt_limit": 3,
                    "key_ro": "random_value_1",
                    "key_rw": "random_value_2",
                }
            ]
        }
    }


class Test(TestCreate):
    id_test: int = Field(description="ID of the test.")
    last_started_time: Optional[float] = Field(
        None, description="Time when the last test was executed."
    )
    last_result_time: Optional[float] = Field(
        None, description="Time when the last execution of the test was finished."
    )
    last_result_status: Optional[enums.ResultStatus] = Field(
        description="Result from the last test execution."
    )
    last_downloaded_time: Optional[float] = Field(
        None,
        description="Time when the results for the test were last downloaded. This includes request when there are no results available.",
    )


class Tests(BaseModel):
    tests: List[Test] = Field(description="List of tests.")


class TestFullInfo(BaseModel):
    test: Test = Field(description="Test record.")
    requests: List[Request] = Field(
        description="Request records for the specified test."
    )
    events: List[Event] = Field(description="Event records for the specified test.")
    runs: List[Run] = Field(description="Run records for the specified test.")
    old_params: List[OldParams] = Field(
        description="Old parameters records for the specified test."
    )
    results: List[Result] = Field(description="Result records for the specified test.")
