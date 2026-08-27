from typing import Annotated, Literal, Union

from loguru import logger
from pydantic import BaseModel, Field
from shapely import MultiPolygon, Point, Polygon

from prvosm.models.base import Element
from prvosm.models.node import Node
from prvosm.models.way import Way


class Member(BaseModel):
    """Represents a membership in a relation

    Attributes
    ----------
    type : str
        The type of the element (node, way, or relation)
    ref : int
        The ID of the element
    role : str
        The role of the element in the relation
    """

    type: str
    ref: int
    role: str


class Relation(Element):
    """Represents a relation with a collection of members.

    Together with nodes and ways it represents one of the three main
    OSM element types. As such, it inherits all attributes and methods from [`Element`][prvosm.models.base.Element].

    A relation is effectively a collection of nodes, ways, and relations, where each member has a role within
    the relationship. A membership of a relation is represented by the [`Member`][..Member] class.

    Attributes
    ----------
    type : str
        The OSM element type. Always "relation".
    members : list[Member]
        A list of the members of the relation.

    """

    type: Literal["relation"] = "relation"
    members: list[Member]

    def fetch_full(self) -> "FullRelation":
        """Fetches the relation, but with additional information about member elements.

        This is required for certain operations such as constructing the geometry of the relation.

        Returns
        -------
        FullRelation
            The relation, but with additional information about member elements.
        """
        return self._require_api().fetch_full_relation(self.id)


class FullRelation(Relation):
    """The same as relation, but with additional information about member elements.

    This is required for certain operations such as constructing the geometry of the relation.

    Attributes
    ----------
    elements : list[Node | Way | Relation]
        List of the elements related to this relation, including the relation itself.

    Note
    ----
    In reality this object only contains a list of elements, but to make it
    easier to use, it populates itself with the contents of the relation itself
    (which is always one of the items in the list of elements)
    """

    elements: list[Annotated[Union[Node, Way, Relation], Field(discriminator="type")]]

    def outer_geometry(self) -> MultiPolygon:
        """Tries to construct the outer geometry of the relation

        Assuming that the relation has ways with the role "outer", the function tries
        to construct a MultiPolygon from those ways.
        The function does not assume that the ways are sorted properly.

        Returns
        -------
        MultiPolygon
            A MultiPolygon representing the outer geometry of the relation
        """

        # Find the ways that make up the outer boundary
        outer_ways = [
            member
            for member in self.members
            if member.type == "way" and member.role == "outer"
        ]

        # Create a lookup table for node coordinates
        nodes_coordinates: dict[int, Point] = {
            elm.id: elm.geometry for elm in self.elements if elm.type == "node"
        }

        ways = {elm.id: elm for elm in self.elements if elm.type == "way"}

        from collections import defaultdict

        end_nodes: dict[int, list[int]] = defaultdict(list)
        for way_ref in outer_ways:
            way_id = way_ref.ref
            way = ways[way_id]
            first_node = way.nodes[0]
            last_node = way.nodes[-1]
            end_nodes[first_node].append(way_id)
            end_nodes[last_node].append(way_id)

        for node, connections in end_nodes.items():
            if len(connections) != 2:
                logger.warning(
                    f"Relation {self.id}: Node {node} has {len(connections)} connection(s)s. Since this is not 2 that implies that the boundaries of the relation is broken or incomplete."
                )

        def get_nodes(way_id: int) -> list[int]:
            return ways[way_id].nodes

        def get_polygon() -> Polygon:
            start_node, ways = end_nodes.popitem()

            # Special case if the entire polygon is a single way
            if len(set(ways)) == 1:
                return Polygon(nodes_coordinates[node] for node in get_nodes(ways[0]))

            way1, way2 = ways[0], ways[1]
            way1_ns = get_nodes(way1)
            way2_ns = get_nodes(way2)

            seen_ways = {way1, way2}

            # Make sure that the start node is in the middle
            # logger.debug(f"{start_node!r} - {way1_ns[0]!r} - {way2_ns[0]!r}")
            if way1_ns[0] == start_node:
                way1_ns = way1_ns[::-1]
            if way2_ns[0] != start_node:
                way2_ns = way2_ns[::-1]

            nodes = [*way1_ns, *way2_ns]

            # Walk forward
            while len(end_nodes) and nodes[0] != nodes[-1]:
                new_ways = set(end_nodes.pop(nodes[-1])) - seen_ways
                if len(new_ways) != 1:
                    logger.warning(
                        f"Node {nodes[-1]} resulted in 0 or more than 1 ways {new_ways}"
                    )
                assert len(new_ways) == 1
                new_nodes = get_nodes(*new_ways)
                if nodes[-1] != new_nodes[0]:
                    new_nodes = list(reversed(new_nodes))
                nodes.extend(new_nodes)
                seen_ways |= new_ways

            if nodes[0] in end_nodes:
                end_nodes.pop(nodes[0])

            if nodes[-1] in end_nodes:
                end_nodes.pop(nodes[-1])

            if not nodes[0] == nodes[-1]:
                logger.warning(
                    f"Failed to create a loop (Started at n:{nodes[0]}, Ended at n:{nodes[-1]})",
                )

            return Polygon(nodes_coordinates[node] for node in nodes)

        polygons: list[Polygon] = []
        while len(end_nodes):
            polygons.append(get_polygon())

        return MultiPolygon(polygons)
