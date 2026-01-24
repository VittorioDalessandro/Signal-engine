from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os

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

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/analyze")
def analyze(ticker: str, horizon: str = "short", include_news: bool = True, news_limit: int = 8):
    ticker = ticker.upper().strip()
    horizon = horizon.lower().strip()

    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing FINNHUB_API_KEY")

    if horizon not in ["short", "long"]:
        raise HTTPException(status_code=400, detail="horizon must be short or long")

    # short = daily, long = weekly (più stabile)
    if horizon == "short":
        resolution = "D"
        count = 140
    else:
        resolution = "W"
        count = 220

    ohlc = fetch_ohlc_finnhub(ticker=ticker, resolution=resolution, count=count, token=api_key)

    if len(ohlc) < 50:
        return {"ticker": ticker, "note": "Not enough data", "candles": len(ohlc)}

    pattern_result = run_stock_pattern(ohlc, horizon=horizon)

    out = {
        "ticker": ticker,
        "horizon": horizon,
        "resolution": resolution,
        "pattern": pattern_result,
    }

    if include_news:
        # per ora news di mercato "general"; poi possiamo farle anche per singolo ticker
        out["news"] = fetch_market_news(category="general", limit=news_limit, token=api_key)

    return out

@app.get("/news")
def news(category: str = "general", limit: int = 10):
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing FINNHUB_API_KEY")

    return {
        "category": category,
        "items": fetch_market_news(category=category, limit=limit, token=api_key),
    }

