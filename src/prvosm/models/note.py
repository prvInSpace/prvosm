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

    User details may be missing if the note was submitted anonymously
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
        return self.user is None

    def fetch_user(self) -> User | None:
        if not self.uid:
            return None
        self._require_api().fetch_user(self.uid)


class Note(BaseModel, Bindable):
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
        return Point(self.lon, self.lat)

    @property
    def is_anonymous(self) -> bool:
        return self.comments[0].is_anonymous
