from typing import Optional

from pydantic import BaseModel, Field

from utils import enums


class RunBase(BaseModel):
    id_test: int = Field(description="ID of the test.", alias='fk_tests')
    version: Optional[int] = Field(
        None, description="Version of the test which is running."
    )
    state: enums.RunState = Field(description="Specifies the state of the run.")
    pid: Optional[int] = Field(
        None, description="PID of the new created process that runs the test."
    )
    planned: float = Field(
        description="Time when the instruction to run the test was created."
    )
    started: Optional[float] = Field(
        None, description="Time when the test actually started."
    )
    deadline: Optional[float] = Field(
        None,
        description="Time until which the test must end, later terminated or killed.",
    )
    recovery_attempt: int = Field(
        description="How many times the test failed before this test."
    )


class Run(RunBase):
    id_run: int = Field(description="ID of the run.")
