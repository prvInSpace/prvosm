# Preben OSM's Library (prvosm)
![PyPI - Version](https://img.shields.io/pypi/v/prvosm)
![License](https://img.shields.io/github/license/prvInSpace/prvosm)
[![Release CI](https://github.com/prvInSpace/prvosm/actions/workflows/release.yml/badge.svg)](https://github.com/prvInSpace/prvosm/actions/workflows/release.yml)
[![Documentation CI](https://github.com/prvInSpace/prvosm/actions/workflows/docs.yml/badge.svg)](https://github.com/prvInSpace/prvosm/actions/workflows/docs.yml)

A simple Python library that makes accessing data from the OSM API dead easy and convenient.

## Features
- **Read-only OSM API access:** I never really use Python to write anything to OSM, so a simple read-only API is all that I need, hence all that this library provides at the moment.
- **Object/type oriented:**
  Instead of dealing with a bunch of nested dictionaries, everything is properly parsed into an object using [Pydantic](https://pydantic.dev/docs/validation/latest/get-started/). Want to fetch the details for the user that made a changeset? Call `changeset.fetch_user()` and a `User` object is returned.
- **Easy geometries:** OSM elements (nodes, ways, relations, notes) have functions and properties to get [shapely](https://shapely.readthedocs.io/en/stable/manual.html) geometries.
- **Cached:** Following good practice, objects and responses are stored in a sqlite cache.
- **Almost all read end-points added:** There are a handful that I haven't got around to implementing, but most are implemented.

## Documentation

For documentation, roadmaps, etc. see [prvinspace.github.io/prvosm/](https://prvinspace.github.io/prvosm/).

## Maintainer

This library is maintained by [Preben Vangberg](https://www.openstreetmap.org/user/Preben%20Vangberg). You can pop me a message on OSM, Discord or Matrix if there is anything.