from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, PrivateAttr

if TYPE_CHECKING:
    from prvosm.api.base import OSMClient
    from prvosm.models.changeset import Changeset
    from prvosm.models.user import User


class Bindable:
    _api: OSMClient | None = PrivateAttr(default=None)

    def _require_api(self) -> OSMClient:
        if self._api is None:
            raise RuntimeError("This object is not associated with an OSM client")
        return self._api


class Element(BaseModel, Bindable):
    """Represents the base of the main OSM elements, and contains all the fields that are common
    to nodes, ways, and relations.

    Attributes
    ----------
    id : int
        The ID of the element
    version : int
        The version of the element
    timestamp : datetime
        The date and time this version of the element was created (UTC)
    changeset : int
        The ID of the changeset that made this version of the element
    user : str | None
        The display name of the user that made this version of the element. Might be missing on older elements.
    uid : int | None
        The ID of the user that made this version of the element. Might be missing on older elements.

    tags : dict[str, str]
        Dictionary of string to strings representing the tags attached to the element.

    See Also
    --------
     - [`Node`][prvosm.models.node.Node]:
        One of the base element types, representing a single point
     - [`Way`][prvosm.models.way.Way]:
        One of the base element types, represeting a collection of nodes
    - [`Relation`][prvosm.models.relation.Relation]
        One of the base element type, representing a collection of nodes, ways, and relations
    """

    id: int
    version: int
    timestamp: datetime
    changeset: int
    user: str | None = None
    uid: int | None = None
    tags: dict[str, str] = Field(default_factory=dict)

    def fetch_changeset(self) -> Changeset:
        """Fetches the changeset related to this element

        Returns
        -------
        Changeset
            The changeset that made this version of the object
        """
        return self._require_api().fetch_changeset(self.changeset)

    def fetch_user(self) -> User:
        """Fetches the user related to this element

        Returns
        -------
        User
            The user that made this version of the object
        """
        if self.uid is None:
            raise ValueError("Element has no attached user")
        return self._require_api().fetch_user(self.uid)
