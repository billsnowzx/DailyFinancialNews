from datetime import datetime, timezone

from dailyfinnews.content import dedupe_by_title
from dailyfinnews.models import ContentItem


def item(title: str, weight: float) -> ContentItem:
    return ContentItem(
        source="source",
        timestamp=datetime.now(timezone.utc),
        region="Global",
        asset_class="macro",
        title=title,
        body="",
        url=f"https://example.com/{weight}",
        language="en",
        source_type="rss",
        weight=weight,
    )


def test_dedupe_by_title_keeps_highest_weight() -> None:
    items = dedupe_by_title([item("Fed signals patience", 0.5), item("Fed signals patience", 1.0)])

    assert len(items) == 1
    assert items[0].weight == 1.0

