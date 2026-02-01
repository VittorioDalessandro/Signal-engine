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


def _get_key() -> str:
    key = os.getenv("FINNHUB_API_KEY", "").strip()
    if not key:
        raise HTTPException(status_code=500, detail="Missing FINNHUB_API_KEY")
    return key


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/pattern")
def pattern(ticker: str, horizon: str = "short"):
    """
    Solo pattern (analisi tecnica + spiegazione + overlay).
    """
    ticker = ticker.upper().strip()
    horizon = horizon.lower().strip()
    _get_key()  # verifica key (data_provider la legge da env)

    if horizon not in ["short", "long"]:
        raise HTTPException(status_code=400, detail="horizon must be short or long")

    # short = daily, long = weekly
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
        return {"ticker": ticker, "horizon": horizon, "pattern": None, "note": "Not enough data"}

    try:
        pattern_result = run_stock_pattern(ohlc, horizon=horizon)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pattern engine error: {str(e)}")

    return {
        "ticker": ticker,
        "horizon": horizon,
        "resolution": resolution,
        "pattern": pattern_result,
    }


@app.get("/news/market")
def news_market(category: str = "general", limit: int = 10):
    """
    Solo news di mercato (macro/contesto).
    """
    key = _get_key()
    try:
        items = fetch_market_news(category=category, limit=limit, token=key)
        return {"category": category, "items": items}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"News provider error: {str(e)}")


@app.get("/news/company")
def news_company(ticker: str, days_back: int = 7, limit: int = 10):
    """
    Solo news del titolo (ticker).
    """
    key = _get_key()
    ticker = ticker.upper().strip()
    try:
        items = fetch_company_news(ticker=ticker, days_back=days_back, limit=limit, token=key)
        return {"ticker": ticker, "days_back": days_back, "items": items}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"News provider error: {str(e)}")


@app.get("/analyze")
def analyze(
    ticker: str,
    horizon: str = "short",
    include_market_news: bool = True,
    include_company_news: bool = True,
):
    """
    Aggregatore: pattern + news.
    È quello più comodo da chiamare dal frontend/Base44.
    """
    key = _get_key()
    ticker = ticker.upper().strip()
    horizon = horizon.lower().strip()

    if horizon not in ["short", "long"]:
        raise HTTPException(status_code=400, detail="horizon must be short or long")

    # dati prezzi (short = daily, long = weekly)
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
        return {"ticker": ticker, "horizon": horizon, "pattern": None, "note": "Not enough data"}

    try:
        pattern_result = run_stock_pattern(ohlc, horizon=horizon)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pattern engine error: {str(e)}")

    out = {
        "ticker": ticker,
        "horizon": horizon,
        "resolution": resolution,
        "pattern": pattern_result,
    }

    if include_market_news:
        out["market_news"] = fetch_market_news(category="general", limit=8, token=key)

    if include_company_news:
        out["company_news"] = fetch_company_news(ticker=ticker, days_back=7, limit=8, token=key)

    return out
