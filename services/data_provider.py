import os
import requests
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

def fetch_ohlc_finnhub(
    ticker: str,
    timeframe: str = "1D",
    candles: int = 200,
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Ritorna una lista di candele OHLCV in formato:
    [{"t":..., "o":..., "h":..., "l":..., "c":..., "v":...}, ...]
    timeframe: "1D" (giornaliero) oppure "1W" (settimanale)
    candles: numero di barre richieste (approx)
    """

    key = api_key or os.getenv("FINNHUB_API_KEY", "")
    if not key:
        raise ValueError("FINNHUB_API_KEY missing")

    tf = timeframe.upper().strip()
    if tf in ("1D", "D"):
        resolution = "D"
        # ci mettiamo margine per weekend/festivi
        days_back = max(30, int(candles * 2))
        delta = timedelta(days=days_back)
    elif tf in ("1W", "W"):
        resolution = "W"
        weeks_back = max(52, int(candles))
        delta = timedelta(weeks=weeks_back)
    else:
        raise ValueError("timeframe must be 1D or 1W")

    now = datetime.now(timezone.utc)
    frm = int((now - delta).timestamp())
    to = int(now.timestamp())

    url = "https://finnhub.io/api/v1/stock/candle"
    params = {
        "symbol": ticker.upper().strip(),
        "resolution": resolution,
        "from": frm,
        "to": to,
        "token": key,
    }

    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()

    if data.get("s") != "ok":
        raise ValueError(f"Finnhub error: {data}")

    candles_out = []
    t = data["t"]
    o = data["o"]
    h = data["h"]
    l = data["l"]
    c = data["c"]
    v = data.get("v", [None] * len(t))

    for i in range(len(t)):
        candles_out.append({"t": t[i], "o": o[i], "h": h[i], "l": l[i], "c": c[i], "v": v[i]})

    # se vuoi “tagliare” circa al numero richiesto (opzionale)
    if len(candles_out) > candles:
        candles_out = candles_out[-candles:]

    return candles_out
