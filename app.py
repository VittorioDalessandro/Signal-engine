from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os

from services.data_provider import fetch_ohlc_finnhub
from services.pattern_stockpattern import run_stock_pattern

app = FastAPI(title="Signal Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/analyze")
def analyze(ticker: str, horizon: str = "short"):
    ticker = ticker.upper().strip()
    horizon = horizon.lower().strip()

    if not FINNHUB_API_KEY:
        raise HTTPException(status_code=500, detail="Missing FINNHUB_API_KEY")

    if horizon not in ["short", "long"]:
        raise HTTPException(status_code=400, detail="horizon must be short or long")

    if horizon == "short":
        timeframe = "1D"
        candles = 140
    else:
        timeframe = "1W"
        candles = 220

    ohlc = fetch_ohlc_finnhub(ticker, timeframe, candles, FINNHUB_API_KEY)

    if len(ohlc) < 50:
        return {"ticker": ticker, "patterns": [], "note": "Not enough data"}

    patterns = run_stock_pattern(ohlc)

    return {
        "ticker": ticker,
        "horizon": horizon,
        "timeframe": timeframe,
        "patterns": patterns
    }
