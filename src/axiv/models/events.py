from pydantic import Field

from axiv.models.common import ExternalModel
from axiv.models.common import StrictModel


class Event(ExternalModel):
    id: str
    title: str
    link: str
    date: str
    speaker: str | None = None
    organization: str
    recording: str | None = None


class EventsResponse(StrictModel):
    items: list[Event]
    count: int = Field(ge=0)
