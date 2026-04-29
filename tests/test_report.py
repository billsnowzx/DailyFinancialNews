from datetime import datetime, timezone

from dailyfinnews.report import compose_report
from dailyfinnews.storage import Store
from dailyfinnews.models import ContentItem, MarketPoint


def test_compose_report_contains_required_sections() -> None:
    store = Store(":memory:")
    store.upsert_market_points(
        [
            MarketPoint(
                symbol="BTC-USD",
                name="BTC",
                asset_class="crypto",
                region="Global",
                timestamp=datetime.now(timezone.utc),
                level=100000,
                change_pct=2.0,
            )
        ]
    )
    store.insert_content_items(
        [
            ContentItem(
                source="Reddit Investing",
                timestamp=datetime.now(timezone.utc),
                region="US",
                asset_class="equities",
                title="Investors debate earnings data",
                body="",
                url="https://reddit.com/example",
                language="en",
                source_type="reddit",
                weight=0.5,
            )
        ]
    )

    report = compose_report(
        store.latest_market_points(),
        store.recent_content_items(),
        generated_at=datetime(2026, 4, 29, tzinfo=timezone.utc),
    )

    assert "## TL;DR" in report
    assert "## Cross-Asset Snapshot" in report
    assert "## Social Pulse" in report
    assert "BTC" in report
    store.close()
