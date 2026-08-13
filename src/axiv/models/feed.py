from enum import StrEnum

from pydantic import Field

from axiv.models.common import ExternalModel
from axiv.models.paper import PaperPreview


class FeedSort(StrEnum):
    HOT = "Hot"
    COMMENTS = "Comments"
    VIEWS = "Views"
    LIKES = "Likes"
    GITHUB = "GitHub"
    RECOMMENDED = "Recommended"
    FOR_YOU = "ForYou"
    RECENT = "Recent"


class FeedInterval(StrEnum):
    THREE_DAYS = "3 Days"
    SEVEN_DAYS = "7 Days"
    THIRTY_DAYS = "30 Days"
    NINETY_DAYS = "90 Days"
    ALL_TIME = "All time"


class FeedResponse(ExternalModel):
    page: int = Field(ge=0)
    papers: list[PaperPreview]


class TopicSubgroup(ExternalModel):
    subtopic: str
    count: int = Field(ge=0)


class TopicGroup(ExternalModel):
    group: str
    count: int = Field(ge=0)
    subtopics: list[TopicSubgroup]


class TopicGroupsResponse(ExternalModel):
    topic_groups: list[TopicGroup] = Field(alias="topicGroups")
