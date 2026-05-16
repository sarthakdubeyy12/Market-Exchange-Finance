import yfinance as yf
import streamlit as st
import datetime
import pandas as pd
import sys
import os
import requests as http_requests

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
import ta_functions as ta

# API base URL — reads from Streamlit secrets in production, falls back to localhost
try:
    API_BASE = st.secrets["API_BASE_URL"]
except Exception:
    API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Finance Master", layout="wide")

# ── Navigation ────────────────────────────────────────────────────────────────
page = st.sidebar.radio("📌 Navigation", ["📈 Stock Charts", "🔍 RSI Screener"])

# ── Load ticker CSVs ──────────────────────────────────────────────────────────
@st.cache_data
def load_all_tickers():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    us_files = {
        "NASDAQ":      "nasdaq_tickers.csv",
        "NYSE":        "nyse_tickers.csv",
        "AMEX":        "amex_tickers.csv",
        "Russell3000": "russell3000_tickers.csv",
        "S&P500":      "s&p500_tickers.csv",
    }
    india_files = {
        "NSE": "nse_tickers.csv",
        "BSE": "bse_tickers.csv",
    }
    def read_files(file_map):
        frames = []
        for exchange, fname in file_map.items():
            path = os.path.join(base, fname)
            try:
                df = pd.read_csv(path, usecols=["Ticker", "Company Name"])
                df["Exchange"] = exchange
                frames.append(df)
            except Exception:
                pass
        if not frames:
            return pd.DataFrame(columns=["Ticker", "Company Name", "Exchange"])
        combined = pd.concat(frames, ignore_index=True)
        combined = combined.dropna(subset=["Ticker"])
        combined["Ticker"] = combined["Ticker"].str.strip().str.upper()
        combined = combined.drop_duplicates(subset=["Ticker"]).sort_values("Ticker")
        combined["Label"] = combined["Ticker"] + " — " + combined["Company Name"].fillna("")
        return combined
    return read_files(us_files), read_files(india_files)

