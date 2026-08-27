from typing import TYPE_CHECKING, Literal

from shapely import Point

from prvosm.models.base import Element

if TYPE_CHECKING:
    from prvosm.models.relation import Relation
    from prvosm.models.way import Way


class Node(Element):
    """Represents a single node with a latiude and longitude.

    A node is one of the main OSM element types alongside ways and relations,
    and as such inhertits all the attributes from [`Element`][prvosm.models.base.Element].
    A node may form part of a way or relation, be a standalone POI, or both.

    Attributes
    ----------
    type : str
        The OSM element type. Always "node".
    lat : float
        The latitude in degrees.
    lon : float
        The longitude in degrees.
    """

    type: Literal["node"]
    lat: float
    lon: float

    @property
    def geometry(self) -> Point:
        """Constructs a shapely point for the node

        Returns
        -------
        Point
            A point with the longitude and latitude of the object
        """
        return Point(self.lon, self.lat)

    def fetch_history(
        self,
    ) -> list["Node"]:
        """Fetches a list of all of the version of the node

        Returns
        -------
        list[Node]
            A list containing all the versions of the node
        """
        return self._require_api().fetch_node_history(self.id)

    def fetch_version(self, version: int) -> "Node":
        """Fetches a specific version of the node

        Returns
        -------
        Node
            The version of the node requested
        """
        return self._require_api().fetch_node_version(self.id, version)

    def fetch_relations(self) -> list["Relation"]:
        """Fetches the relations that the node is a member of

        Returns
        -------
        list[Relation]
            A list of the relations the node is a member of if any
        """
        return self._require_api().fetch_relations_for_node(self.id)

    def fetch_ways(self) -> list["Way"]:
        """Fetches the ways that the node is a member of

        Returns
        -------
        list[Way]
            A list of the ways the node is a member of if any
        """
        return self._require_api().fetch_ways_for_node(self.id)
