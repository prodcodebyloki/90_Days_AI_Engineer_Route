"""
LangGraph + LangSmith Starter Project
Market Intelligence Agent: fetches stock news, analyzes market mood, summarizes insights.

5-step build guide (read top to bottom):
  STEP 1 — Define State schema (Pydantic)
  STEP 2 — Define reducer (how messages accumulate in state)
  STEP 3 — Define nodes (stock_news_fetcher, market_mood_predictor, insight_summarizer)
  STEP 4 — Build graph: add nodes + define edges
  STEP 5 — Compile & run (LangSmith auto-traces via env vars)
"""

import os
import ssl
import certifi
import requests
from typing import Annotated, Optional
from pydantic import BaseModel
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# Load all keys from root .env (LANGSMITH_* vars auto-enable tracing)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"), override=True)

# SSL fix for corporate proxies / macOS cert issues
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
os.environ["SSL_CERT_FILE"] = certifi.where()

SERPER_API_KEY = os.getenv("SERPER_API_KEY")


# ─────────────────────────────────────────────
# STEP 1: State schema using Pydantic
# Pydantic enforces types; add_messages is the reducer for the messages field.
# ─────────────────────────────────────────────
class MarketState(BaseModel):
    # STEP 2: Reducer — add_messages appends new messages instead of overwriting.
    # Without this reducer, each node would replace messages entirely.
    messages: Annotated[list, add_messages] = []

    # Plain fields (no reducer needed — each node overwrites directly)
    ticker: str = ""                    # stock symbol user is researching
    news_headlines: list[str] = []      # raw headlines from Serper
    market_mood: Optional[str] = None   # bullish / bearish / neutral
    final_summary: Optional[str] = None


# ─────────────────────────────────────────────
# STEP 3a: Node 1 — Stock News Fetcher
# Hits Google Serper API to pull latest headlines for the ticker.
# ─────────────────────────────────────────────
def stock_news_fetcher(state: MarketState) -> dict:
    ticker = state.ticker or "AAPL"
    query = f"{ticker} stock news latest"

    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": query, "gl": "us", "hl": "en", "num": 5}

    try:
        resp = requests.post(url, json=payload, headers=headers, verify=certifi.where(), timeout=10)
        resp.raise_for_status()
        data = resp.json()
        headlines = [item["title"] for item in data.get("organic", [])[:5]]
    except Exception as e:
        headlines = [f"[Serper error: {e}]"]

    return {
        "news_headlines": headlines,
        "messages": [AIMessage(content=f"Fetched {len(headlines)} headlines for {ticker}.")]
    }


# ─────────────────────────────────────────────
# STEP 3b: Node 2 — Market Mood Predictor
# Sends headlines to LLM to classify sentiment: bullish / bearish / neutral.
# ─────────────────────────────────────────────
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def market_mood_predictor(state: MarketState) -> dict:
    headlines_text = "\n".join(f"- {h}" for h in state.news_headlines)

    prompt = f"""You are a financial analyst. Based on these headlines, classify overall market mood.
Reply with EXACTLY one word: bullish, bearish, or neutral.

Headlines:
{headlines_text}"""

    response = llm.invoke([SystemMessage(content="You are a concise financial analyst."),
                           HumanMessage(content=prompt)])
    mood = response.content.strip().lower()

    return {
        "market_mood": mood,
        "messages": [AIMessage(content=f"Market mood for {state.ticker}: {mood}")]
    }


# ─────────────────────────────────────────────
# STEP 3c: Node 3 — Insight Summarizer
# Combines headlines + mood into a short investor-ready summary.
# ─────────────────────────────────────────────
def insight_summarizer(state: MarketState) -> dict:
    headlines_text = "\n".join(f"- {h}" for h in state.news_headlines)

    prompt = f"""You are a financial analyst. Summarize the market situation for {state.ticker}.
Market mood: {state.market_mood}

Recent headlines:
{headlines_text}

Write a 3-sentence investor briefing."""

    response = llm.invoke([HumanMessage(content=prompt)])

    return {
        "final_summary": response.content,
        "messages": [AIMessage(content=response.content)]
    }


# ─────────────────────────────────────────────
# STEP 4: Build graph — add nodes and define edges
# Linear flow: START → fetch news → predict mood → summarize → END
# ─────────────────────────────────────────────
builder = StateGraph(MarketState)

# Add three nodes
builder.add_node("stock_news_fetcher", stock_news_fetcher)
builder.add_node("market_mood_predictor", market_mood_predictor)
builder.add_node("insight_summarizer", insight_summarizer)

# Define edges (sequential pipeline)
builder.add_edge(START, "stock_news_fetcher")
builder.add_edge("stock_news_fetcher", "market_mood_predictor")
builder.add_edge("market_mood_predictor", "insight_summarizer")
builder.add_edge("insight_summarizer", END)


# ─────────────────────────────────────────────
# STEP 5: Compile and run
# LangSmith traces automatically via LANGSMITH_* env vars — no extra code needed.
# ─────────────────────────────────────────────
graph = builder.compile()


if __name__ == "__main__":
    ticker = input("Enter stock ticker (e.g. NVDA, AAPL, TSLA): ").strip().upper() or "NVDA"

    initial_state = MarketState(
        ticker=ticker,
        messages=[HumanMessage(content=f"Analyze market for {ticker}")]
    )

    print(f"\nRunning market analysis for {ticker}...\n")
    result = graph.invoke(initial_state)

    print("=" * 50)
    print(f"Ticker      : {result['ticker']}")
    print(f"Market Mood : {result['market_mood']}")
    print(f"\nSummary:\n{result['final_summary']}")
    print("=" * 50)
    print(f"\nFull trace → https://smith.langchain.com/projects/{os.getenv('LANGSMITH_PROJECT')}")
