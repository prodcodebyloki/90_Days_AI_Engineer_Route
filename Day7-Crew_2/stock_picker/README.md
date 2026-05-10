# StockPicker Crew — Day 7

Multi-agent CrewAI system that autonomously finds, researches, and picks the best stock to invest in for a given sector. Sends a push notification to the user with the final decision.

---

## How It Works

1. **Manager** receives the sector input and delegates tasks to the crew.
2. **Trending Company Finder** searches the latest news to find 2–3 trending companies in the sector.
3. **Financial Researcher** deep-dives each company — market position, outlook, investment potential.
4. **Stock Picker** reads the research, picks the best company, sends a push notification, and writes a detailed decision report.

All intermediate outputs are saved as structured JSON/Markdown files. Long-term memory (SQLite) and short-term/entity memory (RAG via OpenAI embeddings) let the crew avoid picking the same company twice across runs.

---

## Agents

| Agent | Model | Role | Tools | Memory |
|---|---|---|---|---|
| `manager` | `gpt-4o` | Orchestrates the crew via hierarchical delegation | — | — |
| `trending_company_finder` | `gpt-4o-mini` | Scans news to find 2–3 trending companies in `{sector}` | SerperDevTool | Yes |
| `financial_researcher` | `gpt-4o-mini` | Produces a deep-dive report on each trending company | SerperDevTool | — |
| `stock_picker` | `gpt-4o-mini` | Picks the best company, sends push notification, writes decision report | PushNotificationTool | Yes |

### Custom Tool — `PushNotificationTool`

Sends a real-time push notification via [Pushover](https://pushover.net) when the stock picker makes its final decision.

```python
# Requires in .env:
PUSHOVER_USER=<your_user_key>
PUSHOVER_TOKEN=<your_app_token>
```

---

## Workflow Diagram

```
User / main.py
     │
     │  inputs: { sector: "Technology", current_date: "..." }
     ▼
┌─────────────────────────────────────────────────────┐
│                     MANAGER                         │
│              (gpt-4o, hierarchical)                 │
│         Delegates tasks, monitors progress          │
└──────────────────────┬──────────────────────────────┘
                       │
          ┌────────────▼────────────┐
          │  TASK 1: find_trending_ │
          │       companies         │
          │                         │
          │  Agent: Trending        │
          │  Company Finder         │
          │  Tool:  SerperDevTool   │
          │  Out:   TrendingCompany │
          │         List (JSON)     │
          │  File:  output/         │
          │         trending_       │
          │         companies.json  │
          └────────────┬────────────┘
                       │  context passed down
          ┌────────────▼────────────┐
          │  TASK 2: research_      │
          │  trending_companies     │
          │                         │
          │  Agent: Financial       │
          │  Researcher             │
          │  Tool:  SerperDevTool   │
          │  Out:   TrendingCompany │
          │         ResearchList    │
          │         (JSON)          │
          │  File:  output/         │
          │         research_       │
          │         report.json     │
          └────────────┬────────────┘
                       │  context passed down
          ┌────────────▼────────────┐
          │  TASK 3: pick_best_     │
          │  company                │
          │                         │
          │  Agent: Stock Picker    │
          │  Tool:  PushNotifica-   │
          │         tionTool        │
          │  Out:   decision.md     │
          │  File:  output/         │
          │         decision.md     │
          └────────────┬────────────┘
                       │
          ┌────────────▼────────────┐
          │  Pushover Notification  │
          │  → sent to user phone   │
          └─────────────────────────┘
                       │
                  Final result
                 printed to CLI
```

### Memory Architecture

```
┌────────────────────────────────────────────┐
│                  Memory Layer              │
│                                            │
│  Long-Term (SQLite)                        │
│  └─ ./memory/long_term_memory_storage.db   │
│     Persists decisions across runs         │
│     Prevents picking same company twice    │
│                                            │
│  Short-Term (RAG / OpenAI embeddings)      │
│  └─ ./memory/  [vector store]              │
│     Current session context                │
│                                            │
│  Entity Memory (RAG / OpenAI embeddings)   │
│  └─ ./memory/  [vector store]              │
│     Tracks companies, tickers, reasons     │
└────────────────────────────────────────────┘
```

---

## Project Structure

```
stock_picker/
├── src/stock_picker/
│   ├── config/
│   │   ├── agents.yaml          # Agent definitions
│   │   └── tasks.yaml           # Task definitions
│   ├── tools/
│   │   ├── push_tool.py         # Pushover notification tool
│   │   └── custom_tool.py
│   ├── crew.py                  # Crew assembly + Pydantic output models
│   └── main.py                  # Entry point, sets sector input
├── knowledge/
│   └── user_preference.txt      # User context fed to agents
├── memory/                      # Auto-created: SQLite + RAG vector stores
├── output/                      # Auto-created: task output files
│   ├── trending_companies.json
│   ├── research_report.json
│   └── decision.md
└── pyproject.toml
```

---

## Setup

### Prerequisites

- Python `>=3.10, <3.14`
- [uv](https://docs.astral.sh/uv/) package manager

### 1. Install uv

```bash
pip install uv
```

### 2. Install dependencies

```bash
cd Day7-Crew_2/stock_picker
crewai install
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```bash
# LLM
OPENAI_API_KEY=sk-...

# Web search (news lookup)
SERPER_API_KEY=...

# Push notifications
PUSHOVER_USER=...
PUSHOVER_TOKEN=...
```

| Variable | Purpose | Get it from |
|---|---|---|
| `OPENAI_API_KEY` | Powers all agents (gpt-4o / gpt-4o-mini) | platform.openai.com |
| `SERPER_API_KEY` | Google search via SerperDev | serper.dev |
| `PUSHOVER_USER` | Your Pushover user key | pushover.net |
| `PUSHOVER_TOKEN` | Your Pushover app token | pushover.net |

### 4. Run

```bash
crewai run
```

Default sector is `Technology`. To change it, edit `src/stock_picker/main.py`:

```python
inputs = {
    'sector': 'Healthcare',   # change sector here
    "current_date": str(datetime.now())
}
```

---

## Output Files

| File | Content |
|---|---|
| `output/trending_companies.json` | Structured list of trending companies + tickers + reasons |
| `output/research_report.json` | Deep-dive analysis per company |
| `output/decision.md` | Final pick with rationale + rejected companies |

---

## Key Design Decisions

- **Hierarchical process** — Manager agent orchestrates; no hardcoded task order in code.
- **Pydantic output models** — Structured JSON enforced at task boundaries (`TrendingCompanyList`, `TrendingCompanyResearchList`).
- **Long-term memory** — SQLite persistence prevents re-picking the same company across separate `crewai run` invocations.
- **Push notification** — Real-time decision delivery via Pushover before the full report is written.

---

## Dependencies

```
crewai[tools]==1.14.4
```

Includes: `crewai-tools`, `pydantic`, `requests`, and all CrewAI memory/RAG dependencies.
