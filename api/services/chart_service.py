import io
import base64
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ta_functions as ta


def _df_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return encoded


def generate_charts(df: pd.DataFrame, ticker: str) -> dict:
    try:
        df = df.copy().tail(120).reset_index()

        close  = df["Adj Close"]
        high   = df["High"]
        low    = df["Low"]
        open_  = df["Open"]
        dates  = df["Date"] if "Date" in df.columns else pd.Series(range(len(df)))

        # Compute indicators — all return same-length Series
        sma20              = ta.SMA(close, 20).reset_index(drop=True)
        upper, mid, lower  = ta.BBANDS(close, 20)
        upper  = upper.reset_index(drop=True)
        mid    = mid.reset_index(drop=True)
        lower  = lower.reset_index(drop=True)
        rsi    = ta.RSI(close, 14).reset_index(drop=True)
        macd_s, signal_s, hist_s = ta.MACD(close, 12, 26, 9)
        macd_s   = macd_s.reset_index(drop=True)
        signal_s = signal_s.reset_index(drop=True)
        hist_s   = hist_s.reset_index(drop=True)

        close  = close.reset_index(drop=True)
        open_  = open_.reset_index(drop=True)
        high   = high.reset_index(drop=True)
        low    = low.reset_index(drop=True)

        # Build aligned frame — drop NaN rows
        frame = pd.DataFrame({
            "close": close, "open": open_, "high": high, "low": low,
            "sma20": sma20, "upper": upper, "mid": mid, "lower": lower,
            "rsi": rsi, "macd": macd_s, "signal": signal_s, "hist": hist_s,
        }).dropna().reset_index(drop=True)

        if len(frame) < 10:
            return {}

        n = len(frame)
        x = np.arange(n)

        # Date labels
        date_labels = dates.reset_index(drop=True).iloc[frame.index] if hasattr(dates, "iloc") else None

        BG    = "#0f172a"
        CARD  = "#1e293b"
        BLUE  = "#60a5fa"
        GREEN = "#22c55e"
        RED   = "#ef4444"
        GRAY  = "#94a3b8"
        WHITE = "#e2e8f0"
        GOLD  = "#f59e0b"

        fig = plt.figure(figsize=(12, 8), facecolor=BG)
        gs  = GridSpec(3, 1, figure=fig, height_ratios=[3, 1, 1], hspace=0.06)

        # Panel 1 — Candlestick + Bollinger Bands
        ax1 = fig.add_subplot(gs[0])
        ax1.set_facecolor(CARD)
        for i in range(n):
            c = GREEN if frame["close"].iloc[i] >= frame["open"].iloc[i] else RED
            ax1.plot([i, i], [frame["low"].iloc[i], frame["high"].iloc[i]],
                     color=c, linewidth=0.8)
            ax1.bar(i, abs(frame["close"].iloc[i] - frame["open"].iloc[i]),
                    bottom=min(frame["open"].iloc[i], frame["close"].iloc[i]),
                    color=c, width=0.6, alpha=0.9)
        ax1.plot(x, frame["upper"].values, color=BLUE, linewidth=1,
                 linestyle="--", alpha=0.7, label="BB Upper")
        ax1.plot(x, frame["mid"].values,   color=GOLD, linewidth=1.2, label="SMA 20")
        ax1.plot(x, frame["lower"].values, color=BLUE, linewidth=1,
                 linestyle="--", alpha=0.7, label="BB Lower")
        ax1.fill_between(x, frame["upper"].values, frame["lower"].values,
                         alpha=0.05, color=BLUE)
        ax1.set_title(f"{ticker} — Price · Bollinger Bands · RSI · MACD",
                      color=WHITE, fontsize=12, fontweight="bold", pad=10)
        ax1.tick_params(colors=GRAY, labelbottom=False)
        ax1.spines[:].set_color(CARD)
        ax1.legend(facecolor=CARD, labelcolor=WHITE, fontsize=8, loc="upper left")

        # Panel 2 — RSI
        ax2 = fig.add_subplot(gs[1], sharex=ax1)
        ax2.set_facecolor(CARD)
        ax2.plot(x, frame["rsi"].values, color=GOLD, linewidth=1.5)
        ax2.axhline(70, color=RED,   linewidth=0.8, linestyle="--", alpha=0.7)
        ax2.axhline(30, color=GREEN, linewidth=0.8, linestyle="--", alpha=0.7)
        ax2.fill_between(x, frame["rsi"].values, 70,
                         where=frame["rsi"].values > 70, alpha=0.2, color=RED)
        ax2.fill_between(x, frame["rsi"].values, 30,
                         where=frame["rsi"].values < 30, alpha=0.2, color=GREEN)
        ax2.set_ylim(0, 100)
        ax2.set_ylabel("RSI", color=GRAY, fontsize=9)
        ax2.tick_params(colors=GRAY, labelbottom=False)
        ax2.spines[:].set_color(CARD)

        # Panel 3 — MACD
        ax3 = fig.add_subplot(gs[2], sharex=ax1)
        ax3.set_facecolor(CARD)
        ax3.plot(x, frame["macd"].values,   color=BLUE, linewidth=1.2, label="MACD")
        ax3.plot(x, frame["signal"].values, color=GOLD, linewidth=1.2, label="Signal")
        bar_colors = [GREEN if h >= 0 else RED for h in frame["hist"].values]
        ax3.bar(x, frame["hist"].values, color=bar_colors, alpha=0.6, width=0.6)
        ax3.axhline(0, color=GRAY, linewidth=0.5)
        ax3.set_ylabel("MACD", color=GRAY, fontsize=9)
        ax3.tick_params(colors=GRAY)
        ax3.spines[:].set_color(CARD)

        # X-axis labels
        step   = max(1, n // 6)
        xticks = list(range(0, n, step))
        if date_labels is not None:
            try:
                xlabels = [pd.to_datetime(date_labels.iloc[i]).strftime("%b %d")
                           for i in xticks]
            except Exception:
                xlabels = [str(i) for i in xticks]
        else:
            xlabels = [str(i) for i in xticks]
        ax3.set_xticks(xticks)
        ax3.set_xticklabels(xlabels, color=GRAY, fontsize=8)

        fig.tight_layout()
        return {"price_bb_rsi_macd": _df_to_base64(fig)}

    except Exception as e:
        # If chart generation fails for any reason, return empty so email still sends
        print(f"Chart generation error for {ticker}: {e}")
        return {}
