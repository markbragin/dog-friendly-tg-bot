from dataclasses import dataclass


@dataclass
class Coordinates:
    lat: float
    lon: float


@dataclass
class PlaceInfo:
    id: int | None
    name: str | None
    address: str | None
    loc: Coordinates | None
    photo: bytes | None
    dist: float | None


@dataclass
class Suggestion:
    name: str | None
    address: str | None
    description: str | None
    photo: bytes | None

