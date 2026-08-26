# Preben OSM's Library (prvosm)

A simple Python library that makes accessing data from the OSM API dead easy and convenient.

## Features
- **Read-only OSM API access:** I never really use Python to write anything to OSM, so a simple read-only API is all that I need, hence all that this library provides at the moment.
- **Object/type oriented:**
  Instead of dealing with a bunch of nested dictionaries, everything is properly parsed into an object using [Pydantic](https://pydantic.dev/docs/validation/latest/get-started/). Want to fetch the details for the user that made a changeset? Call `changeset.fetch_user()` and a `User` object is returned.
- **Easy geometries:** OSM elements (nodes, ways, relations, notes) have functions and properties to get [shapely](https://shapely.readthedocs.io/en/stable/manual.html) geometries.
- **Cached:** Following good practice, objects and responses are stored in a sqlite cache.
- **Almost all read end-points added:** There are a handful that I haven't got around to implementing, but most are implemented.

## Roadmap / Ideas

I got other scripts that I use with this codebase that could be implemented / folded into it. If you have any ideas please let me know!

For the time being, the things I'd like to do:
- Add all the remaining documentation and testing to prepare for a v1.0 release
- Add Github actions to build documentation and push new versions to PyPI
- Add missing helper functions on different objects

Then once that is done some ideas I might have:
- "Historical" API to make fetching and parsing larger histories / PBFs easier (I'm currently using this to analyse changesets)

I also have a bunch of code for fetching data from OS OpenData etc. but I feel that is more suitable for a separate library.

## Maintainer

This library is maintained by [Preben Vangberg](https://www.openstreetmap.org/user/Preben%20Vangberg). You can pop me a message on OSM, Discord or Matrix if there is anything.