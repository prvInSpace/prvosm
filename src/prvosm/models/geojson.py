from typing import Literal, TypeVar

from pydantic import BaseModel


class Point(BaseModel):
    type: Literal["Point"]
    coordinates: list[float]


T = TypeVar("T", bound=BaseModel)


class Feature[T](BaseModel):
    type: Literal["Feature"]
    geometry: Point
    properties: T
