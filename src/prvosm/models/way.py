from typing import Annotated, Literal, Union

from pydantic import Field
from shapely import LineString, Point

from prvosm.models.base import Element
from prvosm.models.node import Node


class Way(Element):
    """Represents a single way (series of nodes) in the OSM database

    A way may be closed (i.e a building, loop, etc.) or open (road).
    To construct the full geometry, a full way is required (see `fetch_full`)
    """

    type: Literal["way"] = "way"
    nodes: list[int]

    @property
    def is_closed(self) -> bool:
        """Helper property to check if a way is closed or not

        This can also be determined by fetching the full way, construction the geometry,
        and checking the is_closed property on the geometry
        """
        return self.nodes[0] == self.nodes[-1]

    def fetch_full(self) -> "FullWay":
        """Fetches the full version of the way with additional information about child nodes

        Required for certain features such as geometry.
        """
        return self._require_api().fetch_full_way(self.id)


class FullWay(Way):
    """
    Represents a way with additional information about child nodes.

    This function is useful since it the additional information about nodes is
    required to generate the geometry of the way.

    Notes
    ----
    In reality this object only contains a list of elements, but to make it
    easier to use, it populates itself with the contents of the relation itself
    (which is always one of the items in the list of elements)
    """

    # This will always be a list of nodes + the way itself
    elements: list[Annotated[Union[Node, Way], Field(discriminator="type")]]

    @property
    def geometry(self) -> LineString:
        """Constructs the geometry of the way"""
        node_geometries = {
            node.id: Point(node.lon, node.lat)
            for node in self.elements
            if node.type == "node"
        }
        return LineString([node_geometries[node] for node in self.nodes])
