from pydantic import Field

from alphaxiv.models.common import ExternalModel
from alphaxiv.models.common import StrictModel


class PaperSearchResult(ExternalModel):
    paper_id: str = Field(alias="paperId")
    title: str
    link: str | None = None
    snippet: str | None = None


class PaperSearchResults(StrictModel):
    items: list[PaperSearchResult]
    count: int = Field(ge=0)


class FullTextSnippet(ExternalModel):
    page_number: int = Field(alias="pageNumber", ge=1)
    snippet: str


class FullTextSearchResult(ExternalModel):
    paper_id: str = Field(alias="paperId")
    title: str
    abstract: str
    publication_date: str | None = Field(default=None, alias="publicationDate")
    votes: int = 0
    snippets: list[FullTextSnippet] = Field(default_factory=list)


class FullTextSearchResults(StrictModel):
    items: list[FullTextSearchResult]
    count: int = Field(ge=0)


class TopicSuggestions(ExternalModel):
    data: list[str]


class Organization(ExternalModel):
    id: str
    name: str
    slug: str
    image: str | None = None


class OrganizationResults(StrictModel):
    items: list[Organization]
    count: int = Field(ge=0)
