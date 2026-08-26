from datetime import datetime

from pydantic import BaseModel, Field

from prvosm.models.base import Bindable
from prvosm.models.user import User


class Changeset(BaseModel, Bindable):
    id: int
    created_at: datetime
    open: bool
    comments_count: int
    changes_count: int
    created_count: int
    modified_count: int
    closed_at: datetime
    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float
    uid: int
    user: str
    tags: dict[str, str] = Field(default_factory=dict)

    def fetch_user(self) -> User:
        return self._require_api().fetch_user(self.uid)
