from pydantic import Field

from alphaxiv.models.common import ExternalModel
from alphaxiv.models.common import StrictModel


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
