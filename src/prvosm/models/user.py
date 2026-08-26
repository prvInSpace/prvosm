from datetime import datetime

from pydantic import BaseModel, HttpUrl

from prvosm.models.base import Bindable


class SocialLink(BaseModel):
    url: HttpUrl
    platform: str | None


class Image(BaseModel):
    href: HttpUrl


class Count(BaseModel):
    count: int


class CountWithActive(Count):
    active: int


class ContributorTerms(BaseModel):
    agreed: bool


class Blocks(BaseModel):
    received: CountWithActive
    issued: CountWithActive | None = None


class User(BaseModel, Bindable):
    id: int
    display_name: str
    account_created: datetime
    description: str
    social_links: list[SocialLink]
    roles: list[str]
    contributor_terms: ContributorTerms
    company: str | None = None
    img: Image | None = None
    changesets: Count
    traces: Count
    blocks: Blocks
