# Getting started

Prvosm is made it be incredibly straight forward to set up. To get started, first install the library using your favourite package manager:

=== "pip"

    ```bash
    pip install prvosm
    ```

=== "uv"

    ```bash
    uv add prvosm
    ```

=== "Poetry"

    ```bash
    poetry add prvosm
    ```

## The API object

The initial starting point is the [`OSMApi`][prvosm.OSMApi] class. This class implements most of the read functions from the main [OpenStreetMap API](https://wiki.openstreetmap.org/wiki/API_v0.6). To create the object initialise it with a name:

```python
from prvosm import OSMApi
api = OSMApi("my-app")
```
??? question "Why do I have to add a name?"

    The reason why a name is required is that the API wants a user-agent to be set in the request. The name is used to create a user-agent in the format `{app_name} (prvosm {prvosm.version})`. You can override the user-agent by passing a custom user-agent in the constructor.

## Example usages

Now that you have the object, what can you do with it? Well, most things! Let's go through some examples!

### Fetching a single POI / Node
Let's say you want to check out your favourite mountain. If you find the ID of it on OSM, and use the [`fetch_node`][prvosm.OSMApi.fetch_node] method on the API object we just constructed:

```python
from prvosm import OSMApi
api = OSMApi("my-app")
favourite_mountain = api.fetch_node(14118602506)
```

??? example "Model dump"

    **Python:**
    ```python
    favourite_mountain.model_dump_json(indent=4)
    ```
    **Model content:**
    ```json
    {
        "id": 14118602506,
        "version": 1,
        "timestamp": "2026-08-24T08:52:12Z",
        "changeset": 187926199,
        "user": "Preben Vangberg",
        "uid": 24239154,
        "tags": {
            "ele": "126.8",
            "name": "Litlefjellet",
            "natural": "peak"
        },
        "type": "node",
        "lat": 60.7327097,
        "lon": 5.1940282
    }
    ```


The [`fetch_node`][prvosm.OSMApi.fetch_node] method returns a [`Node`](prvosm.models.node.Node) object with information about the node and some handy helper methods.
I wonder who changed it last? Well, let find out! While most objects will have a user (and uid) attached to it, this is not always the case for older objects. Let's check if the user added other objects while they were at it!

### Fetching a changeset

If we want to fetch a changeset directly from the api, we can do so by calling the [`fetch_changeset`][prvosm.OSMApi.fetch_changeset] method. However, since we already have a [`Node`](prvosm.models.node.Node) we can call the `fetch_changeset` method directly on the object:

```python
changeset = favourite_mountain.fetch_changeset()
```

??? example "Model dump"

    **Python:**
    ```python
    changeset.model_dump_json(indent=4)
    ```
    **Model content:**
    ```json
    {
        "id": 187926199,
        "created_at": "2026-08-24T08:52:12Z",
        "open": false,
        "comments_count": 0,
        "changes_count": 2,
        "created_count": 2,
        "modified_count": 0,
        "closed_at": "2026-08-24T08:52:13Z",
        "min_lat": 60.7327097,
        "min_lon": 5.1493423,
        "max_lat": 60.7598805,
        "max_lon": 5.1940282,
        "uid": 24239154,
        "user": "Preben Vangberg",
        "tags": {
            "changesets_count": "928",
            "comment": "Added two small peaks",
            "created_by": "iD 2.42.2",
            "host": "https://www.openstreetmap.org/edit",
            "imagery_used": "Kartverket topo",
            "locale": "en-GB",
            "source": "local knowledge;Kartverket topo"
        }
    }
    ```

According to the created count (`changeset.created_count`) and the comment, the user created another peak.

### Fetching a user

Same as before, if we want to fetch details about a user, we could use the [`OSMApi`][prvosm.OSMApi] object directly, but since we have the changeset we might as well use that. For completeness's sake, the main function is [`fetch_user`][prvosm.OSMApi.fetch_user]. To fetch the user of a changeset, you can use:

```python
user = changeset.fetch_user()
```

??? example "Model dump"

    **Python:**
    ```python
    user.model_dump_json(indent=4)
    ```
    **Model content:**
    ```json
    {
        "id": 24239154,
        "display_name": "Preben Vangberg",
        "account_created": "2026-06-22T11:18:41Z",
        "description": "...",
        "social_links": [
            {
                "url": "https://toot.wales/@prvinspace",
                "platform": null
            }
        ],
        "roles": [],
        "contributor_terms": {
            "agreed": true
        },
        "company": "PhD Student, Bangor University",
        "img": {
            "href": "https://www.openstreetmap.org/rails/active_storage/representations/redirect/eyJfcmFpbHMiOnsiZGF0YSI6MzcwOTU4NjIsInB1ciI6ImJsb2JfaWQifX0=--3589c481ad01e2286d8ae9931176c958e42e6a09/eyJfcmFpbHMiOnsiZGF0YSI6eyJmb3JtYXQiOiJqcGVnIiwicmVzaXplX3RvX2xpbWl0IjpbMTAwLDEwMF19LCJwdXIiOiJ2YXJpYXRpb24ifX0=--e2e4a75d9b9ef79144147b4e6db38afad5a755ec/1665950020372.jpeg"
        },
        "changesets": {
            "count": 942
        },
        "traces": {
            "count": 4
        },
        "blocks": {
            "received": {
                "count": 0,
                "active": 0
            },
            "issued": null
        }
    }
    ```


### Final words

The go-to documentation to see what the library can do is the [`OSMApi`][prvosm.OSMApi] class. Almost all other features are built around it or are simple helper functions around that class.


??? Info "Random fun fact"

    For what it is worth, Litlefjellet is not my favourite mountain, but it is my dog's favourite. He loves running around the meadows when there are not grazing animals there. My favourite mountain is probably Tryfan.