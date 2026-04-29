from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import requests

from .models import ContentItem


def fetch_content_items(sources: list[dict[str, Any]], timeout: int = 15) -> list[ContentItem]:
    items: list[ContentItem] = []
    for source in sources:
        source_type = source.get("type")
        if source_type == "rss":
            items.extend(fetch_rss_source(source))
        elif source_type == "reddit":
            items.extend(fetch_reddit_source(source, timeout=timeout))
    return dedupe_by_title(items)


def fetch_rss_source(source: dict[str, Any]) -> list[ContentItem]:
    import feedparser

    feed = feedparser.parse(source["url"])
    return [
        ContentItem(
            source=source["name"],
            timestamp=parse_entry_timestamp(entry),
            region=source["region"],
            asset_class=source["asset_class"],
            title=(entry.get("title") or "").strip(),
            body=(entry.get("summary") or "").strip(),
            url=(entry.get("link") or source["url"]).strip(),
            language=source.get("language", "en"),
            source_type="rss",
            weight=float(source.get("weight", 1.0)),
        )
        for entry in feed.entries
        if entry.get("title")
    ]


def fetch_reddit_source(source: dict[str, Any], timeout: int = 15) -> list[ContentItem]:
    response = requests.get(
        source["url"],
        headers={"User-Agent": "DailyFinNews/0.1"},
        timeout=timeout,
    )
    response.raise_for_status()
    children = response.json().get("data", {}).get("children", [])
    items: list[ContentItem] = []
    for child in children:
        data = child.get("data", {})
        title = (data.get("title") or "").strip()
        if not title:
            continue
        created_utc = data.get("created_utc")
        timestamp = (
            datetime.fromtimestamp(created_utc, timezone.utc)
            if created_utc
            else datetime.now(timezone.utc)
        )
        permalink = data.get("permalink") or ""
        items.append(
            ContentItem(
                source=source["name"],
                timestamp=timestamp,
                region=source["region"],
                asset_class=source["asset_class"],
                title=title,
                body=(data.get("selftext") or "").strip(),
                url=f"https://www.reddit.com{permalink}" if permalink else source["url"],
                language=source.get("language", "en"),
                source_type="reddit",
                weight=float(source.get("weight", 1.0)),
            )
        )
    return items


def dedupe_by_title(items: list[ContentItem]) -> list[ContentItem]:
    seen: set[str] = set()
    unique: list[ContentItem] = []
    for item in sorted(items, key=lambda value: value.weight, reverse=True):
        key = normalize_title(item.title)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def normalize_title(title: str) -> str:
    return " ".join(
        token.strip(".,:;!?()[]{}\"'").lower()
        for token in title.split()
        if len(token.strip(".,:;!?()[]{}\"'")) > 2
    )


def parse_entry_timestamp(entry: Any) -> datetime:
    for key in ("published", "updated", "created"):
        value = entry.get(key)
        if value:
            parsed = parsedate_to_datetime(value)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
    return datetime.now(timezone.utc)
