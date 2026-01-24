# services/news_provider.py
import os
import requests
from datetime import datetime, timedelta, timezone

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")


def _to_yyyy_mm_dd(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


def fetch_company_news(symbol: str, days_back: int = 7, limit: int = 10):
    """
    News specifiche di una società (es. AAPL).
    """
    if not FINNHUB_API_KEY:
        raise ValueError("Missing FINNHUB_API_KEY env var")

    symbol = symbol.upper().strip()
    now = datetime.now(timezone.utc)
    from_dt = now - timedelta(days=days_back)

    url = "https://finnhub.io/api/v1/company-news"
    params = {
        "symbol": symbol,
        "from": _to_yyyy_mm_dd(from_dt),
        "to": _to_yyyy_mm_dd(now),
        "token": FINNHUB_API_KEY,
    }

    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json() or []

    data = sorted(data, key=lambda x: x.get("datetime", 0), reverse=True)

    out = []
    for item in data[: max(0, limit)]:
        ts = item.get("datetime")  # unix seconds
        dt_iso = None
        if ts:
            dt_iso = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()

        out.append(
            {
                "headline": item.get("headline"),
                "source": item.get("source"),
                "datetime": dt_iso,
                "url": item.get("url"),
                "summary": item.get("summary"),
                "category": item.get("category"),
            }
        )
    return out


def fetch_market_news(category: str = "general", limit: int = 10):
    """
    News di mercato (general, forex, crypto, merger, ...).
    """
    if not FINNHUB_API_KEY:
        raise ValueError("Missing FINNHUB_API_KEY env var")

    url = "https://finnhub.io/api/v1/news"
    params = {"category": category, "token": FINNHUB_API_KEY}

    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json() or []

    out = []
    for item in data[: max(0, limit)]:
        ts = item.get("datetime")
        dt_iso = None
        if ts:
            dt_iso = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()

        out.append(
            {
                "headline": item.get("headline"),
                "source": item.get("source"),
                "datetime": dt_iso,
                "url": item.get("url"),
                "summary": item.get("summary"),
                "category": item.get("category"),
            }
        )
    return out
