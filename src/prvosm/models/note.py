from datetime import datetime, timezone
from typing import Annotated

from pydantic import (
    BaseModel,
    BeforeValidator,
    HttpUrl,
)
from shapely import Point

from prvosm.models.base import Bindable
from prvosm.models.user import User


def parse_custom_datetime(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S UTC").replace(
        tzinfo=timezone.utc
    )


class Comment(BaseModel, Bindable):
    """Represents a comment on a note

    User details may be missing if the note was submitted anonymously.

    Attributes
    ----------
    date : datetime
        The date and time the comment was created.
    uid: int | None
        The ID of the user that submitted the comment (if present).
    user: str | None
        The display name of the user that submitted the comment (if present).
    user_url: HttpUrl | None
        A URL to the user's page (if present).
    action: str
        The action the user took (opened, closed, commented, etc.) when commenting.
    text: str
        The text of the comment.
    html: str
        The HTML form of the comment.
    """

    date: Annotated[datetime, BeforeValidator(parse_custom_datetime)]
    uid: int | None = None
    user: str | None = None
    user_url: HttpUrl | None = None
    action: str
    text: str
    html: str

    @property
    def is_anonymous(self) -> bool:
        """Whether the comment was submitted anonimously or not"""
        return self.user is None

    def fetch_user(self) -> User | None:
        """Fetches the user that made the comment

        Returns
        -------
        User | None
            User if the the user information is available, otherwise None
        """
        if not self.uid:
            return None
        self._require_api().fetch_user(self.uid)


class Note(BaseModel, Bindable):
    """Represents a note on the map

    Attributes
    ----------
    id : int
        The ID of the note.
    lon : float
        The longitude of the note in degrees.
    lat : float
        The latitude of the note in degrees.
    url : HttpUrl
        The URL of the note.
    comment_url : HttpUrl | None
        The URL end-point of the API to make a comment.
    close_url : HttpUrl
        The URL end-point of the API to close a note.
    date_created : datetime
        The date and time that the note was created.
    comments : list[Comment]
        A list with all the comments on the note.
    """

    id: int
    lon: float
    lat: float
    url: HttpUrl
    comment_url: HttpUrl | None = None
    close_url: HttpUrl | None = None
    date_created: Annotated[datetime, BeforeValidator(parse_custom_datetime)]
    comments: list[Comment]

    @property
    def geometry(self) -> Point:
        """The geometry of the note

        Returns
        -------
        Point
            A point representing the longitude and latitude of the note.
        """
        return Point(self.lon, self.lat)

    @property
    def is_anonymous(self) -> bool:
        return self.comments[0].is_anonymous
