from typing import List

from pydantic import BaseModel, Field


class OrchestratorBase(BaseModel):
    name: str = Field(description="Human readable orchestrator name.")
    last_seen: float = Field(
        description="The last time when the orchestrator has either authenticated or used any endpoint."
    )


class Orchestrator(OrchestratorBase):
    id_orchestrator: int = Field(description="ID of the orchestrator.")


class Orchestrators(BaseModel):
    orchestrators: List[Orchestrator]
