from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import ContentItem, MarketPoint


SCHEMA = """
CREATE TABLE IF NOT EXISTS market_points (
  symbol TEXT NOT NULL,
  name TEXT NOT NULL,
  asset_class TEXT NOT NULL,
  region TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  level REAL NOT NULL,
  change_pct REAL,
  PRIMARY KEY (symbol, timestamp)
);

CREATE TABLE IF NOT EXISTS content_items (
  source TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  region TEXT NOT NULL,
  asset_class TEXT NOT NULL,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  url TEXT NOT NULL,
  language TEXT NOT NULL,
  source_type TEXT NOT NULL,
  weight REAL NOT NULL,
  title_key TEXT NOT NULL,
  PRIMARY KEY (source, url, title_key)
);
"""


class Store:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        if str(path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(path))
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)

    def close(self) -> None:
        self.connection.close()

    def upsert_market_points(self, points: list[MarketPoint]) -> None:
        self.connection.executemany(
            """
            INSERT OR REPLACE INTO market_points
            (symbol, name, asset_class, region, timestamp, level, change_pct)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    point.symbol,
                    point.name,
                    point.asset_class,
                    point.region,
                    point.timestamp.isoformat(),
                    point.level,
                    point.change_pct,
                )
                for point in points
            ],
        )
        self.connection.commit()

    def insert_content_items(self, items: list[ContentItem]) -> None:
        self.connection.executemany(
            """
            INSERT OR IGNORE INTO content_items
            (source, timestamp, region, asset_class, title, body, url, language, source_type, weight, title_key)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    item.source,
                    item.timestamp.isoformat(),
                    item.region,
                    item.asset_class,
                    item.title,
                    item.body,
                    item.url,
                    item.language,
                    item.source_type,
                    item.weight,
                    title_key(item.title),
                )
                for item in items
            ],
        )
        self.connection.commit()

    def latest_market_points(self) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
            SELECT mp.*
            FROM market_points mp
            JOIN (
              SELECT symbol, MAX(timestamp) AS latest_timestamp
              FROM market_points
              GROUP BY symbol
            ) latest
            ON latest.symbol = mp.symbol AND latest.latest_timestamp = mp.timestamp
            ORDER BY asset_class, name
            """
        ).fetchall()

    def recent_content_items(self, limit: int = 80) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
            SELECT *
            FROM content_items
            ORDER BY timestamp DESC, weight DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()


def title_key(title: str) -> str:
    return " ".join(
        token.strip(".,:;!?()[]{}\"'").lower()
        for token in title.split()
        if len(token.strip(".,:;!?()[]{}\"'")) > 2
    )
