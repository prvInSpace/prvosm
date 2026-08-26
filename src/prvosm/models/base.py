from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, PrivateAttr

if TYPE_CHECKING:
    from prvosm.api.base import OSMClient
    from prvosm.models.changeset import Changeset
    from prvosm.models.user import User


class Bindable:
    _api: OSMClient | None = PrivateAttr(default=None)

    def _require_api(self) -> "OSMClient":
        if self._api is None:
            raise RuntimeError("This object is not associated with an OSM client")
        return self._api


class Element(BaseModel, Bindable):
    id: int
    version: int
    timestamp: datetime
    changeset: int
    user: str | None = None
    uid: int | None = None
    tags: dict[str, str] = Field(default_factory=dict)

    def fetch_changeset(self) -> Changeset:
        """Fetches the changeset related to this element"""
        return self._require_api().fetch_changeset(self.id)

    def fetch_user(self) -> User:
        if self.uid is None:
            raise ValueError("Element has no attached user")
        return self._require_api().fetch_user(self.uid)
