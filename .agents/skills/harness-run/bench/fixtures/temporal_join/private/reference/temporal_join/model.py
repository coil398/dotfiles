from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Event:
    side: str
    key: Any
    timestamp: int
    value: Any


@dataclass(frozen=True)
class Match:
    left: Event
    right: Event
    timestamp: int


@dataclass(frozen=True)
class Watermark:
    side: str
    timestamp: int


@dataclass(frozen=True)
class Flush:
    pass
