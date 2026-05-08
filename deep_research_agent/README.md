# Deep Research Agent

A multi-agent pipeline that takes a research query, autonomously plans and executes web searches, synthesizes findings into a detailed report, and delivers it via email — all orchestrated through the OpenAI Agents SDK with structured outputs enforced by Pydantic.

---

## Tech Stack

| Library | Purpose |
|---|---|
| `openai-agents` | Agent orchestration, `Runner`, `trace`, `WebSearchTool`, `function_tool` |
| `pydantic` | Structured output schema validation (JSON → typed Python objects) |
| `gradio` | Browser UI for query input and report streaming |
| `sendgrid` | Email delivery of the final HTML report |
| `python-dotenv` | Loads API keys from `.env` |
| `asyncio` | Concurrent parallel web searches |
| `gpt-4o-mini` | LLM powering all four agents |

---

## What It Does

Given a natural language research query, the system:
1. Plans 5 targeted web search queries
2. Executes all searches in parallel
3. Synthesizes a 1000+ word markdown report
4. Emails the report as formatted HTML

---

## Workflow Diagram

```
User Query (Gradio UI)
        │
        ▼
┌─────────────────────┐
│   ResearchManager   │  ← orchestrates the full pipeline
└─────────────────────┘
        │
        ▼
┌─────────────────────┐     output_type=WebSearchPlan
│    PlannerAgent     │  ─────────────────────────────►  WebSearchPlan (Pydantic)
│    (gpt-4o-mini)    │     list[WebSearchItem(query, reason)]
└─────────────────────┘
        │
        │  5 x WebSearchItem
        ▼
┌─────────────────────┐     tool: WebSearchTool
│    SearchAgent      │  ─────────────────────────────►  raw web results
│    (gpt-4o-mini)    │     returns plain text summary
│  [runs in parallel] │
└─────────────────────┘
        │
        │  list[str] summaries
        ▼
┌─────────────────────┐     output_type=ReportData
│    WriterAgent      │  ─────────────────────────────►  ReportData (Pydantic)
│    (gpt-4o-mini)    │     short_summary, markdown_report, follow_up_questions
└─────────────────────┘
        │
        │  ReportData.markdown_report
        ▼
┌─────────────────────┐     tool: send_email (function_tool)
│    EmailAgent       │  ─────────────────────────────►  SendGrid API → inbox
│    (gpt-4o-mini)    │
└─────────────────────┘
        │
        ▼
  Markdown report streamed back to Gradio UI
```

---

## Folder Structure

```
deep_research_agent/
│
├── deep_research.py       # Entry point — Gradio UI, wires query to ResearchManager
├── research_manager.py    # Pipeline orchestrator — coordinates all agents in sequence
│
├── planner_agent.py       # Agent 1: plans 5 search queries; outputs WebSearchPlan
├── search_agent.py        # Agent 2: executes one web search; uses WebSearchTool
├── writer_agent.py        # Agent 3: synthesizes report; outputs ReportData
├── email_agent.py         # Agent 4: converts report to HTML and sends via SendGrid
│
└── __pycache__/           # Python bytecode cache (auto-generated, ignore)
```

---

## Step-by-Step Execution Flow

### Step 1 — User Submits Query (Gradio UI)
File: `deep_research.py`

- User types a research topic in the Gradio textbox
- Clicks **Run** or presses Enter
- `run(query)` async generator is called, yields status strings + final markdown to the UI in real time

### Step 2 — Plan Searches (PlannerAgent)
File: `planner_agent.py`

- `ResearchManager.plan_searches(query)` runs `PlannerAgent`
- System prompt instructs LLM to return exactly 5 search queries
- `output_type=WebSearchPlan` forces the LLM to respond in JSON matching the schema
- `Runner.run()` returns result; `result.final_output_as(WebSearchPlan)` deserializes JSON → `WebSearchPlan` Pydantic object

### Step 3 — Execute Searches in Parallel (SearchAgent)
File: `search_agent.py`

- `ResearchManager.perform_searches(search_plan)` spawns one `asyncio.Task` per `WebSearchItem`
- Each task calls `ResearchManager.search(item)` which runs `SearchAgent`
- `SearchAgent` has `tools=[WebSearchTool(...)]` and `tool_choice="required"` — it **must** call the web search tool
- Returns a plain text 2–3 paragraph summary (no structured output here)
- `asyncio.as_completed()` collects results as they finish, tracking progress

### Step 4 — Write Report (WriterAgent)
File: `writer_agent.py`

- `ResearchManager.write_report(query, search_results)` runs `WriterAgent`
- Input: original query + all search summaries concatenated
- `output_type=ReportData` enforces structured output with three fields
- `result.final_output_as(ReportData)` gives a typed `ReportData` object

### Step 5 — Send Email (EmailAgent)
File: `email_agent.py`

- `ResearchManager.send_email(report)` runs `EmailAgent` with `report.markdown_report` as input
- `EmailAgent` has a `@function_tool` decorated function `send_email(subject, html_body)`
- Agent decides subject line and converts markdown to HTML, then calls the tool
- `send_email` tool calls SendGrid API using `SENDGRID_API_KEY` from `.env`

### Step 6 — Stream Report to UI
- `report.markdown_report` is yielded last from the generator
- Gradio renders it as formatted markdown in the browser

---

## Handoff & Tool Usage Flow

