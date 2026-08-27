from datetime import datetime

from pydantic import BaseModel, HttpUrl

from prvosm.models.base import Bindable


class SocialLink(BaseModel):
    """A link to a social account.

    Attributes
    ----------
    url : HttpUrl
        The URL to the social account.
    platform : str | None
        The name or description of the platform, if present.
    """

    url: HttpUrl
    platform: str | None


class Image(BaseModel):
    """A link to an image

    Attributes
    ----------
    href : HttpUrl
        The URL to the image
    """

    href: HttpUrl


class Count(BaseModel):
    """A wrapper object for a count

    Attributes
    ----------
    count : int
        The count
    """

    count: int


class CountWithActive(BaseModel):
    """A wrapper object for a count with how many are active

    Attributes
    ----------
    count : int
        The count
    count : int
        The number that are active
    """

    count: int
    active: int


class ContributorTerms(BaseModel):
    """Information about whether the user has agreed to the
    [Contributor Terms](https://osmfoundation.org/wiki/Licence/Contributor_Terms) or not.

    Attributes
    ----------
    agreed : bool
        Boolean flag represeting whether the user agreed to the
        [Contributor Terms](https://osmfoundation.org/wiki/Licence/Contributor_Terms) or not.
    """

    agreed: bool


class Blocks(BaseModel):
    """Information about the number of blocks that has been
    received or issues by a user.

    Attributes
    ----------
    received : CountWithActive
        The number of blocks the user has been received, including how
        many are still active.
    issues : CountWithActive
        The number of blocks the user has issues, including how
        many are still active.
    """

    received: CountWithActive
    issued: CountWithActive | None = None


class User(BaseModel, Bindable):
    """Represents an OSM user

    Attributes
    ----------
    id : int
        The ID of the user.
    display_name : str
        The current display name of the user.
    account_created : datetime
        The date and time the user was created.
    description : str
        The description set by the user.
    social_links : list[SocialLink]
        A list of social links, if any.
    roles : list[str]
        A list of roles that the user has, if any.
    contributor_terms : ContributorTerms
        An object with details about whether the user has accepted the [Contributor Terms](https://osmfoundation.org/wiki/Licence/Contributor_Terms)
    company : str | None = None
        The company the user works for, if any.
    img : Image | None = None
        The profile picture of the user, if any.
    changesets : Count
        The number of changesets made by the user.
    traces : Count
        The number of GPS traces uploaded by the user.
    blocks : Blocks
        Details about the number of blocks that has been sent and received by the user and whether they are still active,
    """

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
