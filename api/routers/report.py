from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..services import indicator_service, sentiment_service
from ..routers.llm import _build_prompt, _groq_client, GROQ_MODEL
from ..services.email_service import send_analysis_email
from ..services.chart_service import generate_charts
from ..services.data_service import get_price_data

router = APIRouter(prefix="/report", tags=["Reports"])


class ReportRequest(BaseModel):
    ticker: str
    email: str
    start_date: Optional[str] = "2023-01-01"
    end_date: Optional[str] = None


@router.post("/send")
def send_report(req: ReportRequest):
    """
    Full pipeline for any ticker:
    1. Fetch technical indicators
    2. Fetch news sentiment
    3. Call Groq LLM for analysis
    4. Generate charts (candlestick + BB + RSI + MACD)
    5. Send professional HTML report with charts to email

    Works for ALL 13,000+ tickers.
    """
    ticker = req.ticker.strip().upper()

    try:
        # Step 1 — indicators
        indicators = indicator_service.get_all_indicators(ticker, req.start_date, req.end_date)
        latest     = indicators.get("latest", {})

        # Step 2 — sentiment
        sentiment = sentiment_service.get_news_sentiment(ticker)

        # Step 3 — Groq analysis
        prompt   = _build_prompt(ticker, latest, sentiment)
        response = _groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are a professional stock analyst. Be concise and data-driven."},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.3,
            max_tokens=512,
        )
        analysis = response.choices[0].message.content

        # Step 4 — generate charts
        df     = get_price_data(ticker, req.start_date, req.end_date)
        charts = generate_charts(df, ticker)

        # Step 5 — build payload
        report_data = {
            "ticker":    ticker,
            "price":     latest.get("price"),
            "sentiment": sentiment.get("overall"),
            "analysis":  analysis,
            "indicators": {
                "rsi":         latest.get("rsi"),
                "macd":        latest.get("macd"),
                "signal":      latest.get("signal"),
                "cci":         latest.get("cci"),
                "sma":         latest.get("sma"),
                "ema":         latest.get("ema"),
                "obv_million": latest.get("obv"),
            },
        }

        # Step 6 — send email with charts
        send_analysis_email(req.email, ticker, report_data, charts)

        return {
            "status":    "sent",
            "ticker":    ticker,
            "email":     req.email,
            "price":     latest.get("price"),
            "sentiment": sentiment.get("overall"),
            "analysis":  analysis,
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