```
ResearchManager (orchestrator)
    │
    ├── Runner.run(planner_agent, query)
    │       └── PlannerAgent
    │               LLM call → structured JSON output
    │               Parsed to: WebSearchPlan via Pydantic
    │
    ├── asyncio.gather (parallel)
    │   ├── Runner.run(search_agent, item_1)
    │   │       └── SearchAgent
    │   │               TOOL CALL → WebSearchTool (built-in)
    │   │               Returns: text summary
    │   ├── Runner.run(search_agent, item_2)
    │   │       └── ... (same)
    │   └── Runner.run(search_agent, item_N)  [up to 5]
    │
    ├── Runner.run(writer_agent, query + summaries)
    │       └── WriterAgent
    │               LLM call → structured JSON output
    │               Parsed to: ReportData via Pydantic
    │
    └── Runner.run(email_agent, markdown_report)
            └── EmailAgent
                    TOOL CALL → send_email() [function_tool]
                        └── SendGrid HTTP API → email delivered
```

---

## Structured Output: JSON → Pydantic

### How It Works

The OpenAI Agents SDK supports `output_type` on an `Agent`. When set, the SDK instructs the LLM to respond in JSON conforming to the schema derived from the Pydantic model. The LLM returns raw JSON. The SDK then calls `model.model_validate(json_data)` to construct the Pydantic object.

```python
# LLM returns this JSON:
{
  "searches": [
    {"reason": "...", "query": "latest AI safety research 2024"},
    {"reason": "...", "query": "OpenAI safety team findings"}
  ]
}

# SDK validates and wraps into Pydantic:
plan = WebSearchPlan(
    searches=[
        WebSearchItem(reason="...", query="latest AI safety research 2024"),
        WebSearchItem(reason="...", query="OpenAI safety team findings"),
    ]
)

# Access is typed and safe:
for item in plan.searches:
    print(item.query)   # full IDE autocomplete, type checking
```

The `final_output_as(ModelClass)` call on the result is the explicit deserialization step:

```python
result = await Runner.run(planner_agent, f"Query: {query}")
search_plan = result.final_output_as(WebSearchPlan)  # JSON → Pydantic object
```

### Pydantic Models in This Project

#### `WebSearchItem` — single search query unit
```python
class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important.")
    query: str  = Field(description="The search term to use for the web search.")
```

#### `WebSearchPlan` — container for all planned searches
```python
class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="A list of web searches to perform.")
```

#### `ReportData` — final structured research output
```python
class ReportData(BaseModel):
    short_summary:        str        = Field(description="2-3 sentence summary of findings.")
    markdown_report:      str        = Field(description="Full report in markdown format.")
    follow_up_questions:  list[str]  = Field(description="Suggested topics for further research.")
```

---

## Why Pydantic?

| Problem without Pydantic | How Pydantic solves it |
|---|---|
| LLM output is raw string/JSON — no type guarantees | Schema enforced at validation time; invalid JSON raises `ValidationError` |
| Accessing `result["searches"][0]["query"]` is brittle | `plan.searches[0].query` — typed, IDE-autocompleted, refactor-safe |
| Missing fields silently return `None` or `KeyError` | Required fields raise `ValidationError` immediately on parse |
| Passing raw dicts between agents causes runtime bugs | Typed objects make contracts between agents explicit |
| Field descriptions are scattered in prompts or comments | `Field(description=...)` keeps schema + documentation co-located |

Pydantic is not just a convenience here — it is the **contract layer** between LLM output and Python code. The `Field(description=...)` annotations also feed directly into the JSON schema sent to the LLM, guiding it to produce the right structure.

---

## Key Points to Note

1. **All agents use `gpt-4o-mini`** — fast, cheap, sufficient for planning, summarizing, and writing. Change model per agent if quality needs differ.

2. **Parallel search execution** — `asyncio.create_task` + `asyncio.as_completed` runs all 5 searches concurrently. Wall time ≈ slowest single search, not sum of all.

3. **`tool_choice="required"` on SearchAgent** — prevents the LLM from skipping the web search and answering from training data. Forces a real tool call every time.

4. **Tracing** — `gen_trace_id()` + `trace(...)` wraps the full run. Every agent call is visible at `platform.openai.com/traces`. Invaluable for debugging multi-agent flows.

5. **`@function_tool` decorator** — converts a plain Python function into an agent-callable tool. The docstring becomes the tool description sent to the LLM. No manual schema writing needed.

6. **Streaming via `async for`** — `ResearchManager.run()` is an async generator (`yield`). Gradio receives status updates and the final report incrementally, not as one blocked response.

7. **Environment variables** — `OPENAI_API_KEY`, `SENDGRID_API_KEY`, `EMAIL_FROM`, `EMAIL_TO` must be set in `.env`. `load_dotenv(override=True)` ensures `.env` values take precedence over shell env.

8. **No structured output on SearchAgent** — search summaries are plain text by design. Structure would add overhead with no benefit since they're just concatenated as context for the writer.

---

## Environment Setup

```bash
# Install dependencies
pip install openai-agents gradio sendgrid python-dotenv pydantic

# Create .env file
OPENAI_API_KEY=sk-...
SENDGRID_API_KEY=SG...
EMAIL_FROM=you@yourdomain.com
EMAIL_TO=recipient@example.com

# Run
python deep_research.py
```

---

## Required `.env` Keys

| Key | Source |
|---|---|
| `OPENAI_API_KEY` | platform.openai.com/api-keys |
| `SENDGRID_API_KEY` | app.sendgrid.com/settings/api_keys |
| `EMAIL_FROM` | Verified sender in SendGrid |
| `EMAIL_TO` | Recipient address |
