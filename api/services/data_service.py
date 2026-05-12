import yfinance as yf
import pandas as pd
import datetime


def get_price_data(ticker: str, start_date: str, end_date: str = None) -> pd.DataFrame:
    """Download OHLCV data from Yahoo Finance."""
    if end_date is None:
        end_date = str(datetime.date.today())

    raw = yf.download(ticker, start=start_date, end=end_date, auto_adjust=False, progress=False)

    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)

    if raw.empty:
        raise ValueError(f"No data found for ticker '{ticker}'")

    return raw


def get_ticker_info(ticker: str) -> dict:
    """Get company info and metadata from Yahoo Finance."""
    t = yf.Ticker(ticker)
    info = t.info
    return {
        "ticker":        ticker.upper(),
        "name":          info.get("longName", "N/A"),
        "sector":        info.get("sector", "N/A"),
        "industry":      info.get("industry", "N/A"),
        "market_cap":    info.get("marketCap", None),
        "pe_ratio":      info.get("trailingPE", None),
        "52w_high":      info.get("fiftyTwoWeekHigh", None),
        "52w_low":       info.get("fiftyTwoWeekLow", None),
        "avg_volume":    info.get("averageVolume", None),
        "dividend_yield": info.get("dividendYield", None),
        "currency":      info.get("currency", "USD"),
        "exchange":      info.get("exchange", "N/A"),
    }
