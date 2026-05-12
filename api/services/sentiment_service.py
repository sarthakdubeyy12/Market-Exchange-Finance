import requests
from bs4 import BeautifulSoup
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


analyzer = SentimentIntensityAnalyzer()


def _score_to_label(compound: float) -> str:
    if compound >= 0.05:
        return "bullish"
    elif compound <= -0.05:
        return "bearish"
    return "neutral"


def get_news_sentiment(ticker: str) -> dict:
    """
    Scrape latest news headlines from Finviz for a ticker
    and return VADER sentiment scores.
    """
    url = f"https://finviz.com/quote.ashx?t={ticker.upper()}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        news_table = soup.find(id="news-table")

        if not news_table:
            return {"ticker": ticker.upper(), "headlines": [], "overall": "neutral", "score": 0.0}

        headlines = []
        for row in news_table.findAll("tr"):
            a_tag = row.find("a")
            if a_tag:
                text    = a_tag.get_text()
                scores  = analyzer.polarity_scores(text)
                compound = round(scores["compound"], 4)
                headlines.append({
                    "headline":  text,
                    "sentiment": _score_to_label(compound),
                    "score":     compound,
                })

        if not headlines:
            return {"ticker": ticker.upper(), "headlines": [], "overall": "neutral", "score": 0.0}

        avg_score = round(sum(h["score"] for h in headlines) / len(headlines), 4)

        return {
            "ticker":    ticker.upper(),
            "headlines": headlines[:20],  # latest 20
            "overall":   _score_to_label(avg_score),
            "score":     avg_score,
            "count":     len(headlines),
        }

    except Exception as e:
        return {"ticker": ticker.upper(), "error": str(e), "overall": "neutral", "score": 0.0}
