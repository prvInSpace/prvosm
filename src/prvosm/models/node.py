from typing import TYPE_CHECKING, Literal

from shapely import Point

from prvosm.models.base import Element

if TYPE_CHECKING:
    from prvosm.models.relation import Relation
    from prvosm.models.way import Way


class Node(Element):
    """Represents a single node with a latiude and longitude. May form part of a way or relation"""

    type: Literal["node"]
    lat: float
    lon: float

    @property
    def geometry(self) -> Point:
        return Point(self.lon, self.lat)

    def fetch_history(
        self,
    ) -> list["Node"]:
        return self._require_api().fetch_node_history(self.id)

    def fetch_version(self, version: int) -> "Node":
        return self._require_api().fetch_node_version(self.id, version)

    def fetch_relations(self) -> list[Relation]:
        return self._require_api().fetch_relations_for_node(self.id)

    def fetch_ways(self) -> list[Way]:
        return self._require_api().fetch_ways_for_node(self.id)
