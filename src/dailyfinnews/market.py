from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import warnings

import requests

from .models import Instrument, MarketPoint


YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"


def fetch_yahoo_points(instruments: list[Instrument], timeout: int = 15) -> list[MarketPoint]:
    points: list[MarketPoint] = []
    for instrument in instruments:
        try:
            response = requests.get(
                YAHOO_CHART_URL.format(symbol=instrument.symbol),
                params={"range": "5d", "interval": "1d"},
                headers={"User-Agent": "DailyFinNews/0.1"},
                timeout=timeout,
            )
            response.raise_for_status()
            point = parse_yahoo_chart(instrument, response.json())
            if point is not None:
                points.append(point)
        except Exception as exc:
            warnings.warn(f"Skipping instrument {instrument.symbol}: {exc}")
    return points


def parse_yahoo_chart(instrument: Instrument, payload: dict[str, Any]) -> MarketPoint | None:
    result = payload.get("chart", {}).get("result") or []
    if not result:
        return None

    chart = result[0]
    timestamps = chart.get("timestamp") or []
    quote = (chart.get("indicators", {}).get("quote") or [{}])[0]
    closes = quote.get("close") or []
    clean = [(ts, close) for ts, close in zip(timestamps, closes) if close is not None]
    if not clean:
        return None

    timestamp, latest = clean[-1]
    previous = clean[-2][1] if len(clean) > 1 else None
    change_pct = ((latest - previous) / previous * 100) if previous else None
    return MarketPoint(
        symbol=instrument.symbol,
        name=instrument.name,
        asset_class=instrument.asset_class,
        region=instrument.region,
        timestamp=datetime.fromtimestamp(timestamp, timezone.utc),
        level=float(latest),
        change_pct=change_pct,
    )
