from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from sqlite3 import Row


ASSET_CLASSES = ["equities", "rates", "fx", "commodities", "crypto", "macro"]


def compose_report(market_rows: list[Row], content_rows: list[Row], generated_at: datetime) -> str:
    lines: list[str] = [
        "# Daily Cross-Asset Report",
        "",
        f"Generated: {generated_at.isoformat(timespec='minutes')}",
        "",
        "## TL;DR",
        "",
    ]
    lines.extend(tldr_lines(market_rows, content_rows))
    lines.extend(["", "## Cross-Asset Snapshot", ""])
    lines.extend(snapshot_table(market_rows))
    lines.extend(["", "## By Asset Class", ""])
    lines.extend(asset_class_sections(market_rows, content_rows))
    lines.extend(["", "## Narrative Drivers", ""])
    lines.extend(driver_sections(content_rows))
    lines.extend(["", "## Major Financial Press", ""])
    lines.extend(newspaper_digest(content_rows))
    lines.extend(["", "## Social Pulse", ""])
    lines.extend(social_pulse(content_rows))
    lines.extend(["", "## Day Ahead", ""])
    lines.extend(day_ahead(content_rows))
    lines.append("")
    return "\n".join(lines)


def tldr_lines(market_rows: list[Row], content_rows: list[Row]) -> list[str]:
    biggest = sorted(
        [row for row in market_rows if row["change_pct"] is not None],
        key=lambda row: abs(row["change_pct"]),
        reverse=True,
    )[:3]
    headlines = content_rows[:2]
    bullets = [
        f"- {row['name']} moved {row['change_pct']:+.2f}% to {row['level']:.2f}."
        for row in biggest
    ]
    bullets.extend(f"- {row['source']}: {row['title']}" for row in headlines)
    while len(bullets) < 5:
        bullets.append("- Insufficient fresh evidence for a fuller read.")
    return bullets[:5]


def snapshot_table(market_rows: list[Row]) -> list[str]:
    rows = ["| Asset | Region | Level | Change |", "| --- | --- | ---: | ---: |"]
    for row in market_rows:
        change = "n/a" if row["change_pct"] is None else f"{row['change_pct']:+.2f}%"
        rows.append(f"| {row['name']} | {row['region']} | {row['level']:.2f} | {change} |")
    if len(rows) == 2:
        rows.append("| No market data available | n/a | n/a | n/a |")
    return rows


def asset_class_sections(market_rows: list[Row], content_rows: list[Row]) -> list[str]:
    lines: list[str] = []
    market_by_asset = group_rows(market_rows, "asset_class")
    content_by_asset = group_rows(content_rows, "asset_class")
    for asset_class in ASSET_CLASSES:
        if asset_class not in market_by_asset and asset_class not in content_by_asset:
            continue
        lines.append(f"### {asset_class.title()}")
        moves = market_by_asset.get(asset_class, [])
        if moves:
            top_move = sorted(
                [row for row in moves if row["change_pct"] is not None],
                key=lambda row: abs(row["change_pct"]),
                reverse=True,
            )
            if top_move:
                row = top_move[0]
                lines.append(
                    f"{row['name']} was the largest configured move at {row['change_pct']:+.2f}%."
                )
        for row in content_by_asset.get(asset_class, [])[:3]:
            lines.append(f"{row['source']} reported: [{row['title']}]({row['url']}).")
        if not moves and not content_by_asset.get(asset_class):
            lines.append("Insufficient fresh evidence.")
        lines.append("")
    return lines


def driver_sections(content_rows: list[Row]) -> list[str]:
    rows = sorted(content_rows, key=lambda row: row["weight"], reverse=True)[:4]
    if not rows:
        return ["- No narrative drivers available from current ingestion."]
    return [
        f"- **{row['title']}**: sourced from {row['source']} ({row['region']}, {row['asset_class']}). [Link]({row['url']})"
        for row in rows
    ]


def newspaper_digest(content_rows: list[Row]) -> list[str]:
    rows = [row for row in content_rows if row["source_type"] == "newspaper_rss"]
    if not rows:
        return [
            "- No major financial newspaper items were ingested. Check paywall/RSS access before treating this as a quiet-news signal."
        ]

    lines: list[str] = []
    for source, source_rows in sorted(group_rows(rows, "source").items()):
        lines.append(f"### {source}")
        for row in sorted(source_rows, key=lambda value: value["timestamp"], reverse=True)[:3]:
            summary = summarize_text(row["body"]) if row["body"] else "No excerpt available from the feed."
            lines.append(f"- [{row['title']}]({row['url']}) — {summary}")
        lines.append("")
    return lines


def summarize_text(text: str, max_words: int = 32) -> str:
    clean = " ".join(text.replace("\n", " ").split())
    words = clean.split()
    if len(words) <= max_words:
        return clean
    return " ".join(words[:max_words]).rstrip(".,;:") + "..."


def social_pulse(content_rows: list[Row]) -> list[str]:
    social = [row for row in content_rows if row["source_type"] in {"reddit", "x_list", "xiaohongshu"}]
    if not social:
        return ["- No enabled social sources produced fresh items. Treat this as missing sentiment, not a neutral signal."]
    return [
        f"- Sentiment proxy from {row['source']}: [{row['title']}]({row['url']})"
        for row in social[:5]
    ]


def day_ahead(content_rows: list[Row]) -> list[str]:
    event_terms = ("auction", "earnings", "speaker", "data", "calendar", "rate decision")
    matches = [
        row for row in content_rows if any(term in row["title"].lower() for term in event_terms)
    ]
    if not matches:
        return ["- No day-ahead calendar items found in enabled sources. Add a calendar feed for production."]
    return [f"- {row['source']}: [{row['title']}]({row['url']})" for row in matches[:6]]


def group_rows(rows: list[Row], key: str) -> dict[str, list[Row]]:
    grouped: dict[str, list[Row]] = defaultdict(list)
    for row in rows:
        grouped[row[key]].append(row)
    return grouped
