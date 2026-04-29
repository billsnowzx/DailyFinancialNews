from dailyfinnews.market import parse_yahoo_chart
from dailyfinnews.models import Instrument


def test_parse_yahoo_chart_calculates_change_pct() -> None:
    instrument = Instrument("^GSPC", "S&P 500", "equities", "US")
    payload = {
        "chart": {
            "result": [
                {
                    "timestamp": [1000, 2000],
                    "indicators": {"quote": [{"close": [100.0, 105.0]}]},
                }
            ]
        }
    }

    point = parse_yahoo_chart(instrument, payload)

    assert point is not None
    assert point.level == 105.0
    assert point.change_pct == 5.0

