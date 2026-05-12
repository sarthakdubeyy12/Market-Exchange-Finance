import smtplib
import os
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()


def send_analysis_email(to_email: str, ticker: str,
                        analysis_data: dict, charts: dict = None) -> bool:
    smtp_host     = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port     = int(os.getenv("SMTP_PORT", "587"))
    smtp_user     = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")

    if not smtp_user or not smtp_password:
        raise ValueError("SMTP_USER and SMTP_PASSWORD must be set in .env")

    subject = f"📊 {ticker.upper()} Market Report — {datetime.date.today().strftime('%B %d, %Y')}"
    html    = _build_html(ticker, analysis_data, charts or {})

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"Finance Master <{smtp_user}>"
    msg["To"]      = to_email
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to_email, msg.as_string())

    return True


def _signal_color(value, low, high):
    """Return color based on value range."""
    if value is None:
        return "#94a3b8"
    if value > high:
        return "#ef4444"
    if value < low:
        return "#22c55e"
    return "#f59e0b"


def _build_html(ticker: str, data: dict, charts: dict) -> str:
    ind       = data.get("indicators", {})
    sentiment = data.get("sentiment", "neutral")
    analysis  = data.get("analysis", "").replace("\n", "<br>")
    price     = data.get("price", "N/A")
    today     = datetime.date.today().strftime("%B %d, %Y")

    color_map = {"bullish": "#22c55e", "bearish": "#ef4444", "neutral": "#f59e0b"}
    sent_color = color_map.get(sentiment, "#f59e0b")
    sent_icon  = {"bullish": "📈", "bearish": "📉", "neutral": "➡️"}.get(sentiment, "➡️")

    rsi_val  = ind.get("rsi")
    rsi_color = _signal_color(rsi_val, 30, 70)
    rsi_label = "Oversold 🟢" if rsi_val and rsi_val < 30 else ("Overbought 🔴" if rsi_val and rsi_val > 70 else "Neutral 🟡")

    macd_val   = ind.get("macd", 0) or 0
    sig_val    = ind.get("signal", 0) or 0
    macd_cross = "Bullish Cross 🟢" if macd_val > sig_val else "Bearish Cross 🔴"

    chart_html = ""
    if charts.get("price_bb_rsi_macd"):
        chart_html = f"""
        <div style="margin: 24px 0;">
          <h3 style="color:#60a5fa; font-size:13px; text-transform:uppercase;
                     letter-spacing:1px; margin:0 0 12px 0;">
            📊 Price Chart — Bollinger Bands · RSI · MACD
          </h3>
          <img src="data:image/png;base64,{charts['price_bb_rsi_macd']}"
               style="width:100%; border-radius:8px; border:1px solid #1e293b;" />
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{ticker} Market Report</title>
</head>
<body style="margin:0; padding:0; background:#0a0f1e; font-family:'Segoe UI',Arial,sans-serif;">

<!-- Wrapper -->
<table width="100%" cellpadding="0" cellspacing="0"
       style="background:#0a0f1e; padding:30px 0;">
<tr><td align="center">
<table width="620" cellpadding="0" cellspacing="0"
       style="background:#0f172a; border-radius:16px; overflow:hidden;
              border:1px solid #1e293b; max-width:620px;">

  <!-- Header -->
  <tr>
    <td style="background:linear-gradient(135deg,#1e3a5f,#0f172a);
               padding:32px 32px 24px; text-align:center;">
      <p style="margin:0 0 4px; color:#60a5fa; font-size:12px;
                text-transform:uppercase; letter-spacing:2px;">Finance Master</p>
      <h1 style="margin:0; color:#e2e8f0; font-size:32px; font-weight:700;">
        {ticker.upper()}
      </h1>
      <p style="margin:8px 0 0; color:#94a3b8; font-size:13px;">{today}</p>
    </td>
  </tr>

  <!-- Greeting -->
  <tr>
    <td style="padding:24px 32px 0;">
      <div style="background:#1e293b; border-radius:10px; padding:18px 20px;
                  border-left:4px solid #60a5fa;">
        <p style="margin:0; color:#cbd5e1; font-size:14px; line-height:1.7;">
          👋 Hey! I'm your Finance Master assistant — here to help you make
          smarter investment decisions. Here's today's complete market analysis
          for <strong style="color:#60a5fa;">{ticker.upper()}</strong>.
          I've crunched the numbers, read the news, and asked the AI —
          so you don't have to. Let's dive in! 🚀
        </p>
      </div>
    </td>
  </tr>

  <!-- Price + Sentiment -->
  <tr>
    <td style="padding:20px 32px 0;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td width="48%" style="background:#1e293b; border-radius:10px;
                                  padding:20px; text-align:center;">
            <p style="margin:0 0 4px; color:#94a3b8; font-size:11px;
                      text-transform:uppercase; letter-spacing:1px;">Current Price</p>
            <p style="margin:0; color:#e2e8f0; font-size:30px; font-weight:700;">
              ${price}
            </p>
          </td>
          <td width="4%"></td>
          <td width="48%" style="background:#1e293b; border-radius:10px;
                                  padding:20px; text-align:center;">
            <p style="margin:0 0 4px; color:#94a3b8; font-size:11px;
                      text-transform:uppercase; letter-spacing:1px;">Market Sentiment</p>
            <p style="margin:0; color:{sent_color}; font-size:22px; font-weight:700;">
              {sent_icon} {sentiment.upper()}
            </p>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- Chart -->
  <tr>
    <td style="padding:20px 32px 0;">
      {chart_html}
    </td>
  </tr>

  <!-- Technical Indicators -->
  <tr>
    <td style="padding:20px 32px 0;">
      <h3 style="margin:0 0 14px; color:#60a5fa; font-size:13px;
                 text-transform:uppercase; letter-spacing:1px;">
        🔢 Technical Indicators — What the Numbers Say
      </h3>

      <!-- RSI -->
      <div style="background:#1e293b; border-radius:8px; padding:14px 16px;
                  margin-bottom:10px; border-left:3px solid {rsi_color};">
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td>
              <p style="margin:0; color:#94a3b8; font-size:11px;">RSI (14) — Relative Strength Index</p>
              <p style="margin:4px 0 0; color:#e2e8f0; font-size:20px; font-weight:700;">
                {round(rsi_val, 2) if rsi_val else 'N/A'}
              </p>
            </td>
            <td align="right">
              <span style="background:{rsi_color}22; color:{rsi_color};
                           padding:4px 10px; border-radius:20px; font-size:12px;
                           font-weight:600;">{rsi_label}</span>
            </td>
          </tr>
        </table>
        <p style="margin:8px 0 0; color:#64748b; font-size:11px;">
          💡 RSI below 30 = oversold (potential buy). Above 70 = overbought (potential sell).
          Between 30–70 = normal trading range.
        </p>
      </div>

      <!-- MACD -->
      <div style="background:#1e293b; border-radius:8px; padding:14px 16px;
                  margin-bottom:10px; border-left:3px solid #60a5fa;">
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td>
              <p style="margin:0; color:#94a3b8; font-size:11px;">MACD — Moving Average Convergence Divergence</p>
              <p style="margin:4px 0 0; color:#e2e8f0; font-size:20px; font-weight:700;">
                {round(ind.get('macd', 0) or 0, 4)}
                <span style="color:#94a3b8; font-size:13px; font-weight:400;">
                  / Signal: {round(ind.get('signal', 0) or 0, 4)}
                </span>
              </p>
            </td>
            <td align="right">
              <span style="background:#1e3a5f; color:#60a5fa;
                           padding:4px 10px; border-radius:20px; font-size:12px;
                           font-weight:600;">{macd_cross}</span>
            </td>
          </tr>
        </table>
        <p style="margin:8px 0 0; color:#64748b; font-size:11px;">
          💡 When MACD crosses above signal line = bullish momentum.
          Below signal line = bearish momentum.
        </p>
      </div>

      <!-- CCI + SMA + EMA row -->
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td width="32%" style="background:#1e293b; border-radius:8px;
                                  padding:12px; text-align:center;">
            <p style="margin:0; color:#94a3b8; font-size:10px; text-transform:uppercase;">CCI (14)</p>
            <p style="margin:6px 0 0; color:#e2e8f0; font-size:18px; font-weight:700;">
              {round(ind.get('cci', 0) or 0, 1)}
            </p>
            <p style="margin:4px 0 0; color:#64748b; font-size:10px;">
              {'Overbought' if (ind.get('cci') or 0) > 100 else 'Oversold' if (ind.get('cci') or 0) < -100 else 'Normal'}
            </p>
          </td>
          <td width="2%"></td>
          <td width="32%" style="background:#1e293b; border-radius:8px;
                                  padding:12px; text-align:center;">
            <p style="margin:0; color:#94a3b8; font-size:10px; text-transform:uppercase;">SMA (14)</p>
            <p style="margin:6px 0 0; color:#e2e8f0; font-size:18px; font-weight:700;">
              ${round(ind.get('sma', 0) or 0, 2)}
            </p>
            <p style="margin:4px 0 0; color:#64748b; font-size:10px;">Simple Moving Avg</p>
          </td>
          <td width="2%"></td>
          <td width="32%" style="background:#1e293b; border-radius:8px;
                                  padding:12px; text-align:center;">
            <p style="margin:0; color:#94a3b8; font-size:10px; text-transform:uppercase;">EMA (14)</p>
            <p style="margin:6px 0 0; color:#e2e8f0; font-size:18px; font-weight:700;">
              ${round(ind.get('ema', 0) or 0, 2)}
            </p>
            <p style="margin:4px 0 0; color:#64748b; font-size:10px;">Exp Moving Avg</p>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- AI Analysis -->
  <tr>
    <td style="padding:20px 32px 0;">
      <div style="background:#1e293b; border-radius:10px; padding:20px;">
        <h3 style="margin:0 0 14px; color:#60a5fa; font-size:13px;
                   text-transform:uppercase; letter-spacing:1px;">
          🤖 AI Analysis — Powered by LLaMA 3.3
        </h3>
        <div style="color:#cbd5e1; font-size:14px; line-height:1.8;">
          {analysis}
        </div>
      </div>
    </td>
  </tr>

  <!-- Glossary -->
  <tr>
    <td style="padding:20px 32px 0;">
      <div style="background:#0f172a; border:1px solid #1e293b;
                  border-radius:10px; padding:18px 20px;">
        <h3 style="margin:0 0 12px; color:#f59e0b; font-size:12px;
                   text-transform:uppercase; letter-spacing:1px;">
          📚 Quick Glossary — Key Terms Explained
        </h3>
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td style="padding:4px 0; color:#94a3b8; font-size:12px; width:30%;">
              <strong style="color:#e2e8f0;">RSI</strong>
            </td>
            <td style="padding:4px 0; color:#64748b; font-size:12px;">
              Measures momentum. 0–30 = oversold, 70–100 = overbought
            </td>
          </tr>
          <tr>
            <td style="padding:4px 0; color:#94a3b8; font-size:12px;">
              <strong style="color:#e2e8f0;">MACD</strong>
            </td>
            <td style="padding:4px 0; color:#64748b; font-size:12px;">
              Trend indicator. Crossover above signal = buy signal
            </td>
          </tr>
          <tr>
            <td style="padding:4px 0; color:#94a3b8; font-size:12px;">
              <strong style="color:#e2e8f0;">Bollinger Bands</strong>
            </td>
            <td style="padding:4px 0; color:#64748b; font-size:12px;">
              Volatility bands. Price near upper = overbought, near lower = oversold
            </td>
          </tr>
          <tr>
            <td style="padding:4px 0; color:#94a3b8; font-size:12px;">
              <strong style="color:#e2e8f0;">CCI</strong>
            </td>
            <td style="padding:4px 0; color:#64748b; font-size:12px;">
              Above +100 = overbought, below -100 = oversold
            </td>
          </tr>
          <tr>
            <td style="padding:4px 0; color:#94a3b8; font-size:12px;">
              <strong style="color:#e2e8f0;">SMA / EMA</strong>
            </td>
            <td style="padding:4px 0; color:#64748b; font-size:12px;">
              Moving averages. Price above = uptrend, below = downtrend
            </td>
          </tr>
          <tr>
            <td style="padding:4px 0; color:#94a3b8; font-size:12px;">
              <strong style="color:#e2e8f0;">OBV</strong>
            </td>
            <td style="padding:4px 0; color:#64748b; font-size:12px;">
              Rising OBV = buying pressure. Falling = selling pressure
            </td>
          </tr>
        </table>
      </div>
    </td>
  </tr>

  <!-- Disclaimer -->
  <tr>
    <td style="padding:20px 32px 30px;">
      <p style="margin:0; color:#334155; font-size:11px; text-align:center;
                line-height:1.6;">
        ⚠️ This report is for informational purposes only and does not constitute
        financial advice. Always do your own research before making investment decisions.<br>
        Generated by <strong style="color:#475569;">Finance Master</strong> ·
        Powered by Groq LLaMA 3.3 · {today}
      </p>
    </td>
  </tr>

</table>
</td></tr>
</table>

</body>
</html>"""
