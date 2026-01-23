import os
import requests

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")

def fetch_ohlc_finnhub(ticker: str, resolution: str = "D", count: int = 200):
    """
    Ritorna una lista di candele OHLCV in formato:
    [{"t":..., "o":..., "h":..., "l":..., "c":..., "v":...}, ...]
    resolution: "D" (giornaliero) oppure "W" (settimanale)
    count: numero di barre (es. 60 breve, 260 lungo)
    """
    if not FINNHUB_API_KEY:
        raise ValueError("FINNHUB_API_KEY missing")

    url = "https://finnhub.io/api/v1/stock/candle"
    params = {
        "symbol": ticker.upper(),
        "resolution": resolution,
        "count": int(count),
        "token": FINNHUB_API_KEY,
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
