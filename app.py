from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from typing import Any, Dict, List

from services.data_provider import fetch_ohlc_finnhub
from services.pattern_stockpattern import run_stock_pattern
from services.news_provider import fetch_market_news

app = FastAPI(title="Signal Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def _normalize_candles(candles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Converte le chiavi Finnhub-style:
      o,h,l,c,v,t  ->  open,high,low,close,volume,time
    così run_stock_pattern (che usa 'close') funziona.
    """
    out: List[Dict[str, Any]] = []
    for c in candles:
        out.append({
            "time": c.get("t") if c.get("t") is not None else c.get("time"),
            "open": c.get("o") if c.get("o") is not None else c.get("open"),
            "high": c.get("h") if c.get("h") is not None else c.get("high"),
            "low":  c.get("l") if c.get("l") is not None else c.get("low"),
            "close": c.get("c") if c.get("c") is not None else c.get("close"),
            "volume": c.get("v") if c.get("v") is not None else c.get("volume"),
        })
    return out

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/analyze")
def analyze(
    ticker: str,
    horizon: str = "short",
    include_news: bool = True,
    news_limit: int = 8,
):
    ticker = ticker.upper().strip()
    horizon = horizon.lower().strip()

    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing FINNHUB_API_KEY")

    if horizon not in ["short", "long"]:
        raise HTTPException(status_code=400, detail="horizon must be short or long")

    # clamp semplice sul limite news (evita valori strani)
    if news_limit < 1:
        news_limit = 1
    if news_limit > 50:
        news_limit = 50

    # short = daily, long = weekly (più stabile)
    if horizon == "short":
        resolution = "D"
        count = 140
    else:
        resolution = "W"
        count = 220

    # prende OHLC
    ohlc_raw = fetch_ohlc_finnhub(
        ticker=ticker,
        resolution=resolution,
        count=count,
        token=api_key,
    )

    if not ohlc_raw or len(ohlc_raw) < 50:
        return {"ticker": ticker, "note": "Not enough data", "candles": len(ohlc_raw) if ohlc_raw else 0}

    # IMPORTANT: normalizzo per il pattern engine
    ohlc = _normalize_candles(ohlc_raw)

    pattern_result = run_stock_pattern(ohlc, horizon=horizon)

    out = {
        "ticker": ticker,
        "horizon": horizon,
        "resolution": resolution,
        "pattern": pattern_result,
    }

    if include_news:
        # per ora news di mercato "general"; poi possiamo farle anche per singolo ticker
        out["news"] = fetch_market_news(
            category="general",
            limit=news_limit,
            token=api_key,
        )

    return out

@app.get("/news")
def news(category: str = "general", limit: int = 10):
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing FINNHUB_API_KEY")

    if limit < 1:
        limit = 1
    if limit > 50:
        limit = 50

    return {
        "category": category,
        "items": fetch_market_news(category=category, limit=limit, token=api_key),
    }
