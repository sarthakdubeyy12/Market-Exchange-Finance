# n8n Workflows

## Setup Instructions

### 1. Install n8n
```bash
brew install node        # if Node.js not installed
npm install -g n8n
n8n start                # opens at http://localhost:5678
```

### 2. Get Groq API Key
- Go to https://console.groq.com
- Sign up (free)
- Create an API key
- In n8n: Settings → Credentials → Add Groq credential → paste key

### 3. Start the Finance-Master API
```bash
.venv/bin/uvicorn api.main:app --reload --port 8000
```

### 4. Import Workflow
- Open n8n at http://localhost:5678
- Click "+" → Import from file
- Select `n8n/workflows/daily_stock_analysis.json`
- Add your Groq credential to the Groq nodes
- Click "Execute Workflow" to test

---

## Available Workflows

| File | What it does |
|---|---|
| `daily_stock_analysis.json` | Runs every weekday 9am, fetches AAPL + TSLA data, sends to Groq LLM for analysis |

---

## Key API Endpoints Used

| Endpoint | Purpose |
|---|---|
| `GET /llm/summary/{ticker}` | All-in-one payload with indicators + sentiment + ready LLM prompt |
| `GET /stock/indicators/{ticker}` | Raw technical indicators |
| `GET /sentiment/news/{ticker}` | News headlines with sentiment scores |
| `GET /screener/rsi` | RSI screener across any market |
| `GET /screener/minervini` | Minervini SEPA screener |
