from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from .config import enabled_content_sources, instruments_from_config, load_config
from .content import fetch_content_items
from .market import fetch_yahoo_points
from .report import compose_report
from .storage import Store


def main() -> None:
    parser = argparse.ArgumentParser(description="DailyFinNews pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest = subparsers.add_parser("ingest", help="Fetch market and content data")
    ingest.add_argument("--config", default="config/sources.yaml")
    ingest.add_argument("--db", default="data/dailyfinnews.sqlite")
    ingest.add_argument("--skip-market", action="store_true")
    ingest.add_argument("--skip-content", action="store_true")

    report = subparsers.add_parser("report", help="Compose a markdown report")
    report.add_argument("--config", default="config/sources.yaml")
    report.add_argument("--db", default="data/dailyfinnews.sqlite")
    report.add_argument("--out", default="reports/latest.md")

    args = parser.parse_args()
    if args.command == "ingest":
        run_ingest(args.config, args.db, args.skip_market, args.skip_content)
    elif args.command == "report":
        run_report(args.config, args.db, args.out)


def run_ingest(config_path: str, db_path: str, skip_market: bool, skip_content: bool) -> None:
    config = load_config(config_path)
    store = Store(db_path)
    try:
        if not skip_market:
            points = fetch_yahoo_points(instruments_from_config(config))
            store.upsert_market_points(points)
            print(f"stored {len(points)} market points")
        if not skip_content:
            items = fetch_content_items(enabled_content_sources(config))
            store.insert_content_items(items)
            print(f"stored {len(items)} content items")
    finally:
        store.close()


def run_report(config_path: str, db_path: str, out_path: str) -> None:
    load_config(config_path)
    store = Store(db_path)
    try:
        report = compose_report(
            store.latest_market_points(),
            store.recent_content_items(),
            generated_at=datetime.now(timezone.utc),
        )
    finally:
        store.close()
    output = Path(out_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(f"wrote {output}")


if __name__ == "__main__":
    main()

