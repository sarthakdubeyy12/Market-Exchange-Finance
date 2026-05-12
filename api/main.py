from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import stock, screener, sentiment, llm, report

app = FastAPI(
    title="Finance-Master API",
    description="""
    REST API for stock market data, technical indicators, screeners, and sentiment analysis.
    Built to integrate with n8n automation workflows and LLM pipelines.
    """,
    version="1.0.0",
)

# Allow all origins — tighten this in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(stock.router)
app.include_router(screener.router)
app.include_router(sentiment.router)
app.include_router(llm.router)
app.include_router(report.router)


@app.get("/", tags=["Health"])
def root():
    return {
        "status":  "ok",
        "message": "Finance-Master API is running",
        "docs":    "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
