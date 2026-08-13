from pydantic import Field

from alphaxiv.models.common import ExternalModel


class Researcher(ExternalModel):
    slug: str
    name: str
    affiliation: str | None = None
    headline: str | None = None
    bio: str | None = None
    photo_url: str | None = Field(default=None, alias="photoUrl")
    citations: int | None = None
    h_index: int | None = Field(default=None, alias="hIndex")
    research_areas: list[str] = Field(default_factory=list, alias="researchAreas")


class ResearchersResponse(ExternalModel):
    researchers: list[Researcher]
    next_offset: int | None = Field(default=None, alias="nextOffset", ge=0)
