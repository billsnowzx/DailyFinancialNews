from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Instrument:
    symbol: str
    name: str
    asset_class: str
    region: str


@dataclass(frozen=True)
class MarketPoint:
    symbol: str
    name: str
    asset_class: str
    region: str
    timestamp: datetime
    level: float
    change_pct: float | None


@dataclass(frozen=True)
class ContentItem:
    source: str
    timestamp: datetime
    region: str
    asset_class: str
    title: str
    body: str
    url: str
    language: str
    source_type: str
    weight: float

