from fastapi import APIRouter, HTTPException
from ..models.schemas import StockRequest, IndicatorRequest
from ..services import data_service, indicator_service

router = APIRouter(prefix="/stock", tags=["Stock Data"])


@router.get("/info/{ticker}")
def stock_info(ticker: str):
    """Get company info and metadata for a ticker."""
    try:
        return data_service.get_ticker_info(ticker)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/price/{ticker}")
def stock_price(ticker: str, start_date: str = "2020-01-01", end_date: str = None):
    """Get historical adjusted close price series."""
    try:
        return {
            "ticker": ticker.upper(),
            "data":   indicator_service.get_price(ticker, start_date, end_date),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/indicators/{ticker}")
def all_indicators(ticker: str, start_date: str = "2020-01-01", end_date: str = None, period: int = 14):
    """
    Get all technical indicators in one call.
    Returns latest snapshot + full time series.
    Perfect for n8n and LLM pipelines.
    """
    try:
        return indicator_service.get_all_indicators(ticker, start_date, end_date, period)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/sma-ema/{ticker}")
def sma_ema(ticker: str, start_date: str = "2020-01-01", end_date: str = None, period: int = 20):
    """Get SMA and EMA for a ticker."""
    try:
        return {
            "ticker": ticker.upper(),
            "period": period,
            "data":   indicator_service.get_sma_ema(ticker, start_date, end_date, period),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/bollinger/{ticker}")
def bollinger_bands(ticker: str, start_date: str = "2020-01-01", end_date: str = None, period: int = 20):
    """Get Bollinger Bands for a ticker."""
    try:
        return {
            "ticker": ticker.upper(),
            "period": period,
            "data":   indicator_service.get_bollinger_bands(ticker, start_date, end_date, period),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/macd/{ticker}")
def macd(ticker: str, start_date: str = "2020-01-01", end_date: str = None):
    """Get MACD, signal line, and histogram."""
    try:
        return {
            "ticker": ticker.upper(),
            "data":   indicator_service.get_macd(ticker, start_date, end_date),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/rsi/{ticker}")
def rsi(ticker: str, start_date: str = "2020-01-01", end_date: str = None, period: int = 14):
    """Get RSI values for a ticker."""
    try:
        return {
            "ticker": ticker.upper(),
            "period": period,
            "data":   indicator_service.get_rsi(ticker, start_date, end_date, period),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/cci/{ticker}")
def cci(ticker: str, start_date: str = "2020-01-01", end_date: str = None, period: int = 14):
    """Get CCI values for a ticker."""
    try:
        return {
            "ticker": ticker.upper(),
            "period": period,
            "data":   indicator_service.get_cci(ticker, start_date, end_date, period),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/obv/{ticker}")
def obv(ticker: str, start_date: str = "2020-01-01", end_date: str = None):
    """Get On Balance Volume for a ticker."""
    try:
        return {
            "ticker": ticker.upper(),
            "data":   indicator_service.get_obv(ticker, start_date, end_date),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
