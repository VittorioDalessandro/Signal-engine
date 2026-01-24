import requests
from datetime import datetime, timezone
from typing import List, Dict, Any

def fetch_market_news(category: str = "general", limit: int = 10, token: str = "") -> List[Dict[str, Any]]:
    """
    News di mercato (general, forex, crypto, merger, ...):
    https://finnhub.io/docs/api/market-news
    """
    if not token:
        raise ValueError("FINNHUB_API_KEY missing")

    url = "https://finnhub.io/api/v1/news"
    params = {"category": category, "token": token}

    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json() or []

    out = []
    for item in data[: max(0, int(limit))]:
        ts = item.get("datetime")
        dt_iso = None
        if ts:
            dt_iso = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()

        out.append({
            "headline": item.get("headline"),
            "source": item.get("source"),
            "datetime": dt_iso,
            "url": item.get("url"),
            "summary": item.get("summary"),
            "category": item.get("category"),
        })

    return out
