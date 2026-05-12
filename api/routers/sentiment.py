from fastapi import APIRouter, HTTPException
from ..services import sentiment_service

router = APIRouter(prefix="/sentiment", tags=["Sentiment"])


@router.get("/news/{ticker}")
def news_sentiment(ticker: str):
    """
    Get latest news headlines from Finviz for a ticker
    with VADER sentiment scores (bullish / bearish / neutral).
    Great for feeding into an LLM for deeper analysis.
    """
    try:
        return sentiment_service.get_news_sentiment(ticker)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
