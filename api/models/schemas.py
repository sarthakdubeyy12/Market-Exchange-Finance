from pydantic import BaseModel
from typing import Optional


class StockRequest(BaseModel):
    ticker: str
    start_date: Optional[str] = "2020-01-01"
    end_date: Optional[str] = None  # defaults to today


class IndicatorRequest(BaseModel):
    ticker: str
    start_date: Optional[str] = "2020-01-01"
    end_date: Optional[str] = None
    period: Optional[int] = 14  # timeperiod for indicators


class ScreenerRequest(BaseModel):
    universe: Optional[str] = "sp500"  # sp500 | nasdaq | nyse


class SentimentRequest(BaseModel):
    ticker: str
