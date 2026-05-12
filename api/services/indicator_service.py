import sys
import os
import pandas as pd

# Add project root to path so ta_functions is importable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ta_functions as ta

from .data_service import get_price_data


def _df_to_records(df: pd.DataFrame) -> list:
    """Convert DataFrame to list of dicts with date as string key."""
    df = df.copy()
    df.index = df.index.astype(str)
    return df.reset_index().rename(columns={"index": "date", "Date": "date"}).to_dict(orient="records")


def get_price(ticker: str, start_date: str, end_date: str = None) -> list:
    """Return adjusted close price series."""
    df = get_price_data(ticker, start_date, end_date)
    result = df[["Adj Close"]].copy()
    result.columns = ["price"]
    return _df_to_records(result)


def get_sma_ema(ticker: str, start_date: str, end_date: str = None, period: int = 20) -> list:
    """Return price with SMA and EMA."""
    df = get_price_data(ticker, start_date, end_date)
    result = df[["Adj Close"]].copy()
    result.columns = ["price"]
    result["sma"] = ta.SMA(df["Adj Close"], timeperiod=period)
    result["ema"] = ta.EMA(df["Adj Close"], timeperiod=period)
    return _df_to_records(result)


def get_bollinger_bands(ticker: str, start_date: str, end_date: str = None, period: int = 20) -> list:
    """Return Bollinger Bands (upper, middle, lower)."""
    df = get_price_data(ticker, start_date, end_date)
    upper, middle, lower = ta.BBANDS(df["Adj Close"], timeperiod=period)
    result = pd.DataFrame({
        "price":  df["Adj Close"],
        "upper":  upper,
        "middle": middle,
        "lower":  lower,
    })
    return _df_to_records(result)


def get_macd(ticker: str, start_date: str, end_date: str = None) -> list:
    """Return MACD, signal line, and histogram."""
    df = get_price_data(ticker, start_date, end_date)
    macd, signal, hist = ta.MACD(df["Adj Close"], fastperiod=12, slowperiod=26, signalperiod=9)
    result = pd.DataFrame({
        "macd":      macd,
        "signal":    signal,
        "histogram": hist,
    })
    return _df_to_records(result)


def get_rsi(ticker: str, start_date: str, end_date: str = None, period: int = 14) -> list:
    """Return RSI values."""
    df = get_price_data(ticker, start_date, end_date)
    result = pd.DataFrame({"rsi": ta.RSI(df["Adj Close"], timeperiod=period)})
    return _df_to_records(result)


def get_cci(ticker: str, start_date: str, end_date: str = None, period: int = 14) -> list:
    """Return CCI values."""
    df = get_price_data(ticker, start_date, end_date)
    result = pd.DataFrame({"cci": ta.CCI(df["High"], df["Low"], df["Close"], timeperiod=period)})
    return _df_to_records(result)


def get_obv(ticker: str, start_date: str, end_date: str = None) -> list:
    """Return On Balance Volume."""
    df = get_price_data(ticker, start_date, end_date)
    result = pd.DataFrame({"obv": ta.OBV(df["Adj Close"], df["Volume"]) / 1e6})
    return _df_to_records(result)


def get_all_indicators(ticker: str, start_date: str, end_date: str = None, period: int = 14) -> dict:
    """Return all indicators in one call — useful for n8n/LLM pipelines."""
    df = get_price_data(ticker, start_date, end_date)
    close = df["Adj Close"]

    upper, middle, lower = ta.BBANDS(close, timeperiod=20)
    macd, signal, hist   = ta.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)

    result = pd.DataFrame({
        "price":     close,
        "sma":       ta.SMA(close, timeperiod=period),
        "ema":       ta.EMA(close, timeperiod=period),
        "rsi":       ta.RSI(close, timeperiod=period),
        "cci":       ta.CCI(df["High"], df["Low"], df["Close"], timeperiod=period),
        "macd":      macd,
        "signal":    signal,
        "histogram": hist,
        "bb_upper":  upper,
        "bb_middle": middle,
        "bb_lower":  lower,
        "obv":       ta.OBV(close, df["Volume"]) / 1e6,
    })

    # Return latest snapshot + full series
    latest = result.dropna().iloc[-1].to_dict()
    latest = {k: round(v, 4) for k, v in latest.items()}

    return {
        "ticker":  ticker.upper(),
        "latest":  latest,
        "series":  _df_to_records(result),
    }
