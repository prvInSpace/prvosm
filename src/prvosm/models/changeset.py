from datetime import datetime

from pydantic import BaseModel, Field
from shapely import Polygon, box

from prvosm.models.base import Bindable
from prvosm.models.osmchange import OsmChange
from prvosm.models.user import User


class Changeset(BaseModel, Bindable):
    """Represents a single changeset

    Attributes
    ----------
    id : int
        The ID of the changeset.
    created_at : datetime
        The date and time the changeset was created (opened)(UTC).
    open : bool
        Whether the changeset is open.
    comments_count : int
        The number of comments on the changeset.
    changes_count : int
        The number of changes made by the changeset.
    created_count : int
        The number of elements created by the changeset.
    modified_count : int
        The number of elements modified by the changeset
    closed_at : datetime
        The date and time the changeset was closed
    min_lat: float
        The minimum latitude of the changeset in degrees.
    min_lon: float
        The minimum longitude of the changeset in degrees.
    max_lat : float
        The maximum latitude of the changeset in degrees.
    max_lon : float
        The maximum longitude of the changeset in degrees.
    uid : int
        The ID of the user that made the changeset
    user : str
        The display name of the user that made the changeset
    tags : dict[str, str]
        A dictionary of tags on the changeset
    """

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
        """Fetches the user that made the changeset

        Returns
        -------
        User
            The user that made the changeset
        """
        return self._require_api().fetch_user(self.uid)

    def fetch_changes(self) -> OsmChange:
        """Fetches the changes made by the changeset.

        Returns
        -------
        OsmChange
            An object with all the changes made by the changeset.
        """
        return self._require_api().fetch_changeset_changes(self.id)

    @property
    def bbox(self) -> Polygon:
        """Contstructs a polygon represeting the BBox of the changeset.

        Returns
        -------
        Polygon
            The BBox (minimal bounding box) of the changeset.
        """
        return box(self.min_lon, self.min_lat, self.max_lon, self.max_lat)
