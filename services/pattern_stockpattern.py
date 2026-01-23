from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class PatternSignal:
    name: str
    direction: str  # "bullish" | "bearish" | "neutral"
    confidence: float  # 0.0 - 1.0
    points: Optional[List[Dict[str, Any]]] = None  # punti da disegnare (x,y,label)
    lines: Optional[List[Dict[str, Any]]] = None   # linee da disegnare (x1,y1,x2,y2,label)


def run_stock_pattern(candles: List[Dict[str, Any]], horizon: str = "short") -> Dict[str, Any]:
    """
    Versione 'safe' e semplice: restituisce 1 segnale placeholder coerente con UI.
    Poi la colleghiamo davvero alla libreria di pattern (step dopo).
    candles: lista di candele con open/high/low/close + timestamp
    horizon: "short" (1-2 settimane) | "long" (6-24 mesi)
    """

    # Esempio: se negli ultimi N periodi il close sta scendendo -> ribassista
    n = 30 if horizon == "short" else 200
    recent = candles[-n:] if len(candles) >= n else candles[:]

    closes = [c.get("close") for c in recent if c.get("close") is not None]
    if len(closes) < 5:
        return {
            "pattern": None,
            "direction": "neutral",
            "confidence": 0.50,
            "explanation": "Dati insufficienti per un pattern affidabile.",
            "overlay": {"points": [], "lines": []},
        }

    trend = closes[-1] - closes[0]
    if trend > 0:
        direction = "bullish"
        name = "Trend rialzista"
        confidence = 0.62
        explanation = "Il prezzo mostra una tendenza crescente nel periodo analizzato."
    elif trend < 0:
        direction = "bearish"
        name = "Trend ribassista"
        confidence = 0.62
        explanation = "Il prezzo mostra una tendenza decrescente nel periodo analizzato."
    else:
        direction = "neutral"
        name = "Laterale"
        confidence = 0.55
        explanation = "Il prezzo è sostanzialmente laterale nel periodo analizzato."

    # Overlay base: 2 punti inizio/fine trend per disegnare una linea guida
    p1 = {"x": 0, "y": float(closes[0]), "label": "Start"}
    p2 = {"x": len(closes) - 1, "y": float(closes[-1]), "label": "End"}
    line = {"x1": p1["x"], "y1": p1["y"], "x2": p2["x"], "y2": p2["y"], "label": "Trend"}

    return {
        "pattern": name,
        "direction": direction,
        "confidence": float(confidence),
        "explanation": explanation,
        "overlay": {"points": [p1, p2], "lines": [line]},
    }
