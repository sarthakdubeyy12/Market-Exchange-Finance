import sys
import os
import pandas as pd
import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ta_functions as ta
import tickers as ti

from .data_service import get_price_data


def _load_tickers(universe: str) -> list:
    """Load tickers from CSV files or live fetch."""
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    csv_map = {
        "sp500":       "s&p500_tickers.csv",
        "nasdaq":      "nasdaq_tickers.csv",
        "nyse":        "nyse_tickers.csv",
        "amex":        "amex_tickers.csv",
        "russell3000": "russell3000_tickers.csv",
        "nse":         "nse_tickers.csv",
        "bse":         "bse_tickers.csv",
    }
    fname = csv_map.get(universe.lower())
    if fname:
        path = os.path.join(base, fname)
        df = pd.read_csv(path)
        return df["Ticker"].dropna().str.strip().tolist()
    raise ValueError(f"Unknown universe '{universe}'. Choose from: {list(csv_map.keys())}")


def rsi_screener(universe: str = "sp500", oversold: int = 30, overbought: int = 70) -> dict:
    """
    Screen stocks by RSI.
    Returns oversold (RSI < oversold) and overbought (RSI > overbought) lists.
    """
    tickers = _load_tickers(universe)
    start = str(datetime.date.today() - datetime.timedelta(days=90))
    end   = str(datetime.date.today())

    oversold_list  = []
    overbought_list = []

    for ticker in tickers[:100]:  # limit to 100 for performance
        try:
            df    = get_price_data(ticker, start, end)
            rsi   = ta.RSI(df["Adj Close"], timeperiod=14).dropna()
            if rsi.empty:
                continue
            latest_rsi = round(float(rsi.iloc[-1]), 2)
            entry = {"ticker": ticker, "rsi": latest_rsi}
            if latest_rsi < oversold:
                oversold_list.append(entry)
            elif latest_rsi > overbought:
                overbought_list.append(entry)
        except Exception:
            continue

    return {
        "universe":   universe,
        "oversold":   sorted(oversold_list,  key=lambda x: x["rsi"]),
        "overbought": sorted(overbought_list, key=lambda x: x["rsi"], reverse=True),
    }


def minervini_screener(universe: str = "sp500") -> list:
    """
    Apply Minervini's SEPA trend template criteria.
    Returns stocks that pass all conditions.
    """
    tickers = _load_tickers(universe)
    start   = str(datetime.date.today() - datetime.timedelta(days=365))
    end     = str(datetime.date.today())
    results = []

    for ticker in tickers[:100]:
        try:
            df = get_price_data(ticker, start, end)
            if len(df) < 200:
                continue

            close = df["Adj Close"]
            sma50  = ta.SMA(close, 50)
            sma150 = ta.SMA(close, 150)
            sma200 = ta.SMA(close, 200)

            current  = float(close.iloc[-1])
            s50      = float(sma50.iloc[-1])
            s150     = float(sma150.iloc[-1])
            s200     = float(sma200.iloc[-1])
            s200_20  = float(sma200.iloc[-20])
            low_52w  = float(close.rolling(252).min().iloc[-1])
            high_52w = float(close.rolling(252).max().iloc[-1])

            conditions = [
                current > s150 > s200,
                s150 > s200_20,
                current > s50,
                current >= 1.3 * low_52w,
                current >= 0.75 * high_52w,
            ]

            if all(conditions):
                results.append({
                    "ticker":   ticker,
                    "price":    round(current, 2),
                    "sma_50":   round(s50, 2),
                    "sma_150":  round(s150, 2),
                    "sma_200":  round(s200, 2),
                    "52w_low":  round(low_52w, 2),
                    "52w_high": round(high_52w, 2),
                })
        except Exception:
            continue

    return results
