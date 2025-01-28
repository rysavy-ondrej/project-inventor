from pydantic import BaseModel, Field


class Time(BaseModel):
    time: float = Field(description="Current time on the agent.")
