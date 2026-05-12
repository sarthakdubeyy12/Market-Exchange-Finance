import os
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from groq import Groq

from ..services import indicator_service, sentiment_service

load_dotenv()

router = APIRouter(prefix="/llm", tags=["LLM Ready Endpoints"])

# Groq client — reads key from .env
_groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
GROQ_MODEL = "llama-3.3-70b-versatile"


class AnalysisRequest(BaseModel):
    ticker: str
    start_date: Optional[str] = "2023-01-01"
    end_date: Optional[str] = None


# ── /llm/summary/{ticker} ─────────────────────────────────────────────────────
@router.get("/summary/{ticker}")
def llm_summary(ticker: str, start_date: str = "2023-01-01", end_date: str = None):
    """
    Returns structured payload with indicators + sentiment + a ready LLM prompt.
    Use this in n8n to feed into the Groq node manually.
    """
    try:
        indicators = indicator_service.get_all_indicators(ticker, start_date, end_date)
        latest     = indicators.get("latest", {})
        sentiment  = sentiment_service.get_news_sentiment(ticker)
        headlines  = sentiment.get("headlines", [])[:5]

        return {
            "ticker": ticker.upper(),
            "price":  latest.get("price"),
            "indicators": {
                "rsi":         latest.get("rsi"),
                "macd":        latest.get("macd"),
                "signal":      latest.get("signal"),
                "cci":         latest.get("cci"),
                "sma":         latest.get("sma"),
                "ema":         latest.get("ema"),
                "bb_upper":    latest.get("bb_upper"),
                "bb_lower":    latest.get("bb_lower"),
                "obv_million": latest.get("obv"),
            },
            "sentiment": {
                "overall":       sentiment.get("overall"),
                "score":         sentiment.get("score"),
                "top_headlines": [h["headline"] for h in headlines],
            },
            "llm_prompt": _build_prompt(ticker, latest, sentiment),
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── /llm/analyze/{ticker} ─────────────────────────────────────────────────────
@router.get("/analyze/{ticker}")
def llm_analyze(ticker: str, start_date: str = "2023-01-01", end_date: str = None):
    """
    Full pipeline in one call:
    1. Fetches technical indicators
    2. Fetches news sentiment
    3. Sends everything to Groq LLM
    4. Returns the AI analysis

    Perfect for n8n — just call this endpoint and get the analysis directly.
    """
    try:
        # Step 1 — get data
        indicators = indicator_service.get_all_indicators(ticker, start_date, end_date)
        latest     = indicators.get("latest", {})
        sentiment  = sentiment_service.get_news_sentiment(ticker)

        # Step 2 — build prompt
        prompt = _build_prompt(ticker, latest, sentiment)

        # Step 3 — call Groq
        response = _groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional stock market analyst. Be concise, data-driven, and clear.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.3,
            max_tokens=512,
        )

        analysis = response.choices[0].message.content

        # Step 4 — return full result
        return {
            "ticker":   ticker.upper(),
            "price":    latest.get("price"),
            "sentiment": sentiment.get("overall"),
            "analysis": analysis,
            "model":    GROQ_MODEL,
            "indicators": {
                "rsi":    latest.get("rsi"),
                "macd":   latest.get("macd"),
                "cci":    latest.get("cci"),
                "sma":    latest.get("sma"),
                "ema":    latest.get("ema"),
            },
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── helpers ───────────────────────────────────────────────────────────────────
def _build_prompt(ticker: str, indicators: dict, sentiment: dict) -> str:
    headlines = sentiment.get("headlines", [])[:5]
    headline_text = "\n".join(f"- {h['headline']}" for h in headlines) or "No headlines available."

    return f"""You are a professional stock market analyst. Analyze the following data for {ticker.upper()} and provide a concise trading summary.

## Technical Indicators (Latest Values)
- Price: {indicators.get('price')}
- RSI (14): {indicators.get('rsi')} — (oversold < 30, overbought > 70)
- MACD: {indicators.get('macd')} | Signal: {indicators.get('signal')}
- CCI (14): {indicators.get('cci')}
- SMA (14): {indicators.get('sma')}
- EMA (14): {indicators.get('ema')}
- Bollinger Upper: {indicators.get('bb_upper')} | Lower: {indicators.get('bb_lower')}
- OBV (millions): {indicators.get('obv')}

## News Sentiment
- Overall: {sentiment.get('overall')} (score: {sentiment.get('score')})
- Recent Headlines:
{headline_text}

## Your Analysis
Please provide:
1. Overall market signal (Bullish / Bearish / Neutral)
2. Key observations from the technical indicators
3. What the news sentiment suggests
4. A short recommendation (1-2 sentences)
"""
