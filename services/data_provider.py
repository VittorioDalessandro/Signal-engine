import requests
from datetime import datetime, timezone

def fetch_ohlc_finnhub(ticker: str, resolution: str = "D", count: int = 200, token: str = ""):
    """
    Ritorna una lista di candele OHLCV in formato:
    [{"t":..., "o":..., "h":..., "l":..., "c":..., "v":...}, ...]
    resolution: "D" (giornaliero) oppure "W" (settimanale)
    count: numero di barre (approssimato convertendo in range temporale)
    """
    if not token:
        raise ValueError("FINNHUB_API_KEY missing")

    now = datetime.now(timezone.utc)
    to_ts = int(now.timestamp())

    # Finnhub /stock/candle usa from/to (non 'count'), quindi stimiamo una finestra temporale
    if resolution == "D":
        from_ts = to_ts - int(count) * 86400
    elif resolution == "W":
        from_ts = to_ts - int(count) * 7 * 86400
    else:
        # fallback: trattalo come giorni
        from_ts = to_ts - int(count) * 86400

    url = "https://finnhub.io/api/v1/stock/candle"
    params = {
        "symbol": ticker.upper(),
        "resolution": resolution,
        "from": from_ts,
        "to": to_ts,
        "token": token,
    }

    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()

    if data.get("s") != "ok":
        raise ValueError(f"Finnhub error: {data}")

    candles = []
    t = data["t"]
    o = data["o"]
    h = data["h"]
    l = data["l"]
    c = data["c"]
    v = data.get("v", [None] * len(t))

    for i in range(len(t)):
        candles.append({"t": t[i], "o": o[i], "h": h[i], "l": l[i], "c": c[i], "v": v[i]})

    return candles
