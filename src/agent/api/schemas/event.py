from typing import List

from pydantic import BaseModel, Field


class EventBase(BaseModel):
    run_at: float = Field(description="Time when the event should be executed.")
    source: str = Field(
        description="What's the source of the event - what cased that the event was planned."
    )
    recovery_attempt: int = Field(
        description="How many times the test failed before this test."
    )


class EventCreate(EventBase):
    pass


class Event(EventBase):
    id_event: int = Field(description="ID of the event.")
    id_test: int = Field(description="ID of the test.", alias='fk_tests')


class Events(BaseModel):
    events: List[Event] = Field(description="List of planned events.")