us_df, india_df = load_all_tickers()
today = datetime.date.today()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — STOCK CHARTS
# ══════════════════════════════════════════════════════════════════════════════
if page == "📈 Stock Charts":

    st.title("📈 Technical Analysis")
    st.caption("Moving Averages · Bollinger Bands · MACD · RSI · CCI · OBV")

    st.sidebar.header("User Input Parameters")

    selected_market = st.sidebar.selectbox("🌍 Select Market",
                                           ["🇺🇸 US Market", "🇮🇳 Indian Market"])
    if selected_market == "🇺🇸 US Market":
        market_df        = us_df
        exchange_options = ["All", "NASDAQ", "NYSE", "AMEX", "S&P500", "Russell3000"]
    else:
        market_df        = india_df
        exchange_options = ["All", "NSE", "BSE"]

    selected_exchange = st.sidebar.selectbox("🏦 Filter by Exchange", exchange_options)
    filtered_df = (market_df[market_df["Exchange"] == selected_exchange]
                   if selected_exchange != "All" else market_df)

    filtered_labels  = filtered_df["Label"].tolist()
    filtered_symbols = filtered_df["Ticker"].tolist()

    default_ticker = "AAPL" if selected_market == "🇺🇸 US Market" else "RELIANCE.NS"
    default_idx    = filtered_symbols.index(default_ticker) if default_ticker in filtered_symbols else 0

    selected_label = st.sidebar.selectbox(
        f"📈 Select Ticker ({len(filtered_symbols):,} available)",
        filtered_labels, index=default_idx)

    manual_ticker = st.sidebar.text_input("✏️ Or type a ticker manually", "")
    symbol = (manual_ticker.strip().upper() if manual_ticker.strip()
              else filtered_symbols[filtered_labels.index(selected_label)])

    start_date = st.sidebar.text_input("Start Date", "2019-01-01")
    end_date   = st.sidebar.text_input("End Date", str(today))
    start      = pd.to_datetime(start_date)
    end        = pd.to_datetime(end_date)

    # Email section
    st.sidebar.markdown("---")
    st.sidebar.subheader("📧 Email Analysis Report")
    email_input = st.sidebar.text_input("Your Email Address", placeholder="you@gmail.com")

    if st.sidebar.button("🔍 Analyze & Send Report"):
        if not email_input:
            st.sidebar.error("Please enter your email address.")
        else:
            with st.spinner(f"Analyzing {symbol} with AI — generating charts & sending report..."):
                try:
                    resp = http_requests.post(
                        f"{API_BASE}/report/send",
                        json={"ticker": symbol, "email": email_input,
                              "start_date": str(start.date())},
                        timeout=90,
                    )
                    if resp.status_code == 200:
                        result = resp.json()
                        st.sidebar.success(f"✅ Report sent to {email_input}")
                        st.subheader(f"🤖 AI Analysis — {symbol}")
                        icons = {"bullish": "🟢", "bearish": "🔴", "neutral": "🟡"}
                        s = result.get("sentiment", "neutral")
                        col1, col2 = st.columns(2)
                        col1.metric("Price", f"${result.get('price', 'N/A')}")
                        col2.metric("Sentiment", f"{icons.get(s,'🟡')} {s.upper()}")
                        st.info(result.get("analysis", ""))
                    else:
                        st.sidebar.error(f"Error: {resp.json().get('detail', 'Unknown error')}")
                except Exception:
                    st.sidebar.error("Could not connect to API. Make sure the API server is running.")

    # Download data
    @st.cache_data(ttl=300)
    def fetch_data(ticker, start, end):
        raw = yf.download(ticker, start=start, end=end, auto_adjust=False, progress=False)
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)
        return raw.copy()

    data = fetch_data(symbol, start, end)
    if data.empty:
        st.error(f"No data found for ticker '{symbol}'.")
        st.stop()

    # Charts
    st.header(f"Adjusted Close Price — {symbol}")
    st.line_chart(data["Adj Close"])

    data["SMA"] = ta.SMA(data["Adj Close"], timeperiod=20)
    data["EMA"] = ta.EMA(data["Adj Close"], timeperiod=20)
    st.header(f"SMA vs EMA — {symbol}")
    st.line_chart(data[["Adj Close", "SMA", "EMA"]])

    data["upper_band"], data["middle_band"], data["lower_band"] = ta.BBANDS(data["Adj Close"], timeperiod=20)
    st.header(f"Bollinger Bands — {symbol}")
    st.line_chart(data[["Adj Close", "upper_band", "middle_band", "lower_band"]])

    data["macd"], data["macdsignal"], data["macdhist"] = ta.MACD(
        data["Adj Close"], fastperiod=12, slowperiod=26, signalperiod=9)
    st.header(f"MACD — {symbol}")
    st.line_chart(data[["macd", "macdsignal"]])

    data["CCI"] = ta.CCI(data["High"], data["Low"], data["Close"], timeperiod=14)
    st.header(f"CCI — {symbol}")
    st.line_chart(data["CCI"])

    data["RSI"] = ta.RSI(data["Adj Close"], timeperiod=14)
    st.header(f"RSI — {symbol}")
    st.line_chart(data["RSI"])

    data["OBV"] = ta.OBV(data["Adj Close"], data["Volume"]) / 10**6
    st.header(f"OBV (millions) — {symbol}")
    st.line_chart(data["OBV"])


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — RSI SCREENER
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔍 RSI Screener":

    st.title("🔍 RSI Screener")
    st.caption("Find oversold & overbought stocks across any market universe")

    st.sidebar.header("Screener Settings")

    universe = st.sidebar.selectbox(
        "Universe",
        ["sp500", "nasdaq", "nyse", "amex", "russell3000", "nse", "bse"],
        index=0,
    )
    oversold_thresh   = st.sidebar.slider("Oversold threshold",   10, 40, 30)
    overbought_thresh = st.sidebar.slider("Overbought threshold", 60, 90, 70)

    if st.sidebar.button("🚀 Run Screener"):
        with st.spinner(f"Scanning {universe.upper()} for RSI signals..."):
            try:
                resp = http_requests.get(
                    f"{API_BASE}/screener/rsi",
                    params={"universe": universe,
                            "oversold": oversold_thresh,
                            "overbought": overbought_thresh},
                    timeout=120,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    oversold   = data.get("oversold", [])
                    overbought = data.get("overbought", [])

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Universe",   universe.upper())
                    col2.metric("🟢 Oversold",   len(oversold))
                    col3.metric("🔴 Overbought", len(overbought))

                    st.markdown("---")

                    c1, c2 = st.columns(2)

                    with c1:
                        st.subheader("🟢 Oversold Stocks")
                        st.caption(f"RSI < {oversold_thresh} — Potential buy signals")
                        if oversold:
                            df_os = pd.DataFrame(oversold)
                            df_os.columns = ["Ticker", "RSI"]
                            df_os["Signal"] = "🟢 Oversold"
                            st.dataframe(df_os, use_container_width=True, hide_index=True)
                        else:
                            st.info("No oversold stocks found.")

                    with c2:
                        st.subheader("🔴 Overbought Stocks")
                        st.caption(f"RSI > {overbought_thresh} — Potential sell signals")
                        if overbought:
                            df_ob = pd.DataFrame(overbought)
                            df_ob.columns = ["Ticker", "RSI"]
                            df_ob["Signal"] = "🔴 Overbought"
                            st.dataframe(df_ob, use_container_width=True, hide_index=True)
                        else:
                            st.info("No overbought stocks found.")

                    # RSI explanation
                    st.markdown("---")
                    st.subheader("📚 What is RSI?")
                    st.markdown("""
| RSI Range | Meaning | Action |
|---|---|---|
| **0 – 30** | Oversold — stock may be undervalued | 🟢 Potential Buy |
| **30 – 70** | Normal range — no strong signal | ➡️ Hold / Watch |
| **70 – 100** | Overbought — stock may be overvalued | 🔴 Potential Sell |

> RSI (Relative Strength Index) measures the speed and magnitude of price changes.
> It's a momentum oscillator that ranges from 0 to 100.
                    """)

                else:
                    st.error(f"API error: {resp.json().get('detail', 'Unknown')}")
            except Exception as e:
                st.error(f"Could not connect to API. Make sure the API server is running at port 8000.")
    else:
        st.info("👈 Configure settings in the sidebar and click **Run Screener** to find signals.")

        st.markdown("""
### How it works
1. Select a market universe (S&P 500, NASDAQ, NSE etc.)
2. Set your RSI thresholds
3. Click Run — the screener checks RSI for up to 100 stocks
4. Results show oversold (buy signals) and overbought (sell signals)

### RSI Quick Reference
- **RSI < 30** → Stock is oversold → potential buying opportunity
- **RSI > 70** → Stock is overbought → potential selling opportunity
- **RSI 30–70** → Normal range, no strong signal
        """)
