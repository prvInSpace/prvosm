import json
import re
from importlib.metadata import version
from pathlib import Path
from typing import Optional, Sequence

import requests
from loguru import logger
from pydantic import BaseModel
from shapely.geometry.base import BaseGeometry

from prvosm.api.base import OSMClient
from prvosm.cache import SqliteCache
from prvosm.models.base import Bindable
from prvosm.models.changeset import Changeset
from prvosm.models.node import Node
from prvosm.models.note import Note
from prvosm.models.osmchange import OsmChange, XmlOsmChange
from prvosm.models.relation import FullRelation, Relation
from prvosm.models.user import User
from prvosm.models.way import FullWay, Way

DEFAULT_CACHE_LOCATION = Path(__file__).parent / "__cache__" / "osm_cache.db"


class OSMApi(OSMClient):
    """
    An implementation of the OSMClient protocol that accesses the main OSM API
    for data.

    Responses are cached in most cases using the SqliteCache object. A handful of
    functions are not (mainly searching). Refer to individual functions for more details

    Attributes
    ----------
    app_name : str
        Required argument. The OSM API requires a proper user-agent. The app
        name is used with the format `{app_name} (prvosm {version})` if
        user-agent is not passed directly to the initialiser
    base_api_url : str
        The base of the API (without the final slash). This can be the main
        OSM API (default) or a mirror with the same end-points.
    cache : SqliteCache
        The cache for the responses from the API.
    user_agent : str
        The user-agent sent to the API. Used to override the default `app_name`
        based user-agent.
    """

    def __init__(
        self,
        app_name: str,
        base_api_url: str = "https://api.openstreetmap.org/api/0.6",
        cache: SqliteCache = SqliteCache(DEFAULT_CACHE_LOCATION),
        user_agent: Optional[str] = None,
    ) -> None:
        self.base_api_url = base_api_url.removesuffix("/")
        self.headers = {
            "User-Agent": (
                user_agent
                if user_agent
                else f"{app_name.strip()} (prvosm {version('prvosm')})"
            ),
        }
        self.cache = cache

    def _bind_api[T](self, obj: T) -> T:
        if isinstance(obj, Bindable):
            obj._api = self
        return obj

    def _fetch_from_cache_or_api(
        self, object_id: str, endpoint: str, params: dict | None = None
    ) -> str:
        # Check for outdated object_ids
        if ".json" in object_id:
            raise ValueError(object_id)

        # check cache first
        if cache_response := self.cache.get_cached(object_id):
            return cache_response

        url = f"{self.base_api_url}{endpoint}"
        logger.info(f"Fetching data from {url}")
        resp = requests.get(url, headers=self.headers, params=params)
        resp.raise_for_status()

        return resp.text

    def _fetch_single_element(self, object_id: str, end_point: str) -> dict:
        if cached := self.cache.get_cached(object_id):
            data = json.loads(cached)
        else:
            resp = self._fetch_from_cache_or_api(object_id, end_point)
            data = json.loads(resp)["elements"][0]
            self.cache.set_cached(object_id, json.dumps(data))
        return data

    def _fetch_multiple_elements(self, object_id: str, end_point: str) -> dict:
        if cached := self.cache.get_cached(object_id):
            data = json.loads(cached)
        else:
            resp = self._fetch_from_cache_or_api(object_id, end_point)
            data = json.loads(resp)["elements"]
            self.cache.set_cached(object_id, json.dumps(data))
        return data

    def _multi_fetch_elements[T: BaseModel](
        self,
        cls: type[T],
        element_type: str,
        ids: Sequence[str | int],
    ) -> list[T]:
        """Helper function for the multi-fetch end-points /nodes, /ways, and /relations"""
        processed_ids = _check_list_of_ids(ids)
        required_ids_to_object_id = {}

        # This part could be made slightly better in that we could also check
        # if we got a history cached
        elements = []
        for id in processed_ids:
            if "v" not in id:
                object_id = f"{element_type[0]}_{id}"
            else:
                id_part, version_part = id.split("v")
                object_id = f"{element_type[0]}_{id_part}_v{version_part}"

            if cached := self.cache.get_cached(object_id):
                elements.append(cls.model_validate_json(cached))
            else:
                required_ids_to_object_id[id] = object_id

        # then we have to make the actual network call to get the data, but
        # we also need to store
        if required_ids_to_object_id:
            url = f"{self.base_api_url}/{element_type}].json"
            logger.info(
                f"Fetching {len(required_ids_to_object_id)} element(s) from {url}"
            )
            resp = requests.get(
                url,
                headers=self.headers,
                params={element_type: ",".join(required_ids_to_object_id.keys())},
            )
            resp.raise_for_status()

            # Process each one and cache them
            for element in resp.json()["elements"]:
                with_version = f"{element['id']}v{element['version']}"
                required_id = (
                    with_version
                    if with_version in required_ids_to_object_id
                    else str(element["id"])
                )
                object_id = required_ids_to_object_id[required_id]
                self.cache.set_cached(object_id, json.dumps(element))
                elements.append(cls.model_validate(element))

        return [self._bind_api(e) for e in elements]

    ## ------------------- Changeset related functions ------------------------------

    def fetch_changeset(self, id: int) -> Changeset:
        """Fetches data about a specific changeset.

        Parameters
        ----------
        id : int
            The ID of the changeset to fetch.

        Returns
        -------
        Changeset
            Data about the requested changeset.
        """
        object_id = f"c_{id}"
        if cached := self.cache.get_cached(object_id):
            data = json.loads(cached)
        else:
            resp = self._fetch_from_cache_or_api(
                object_id,
                f"/changeset/{id}.json",
                params={"include_discussion": "true"},
            )
            data = json.loads(resp)["changeset"]
            self.cache.set_cached(object_id, json.dumps(data))
        return self._bind_api(Changeset.model_validate(data))

    def fetch_changeset_changes(self, id: int) -> OsmChange:
        """Fetches the changes made by a changeset.

        This is returned in the osmChamge XML format, however, it is converted
        to a regular type internally and returned.

        Parameters
        ----------
        id : int
            The ID of the changeset to fetch the changes for.

        Returns
        -------
        OsmChange
            An object containing information about the elements that was changed,
            modified, or created by the specified changeset.
        """
        object_id, end_point = f"c_{id}_changes", f"/changeset/{id}/download"
        data = self.cache.get_cached(object_id)
        if not data:
            url = f"{self.base_api_url}{end_point}"
            logger.info(f"Fetching data from {url}")
            resp = requests.get(url, headers=self.headers)
            resp.raise_for_status()
            data = resp.text
            self.cache.set_cached(object_id, data)

        xml_data = XmlOsmChange.from_xml(bytes(data, encoding="utf-8"))
        return xml_data.to_base_type()

    def fetch_changeset_comments(self) -> None:
        raise NotImplementedError

    ## ------------------- Node related functions ------------------------------

    def fetch_node(self, id: int) -> Node:
        """Fetches a single node from the API.

        Parameters
        ----------
        id : int
            The ID of the node to fetch.

        Returns
        -------
        Node
            A Node object containing information about the requested node.
        """
        object_id, end_point = f"n_{id}", f"/node/{id}.json"
        data = self._fetch_single_element(object_id, end_point)
        return self._bind_api(Node.model_validate(data))

    def fetch_nodes(self, ids: Sequence[str | int]) -> list[Node]:
        """Fetches data for multiple nodes at once.

        Both IDs and IDs with version specifiers are allowed.

        If a node already exists in cache, the node with be read from there
        rather than fetched from the API. All nodes requested are cached.

        Parameters
        ----------
        ids : list[int | str]
            The list of the nodes to fetch. Can either be the pure integer ID
            of a node, or with an additional version specifier at the end
            (e.g. `1234` or `1234v5`).

        Returns
        -------
        list[Node]
            A list of containing the nodes that were requested.
        """
        return self._multi_fetch_elements(Node, "nodes", ids)

    def fetch_node_history(self, id: int) -> list[Node]:
        """Fetches a every version of a node from the API.

        Parameters
        ----------
        id : int
            The ID of the node to fetch the history for.

        Returns
        -------
        list[Node]
            A list of all the versions of the specified node.
        """
        object_id, end_point = f"n_{id}_history", f"/node/{id}/history.json"
        data = self._fetch_multiple_elements(object_id, end_point)
        return [self._bind_api(Node.model_validate(obj)) for obj in data]

    def fetch_node_version(self, id: int, version: int) -> Node:
        """Fetches a single version of a node from the API.

        Parameters
        ----------
        id : int
            The ID of the node to fetch
        version : int
            The version of the node to fetch

        Returns
        -------
        Node
            The version of the node that was requested.
        """
        object_id, end_point = f"n_{id}_v{version}", f"/node/{id}/{int}.json"
        data = self._fetch_single_element(object_id, end_point)
        return self._bind_api(Node.model_validate(data))

    def fetch_ways_for_node(self, id: int) -> list[Way]:
        """Fetches all the ways that a node is part of.

        Parameters
        ----------
        id : int
            The ID of the node.

        Returns
        -------
        list[Way]
            A list of the ways the node is part of, if any.
        """
        object_id, end_point = f"n_{id}_ways", f"/node/{id}/ways.json"
        data = self._fetch_multiple_elements(object_id, end_point)
        return [self._bind_api(Way.model_validate(obj)) for obj in data]

    def fetch_relations_for_node(self, id: int) -> list[Relation]:
        """Fetches all the relations that a node is part of.

        Parameters
        ----------
        id : int
            The ID of the node.

        Returns
        -------
        list[Relation]
            A list of the relations the node is part of, if any.
        """
        object_id, end_point = f"n_{id}_relations", f"/node/{id}/relations.json"
        data = self._fetch_multiple_elements(object_id, end_point)
        return [self._bind_api(Relation.model_validate(obj)) for obj in data]

    ## ------------------- Note related functions ------------------------------

    def fetch_note(self, id: int) -> Note:
        """Fetches details about a specific note

        Parameters
        ----------
        id : int
            The ID of the note.

        Returns
        -------
        Note
            The requested note.
        """

        data = self._fetch_from_cache_or_api(f"note_{id}", f"/notes/{id}.json")
        feature = json.loads(data)["features"][0]
        note_data = feature["properties"]
        note_data["lon"], note_data["lat"] = feature["geometry"]["coordinates"]
        return Note.model_validate(note_data)

    def fetch_notes(
        self, bbox: BaseGeometry, limit: int | None = None, closed: int | None = None
    ) -> list[Note]:
        """Fetches notes from inside side bbox.

        Results from this function are never cached.

        Parameters
        ----------
        bbox : BaseGeometry
            Required argument. Used to define the bounds of the elements. Note
            that the minimum and maximum longitude and latitude of the element is
            used, not its outer bounds, so notes outide the boundaries may be returned.
        limit : int, optional
            Maximum number of items to return. If not provided the default for the API
            is used (100 notes).
        closed : int, optional
            The number of days a note can have been closed for before it is excluded from
            the results. Passing 0 makes the function only return open notes. If not provided
            the default for the API is used (7 days).

        Returns
        -------
        list[Note]
            A list with all the notes found capped at the limit.
        """
        params = {"bbox": ",".join([str(coord) for coord in bbox.bounds])}
        if limit is not None:
            params["limit"] = str(limit)
        if closed is not None:
            params["closed"] = str(closed)

        notes_data = requests.get(
            f"{self.base_api_url}/notes.json",
            headers=self.headers,
            params=params,
        ).json()

        notes = []
        for feature in notes_data["features"]:
            note_data = feature["properties"]
            note_data["lon"], note_data["lat"] = feature["geometry"]["coordinates"]
            note = Note.model_validate(note_data)
            self._bind_api(note)
            for comment in note.comments:
                self._bind_api(comment)
            notes.append(note)

        return notes

    ## ------------------- Relations related functions ------------------------------

    def fetch_relation(self, id: int) -> Relation:
        """Fetches data about a specific relation.

        Parameters
        ----------
        id : int
            The ID of the relation.

        Returns
        -------
        Relation
            The relation requested.
        """
        object_id, end_point = f"r_{id}", f"/relation/{id}.json"
        data = self._fetch_single_element(object_id, end_point)
        return self._bind_api(Relation.model_validate(data))

    def fetch_relations(self, ids: Sequence[str | int]) -> list[Relation]:
        """Fetches data for multiple relations at once.

        Both IDs and IDs with version specifiers are allowed.

        If a relation already exists in cache, the relation with be read from there
        rather than fetched from the API. All relations requested are cached.

        Parameters
        ----------
        ids : list[int | str]
            The list of the relations to fetch. Can either be the pure integer ID
            of a relation, or with an additional version specifier at the end
            (e.g. `1234` or `1234v5`).

        Returns
        -------
        list[Relation]
            A list of containing the relations that were requested.
        """
        return self._multi_fetch_elements(Relation, "relations", ids)

    def fetch_relation_history(self, id: int) -> list[Relation]:
        """Fetches all versions of a relation.

        Parameters
        ----------
        id : int
            The relation to request the history for.

        Returns
        -------
        list[Relation]
            A list containing all the versions of the relation.
        """
        object_id, end_point = f"r_{id}_history", f"/relation/{id}/history.json"
        data = self._fetch_multiple_elements(object_id, end_point)
        return [self._bind_api(Relation.model_validate(obj)) for obj in data]

    def fetch_relation_version(self, id: int, version: int) -> Relation:
        """Fetches a specific version of a relation.

        Parameters
        ----------
        id : int
            The ID of the relation.
        version : int
            The version of the relation to fetch.

        Returns
        -------
        Relation
            The version of the relation requested.
        """
        object_id, end_point = f"r_{id}_v{version}", f"/relation/{id}/{version}.json"
        data = self._fetch_single_element(object_id, end_point)
        return self._bind_api(Relation.model_validate(data))

    def fetch_relations_for_relation(self, id: int) -> list[Relation]:
        """Fetches relations that the relation is a member of (parent relations).

        Parameters
        ----------
        id : int
            The ID of the relation to fetch the relations for.

        Returns
        -------
        list[Relation]
            A list with all the parent relations that the relation is a member of, if any.
        """
        object_id, end_point = f"r_{id}_relations", f"/relation/{id}/relations.json"
        data = self._fetch_multiple_elements(object_id, end_point)
        return [self._bind_api(Relation.model_validate(obj)) for obj in data]

    def fetch_full_relation(self, id: int) -> FullRelation:
        """Fetches the relation in addition to information about all the direct members.

        Required for certain features such as geometry.

        Parameters
        ----------
        id : int
            The ID of the relation to fetch.

        Returns
        -------
        FullRelation
            The relation with additional information about direct members.
        """
        object_id, end_point = f"r_{id}_full", f"/relation/{id}/full.json"
        data = self._fetch_multiple_elements(object_id, end_point)
        main_rel = [e for e in data if e["id"] == id][0]
        main_rel["elements"] = data
        return self._bind_api(FullRelation.model_validate(main_rel))

    ## ------------------- User related functions ------------------------------

    def fetch_user(self, id: int) -> User:
        """Fetches details for a specific user

        Parameters
        ----------
        id : int
            The ID of the user to fetch

        Returns
        -------
        User
            A user object containing information about the user
        """
        object_id, end_point = f"u_{id}", f"/user/{id}.json"
        if cached := self.cache.get_cached(object_id):
            data = json.loads(cached)
        else:
            resp = self._fetch_from_cache_or_api(object_id, end_point)
            data = json.loads(resp)["user"]
            self.cache.set_cached(object_id, json.dumps(data))
        return self._bind_api(User.model_validate(data))

    ## ------------------- Way related functions -------------------------------

    def fetch_way(self, id: int) -> Way:
        """Fetches information about a way.

        Parameters
        ----------
        id : int
            The ID of the way to fetch.

        Returns
        -------
        Way
            Object containing information about the requested way.
        """
        object_id, end_point = f"w_{id}", f"/way/{id}.json"
        data = self._fetch_single_element(object_id, end_point)
        return self._bind_api(Way.model_validate(data))

    def fetch_ways(self, ids: Sequence[str | int]) -> list[Way]:
        """Fetches data for multiple ways at once.

        Both IDs and IDs with version specifiers are allowed.

        If a way already exists in cache, the way with be read from there
        rather than fetched from the API. All ways requested are cached.

        Parameters
        ----------
        ids : list[int | str]
            The list of the ways to fetch. Can either be the pure integer ID
            of a way, or with an additional version specifier at the end
            (e.g. `1234` or `1234v5`).

        Returns
        -------
        list[Way]
            A list of containing the ways that were requested.
        """
        return self._multi_fetch_elements(Way, "ways", ids)

    def fetch_way_history(self, id: int) -> list[Way]:
        """Fetches all the version of a way.

        Parameters
        ----------
        id : int
            The ID of the Way to fetch all the versions for.

        Returns
        -------
        list[Way]
            A list containing all the versions of the requested way.
        """
        object_id, end_point = f"w_{id}_history", f"/way/{id}/history.json"
        data = self._fetch_multiple_elements(object_id, end_point)
        return [self._bind_api(Way.model_validate(obj)) for obj in data]

    def fetch_way_version(self, id: int, version: int) -> Way:
        """Fetch a specific version of a way.

        Parameters
        ----------
        id : int
            The ID of the way to fetch.
        version : int
            The version of the way to fetch.

        Returns
        -------
        Way
            The version of the way that was requested.
        """
        object_id, end_point = f"w_{id}_v{version}", f"/way/{id}/{version}.json"
        data = self._fetch_single_element(object_id, end_point)
        return self._bind_api(Way.model_validate(data))

    def fetch_relations_for_way(self, id: int) -> list[Relation]:
        """Fetch relations that the way is a part of.

        Parameters
        ----------
        id : int
            The ID of the way to fetch the relations for.

        Returns
        -------
        list[Relation]
            A list of all of the relations the way is a member of, if any.
        """
        object_id, end_point = f"w_{id}_relations", f"/way/{id}/relations.json"
        data = self._fetch_multiple_elements(object_id, end_point)
        return [self._bind_api(Relation.model_validate(obj)) for obj in data]

    def fetch_full_way(self, id: int) -> FullWay:
        """Fetches the way in addition to information about all the nodes.

        Required for certain features such as geometry.

        Parameters
        ----------
        id : int
            The ID of the way to fetch.

        Returns
        -------
        FullWay
            The way with additional information about nodes.
        """
        object_id, end_point = f"w_{id}_full", f"/way/{id}/full.json"
        data = self._fetch_multiple_elements(object_id, end_point)
        main_way = [e for e in data["elements"] if e["id"] == id][0]
        main_way["elements"] = data["elements"]
        return self._bind_api(FullWay.model_validate(main_way))


def _check_list_of_ids(ids: Sequence[int | str]) -> list[str]:
    stringified = [str(id) for id in ids]
    for id in stringified:
        if not _is_valid_id_version_string(id):
            raise ValueError(
                f"ID {id} is not in a valid format (id or id + 'v' + version)"
            )
    return stringified


def _is_valid_id_version_string(id: str) -> bool:
    pattern = re.compile("[1-9[0-9]*(v[1-9][0-9]*)?")
    return pattern.fullmatch(id) is not None
