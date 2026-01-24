from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os

from services.data_provider import fetch_ohlc_finnhub
from services.pattern_stockpattern import run_stock_pattern
from services.news_provider import fetch_market_news, fetch_company_news

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
def analyze(ticker: str, horizon: str = "short"):
    ticker = ticker.upper().strip()
    horizon = horizon.lower().strip()

    FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "").strip()
    if not FINNHUB_API_KEY:
        raise HTTPException(status_code=500, detail="Missing FINNHUB_API_KEY")

    if horizon not in ["short", "long"]:
        raise HTTPException(status_code=400, detail="horizon must be short or long")

    # Finnhub resolution: "D" (daily) or "W" (weekly)
    if horizon == "short":
        resolution = "D"
        count = 140
    else:
        resolution = "W"
        count = 220

    try:
        ohlc = fetch_ohlc_finnhub(ticker, resolution=resolution, count=count)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Data provider error: {str(e)}")

    if len(ohlc) < 50:
        return {"ticker": ticker, "patterns": [], "note": "Not enough data"}

    patterns = run_stock_pattern(ohlc, horizon=horizon)

    return {
        "ticker": ticker,
        "horizon": horizon,
        "resolution": resolution,
        "patterns": patterns,
    }

@app.get("/news/market")
def news_market(category: str = "general", limit: int = 10):
    try:
        out = fetch_market_news(category=category, limit=limit)
        return {"category": category, "items": out}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"News provider error: {str(e)}")

@app.get("/news/company")
def news_company(ticker: str, limit: int = 10):
    ticker = ticker.upper().strip()
    try:
        out = fetch_company_news(ticker=ticker, limit=limit)
        return {"ticker": ticker, "items": out}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"News provider error: {str(e)}")
