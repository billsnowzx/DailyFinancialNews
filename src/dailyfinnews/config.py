from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import Instrument


def load_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if "market_data" not in data or "content_sources" not in data:
        raise ValueError("Config must define market_data and content_sources sections.")
    return data


def instruments_from_config(config: dict[str, Any]) -> list[Instrument]:
    return [
        Instrument(
            symbol=item["symbol"],
            name=item["name"],
            asset_class=item["asset_class"],
            region=item["region"],
        )
        for item in config["market_data"].get("instruments", [])
    ]


def enabled_content_sources(config: dict[str, Any]) -> list[dict[str, Any]]:
    return [source for source in config.get("content_sources", []) if source.get("enabled", True)]

