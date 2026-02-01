import os
import requests
from datetime import datetime, timezone, date, timedelta
from typing import List, Dict, Any

def fetch_market_news(
    category: str = "general",
    limit: int = 10,
    token: str = ""
) -> List[Dict[str, Any]]:
    """
    News di mercato (general, forex, crypto, merger, ...):
    https://finnhub.io/docs/api/market-news
    """
    token = token or os.getenv("FINNHUB_API_KEY", "").strip()
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
        dt_iso = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts else None

        out.append({
            "headline": item.get("headline"),
            "source": item.get("source"),
            "datetime": dt_iso,
            "url": item.get("url"),
            "summary": item.get("summary"),
            "category": item.get("category"),
        })

    return out


def fetch_company_news(
    ticker: str,
    days_back: int = 7,
    limit: int = 10,
    token: str = ""
) -> List[Dict[str, Any]]:
    """
    News specifiche di una società (ticker), ultimi N giorni:
    https://finnhub.io/docs/api/company-news
    """
    token = token or os.getenv("FINNHUB_API_KEY", "").strip()
    if not token:
        raise ValueError("FINNHUB_API_KEY missing")

    ticker = ticker.upper().strip()

    to_d = date.today()
    from_d = to_d - timedelta(days=int(days_back))

    url = "https://finnhub.io/api/v1/company-news"
    params = {
        "symbol": ticker,
        "from": from_d.isoformat(),
        "to": to_d.isoformat(),
        "token": token,
    }

    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json() or []

    # ordina più recenti prima
    data = sorted(data, key=lambda x: x.get("datetime", 0), reverse=True)

    out = []
    for item in data[: max(0, int(limit))]:
        ts = item.get("datetime")
        dt_iso = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts else None

        out.append({
            "headline": item.get("headline"),
            "source": item.get("source"),
            "datetime": dt_iso,
            "url": item.get("url"),
            "summary": item.get("summary"),
            "category": item.get("category"),
        })

    return out
