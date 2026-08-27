from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_xml import BaseXmlModel, attr, element

from prvosm.models.node import Node
from prvosm.models.relation import Relation
from prvosm.models.way import Way


class OsmChange(BaseModel):
    """Represents the changes made by a specific changeset

    Attributes
    ----------
    created : list[Node | Way | Relation]
        List of all of the elements created by the changeset
    modified : list[Node | Way | Relation]
        List of all of the elements modified by the changeset
    deleted : list[Node | Way | Relation]
        List of all of the elements deleted by the changeset

    Notes
    -----
    The osmChange format is only available in XML, so this object first parses
    that XML document and then returns a cleaned up version that is based
    on the normal Pydantic BaseModel. All XML types used in the initial parsing
    are effectively duplicates of those found elsewhere.
    """

    created: list[Node | Way | Relation] = Field(default_factory=list)
    modified: list[Node | Way | Relation] = Field(default_factory=list)
    deleted: list[Node | Way | Relation] = Field(default_factory=list)


class XmlTag(BaseXmlModel, tag="tag"):
    k: str = attr()
    v: str = attr()


class XmlNodeReference(BaseXmlModel, tag="nd"):
    ref: int = attr()


class XmlMember(BaseXmlModel, tag="member"):
    type: str = attr()
    ref: int = attr()
    role: str = attr()


class BaseXmlElement[T](BaseXmlModel):
    id: int = attr()
    visible: bool = attr()
    version: int = attr()
    changeset: int = attr()
    timestamp: datetime = attr()
    user: str = attr()
    uid: int = attr()

    def to_base_type(self) -> T: ...


class XmlNode(BaseXmlElement[Node], tag="node"):
    lat: float = attr()
    lon: float = attr()
    tags: list[XmlTag] = element(tag="tag", default_factory=list)

    def to_base_type(self) -> Node:
        return Node.model_validate(
            {
                **self.model_dump(),
                "type": "node",
                "tags": {t.k: t.v for t in self.tags},
            }
        )


class XmlWay(BaseXmlElement[Way], tag="way"):
    nodes: list[XmlNodeReference] = element()
    tags: list[XmlTag] = element(tag="tag", default_factory=list)

    def to_base_type(self) -> Way:
        return Way.model_validate(
            {
                **self.model_dump(),
                "type": "way",
                "nodes": [nd.ref for nd in self.nodes],
                "tags": {t.k: t.v for t in self.tags},
            }
        )


class XmlRelation(BaseXmlElement[Relation], tag="relation"):
    members: list[XmlMember] = element()
    tags: list[XmlTag] = element(tag="tag", default_factory=list)

    def to_base_type(self) -> Relation:
        return Relation.model_validate(
            {
                **self.model_dump(),
                "type": "relation",
                "members": [m.model_dump() for m in self.members],
                "tags": {t.k: t.v for t in self.tags},
            }
        )


class XmlChange(BaseXmlModel):
    element: XmlNode | XmlWay | XmlRelation = element()


class XmlOsmChange(BaseXmlModel, tag="osmChange"):
    version: str = attr()
    generator: Optional[str] = attr(default=None)
    copyright: Optional[str] = attr(default=None)
    attribution: Optional[str] = attr(default=None)
    license: Optional[str] = attr(default=None)

    created: list[XmlChange] = element(tag="create", default_factory=list)
    modified: list[XmlChange] = element(tag="modify", default_factory=list)
    deleted: list[XmlChange] = element(tag="delete", default_factory=list)

    def to_base_type(self) -> OsmChange:
        return OsmChange.model_validate(
            {
                "created": [c.element.to_base_type() for c in self.created],
                "modified": [c.element.to_base_type() for c in self.modified],
                "deleted": [c.element.to_base_type() for c in self.deleted],
            }
        )
