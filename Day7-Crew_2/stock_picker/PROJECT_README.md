# Stock Picker — Multi-Agent AI Crew

A multi-agent AI system that researches trending companies in a given sector and recommends the best stock pick. Built with CrewAI's sequential crew pattern.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent Framework | [CrewAI](https://docs.crewai.com) `1.14.4` |
| LLM | OpenAI `gpt-4o-mini` (agents) / `gpt-4o` (manager) |
| Package Manager | [uv](https://docs.astral.sh/uv/) |
| Config Format | YAML (`agents.yaml`, `tasks.yaml`) |
| Python | `>=3.10, <3.14` |

---

## Project Structure

```
stock_picker/
├── src/stock_picker/
│   ├── config/
│   │   ├── agents.yaml        # Agent definitions with dynamic {placeholders}
│   │   └── tasks.yaml         # Task definitions with dynamic {placeholders}
│   ├── tools/
│   │   ├── custom_tool.py     # Base template for custom tools
│   │   └── push_tool.py       # Push notification tool (stub)
│   ├── crew.py                # Crew wiring — agents, tasks, process
│   └── main.py                # Entry point — injects runtime inputs
├── knowledge/
│   └── user_preference.txt    # User context for knowledge-aware agents
├── .env                       # API keys
└── pyproject.toml
```

---

## Agents

Defined in `src/stock_picker/config/agents.yaml`. All agents use `openai/gpt-4o-mini` except the manager.

| Agent | Role | Responsibility |
|---|---|---|
| `trending_company_finder` | Financial News Analyst in `{sector}` | Scans latest news, surfaces 2–3 trending companies |
| `financial_researcher` | Senior Financial Researcher | Deep-dives each trending company, produces analysis reports |
| `stock_picker` | Stock Picker from Research | Synthesizes research, selects single best investment candidate |
| `manager` | Project Manager (`gpt-4o`) | Delegates tasks across agents to achieve the investment goal |

---

## Execution Flow

```
main.py
  └─ inputs = { sector, current_date }
       └─ StockPicker().crew().kickoff(inputs)
            │
            ├─ [Task 1] research_task  → researcher agent
            │     Finds trending companies in {sector}
            │     Output: bullet-point research list
            │
            └─ [Task 2] reporting_task → reporting_analyst agent
                  Expands research into full sections
                  Output: report.md  (markdown file saved to disk)
```

Process type: **sequential** — each task receives prior task output as context.

---

## Tools

### Built-in (via `crewai[tools]`)
CrewAI agents can use built-in tools like `SerperDevTool` (web search), `ScrapeWebsiteTool`, `FileReadTool`, etc. Install extras with:
```bash
uv add crewai-tools
```

### Custom Tool Template — `tools/custom_tool.py`
Scaffold for project-specific tools using `BaseTool`:

```python
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class MyCustomToolInput(BaseModel):
    argument: str = Field(..., description="What the agent passes in.")

class MyCustomTool(BaseTool):
    name: str = "tool_name"
    description: str = "Describe what this tool does so agents know when to use it."
    args_schema: type[BaseModel] = MyCustomToolInput

    def _run(self, argument: str) -> str:
        # your logic here
        return "result"
```

Attach a tool to an agent in `crew.py`:
```python
@agent
def researcher(self) -> Agent:
    return Agent(
        config=self.agents_config['researcher'],
        tools=[MyCustomTool()],
        verbose=True
    )
```

---

## How Prompts Are Managed

CrewAI uses **Jinja-style `{variable}` placeholders** in YAML config files. Placeholders are resolved at runtime when `crew.kickoff(inputs={...})` is called — no prompt strings are hardcoded.

### The Three Layers

**Layer 1 — `agents.yaml`** defines agent identity with placeholders:
```yaml
trending_company_finder:
  role: >
    Financial News Analyst that finds trending companies in {sector}
  goal: >
    Find 2-3 companies that are trending in the news for further research.
    Always pick new companies. Don't pick the same company twice.
  backstory: >
    You are a market expert with a knack for picking out the most
    interesting companies based on latest news.
```

**Layer 2 — `tasks.yaml`** defines task instructions with placeholders:
```yaml
research_task:
  description: >
    Conduct a thorough research about {topic}
    Make sure you find any interesting and relevant information given
    the current year is {current_year}.
  expected_output: >
    A list with 10 bullet points of the most relevant information about {topic}
  agent: researcher
```

**Layer 3 — `main.py`** is the single injection point — all placeholder values go here:
```python
inputs = {
    'sector': 'Technology',
    'current_date': str(datetime.now())
}
StockPicker().crew().kickoff(inputs=inputs)
```

### Dynamic Injection Example

At kickoff, CrewAI resolves every `{placeholder}` across all YAML before sending anything to the LLM:

```
# Static template in agents.yaml:
role: "Financial News Analyst that finds trending companies in {sector}"

# What the agent actually receives after injection:
role: "Financial News Analyst that finds trending companies in Technology"
```

Switching sector requires changing one value in `main.py` — nothing else:

```python
# Before — Technology sector
inputs = {
    'sector': 'Technology',
    'current_date': '2026-05-10 09:00:00'
}

# After — Healthcare sector (one change, entire crew reoriented)
inputs = {
    'sector': 'Healthcare',
    'current_date': '2026-05-10 09:00:00'
}
```

The agent role, goal, backstory, task description, and expected output all update automatically — the crew is fully parameterized from a single dict.

---

## Knowledge Base

`knowledge/user_preference.txt` provides user-level context to agents:

```
User name is John Doe.
User is an AI Engineer.
User is interested in AI Agents.
User is based in San Francisco, California.
```

Wire it into the crew with:
```python
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource

source = TextFileKnowledgeSource(file_paths=["knowledge/user_preference.txt"])
crew = Crew(..., knowledge_sources=[source])
```

---

## Environment Setup

```bash
# 1. Install uv (if not already)
pip install uv

# 2. Navigate to project
cd stock_picker

# 3. Install dependencies
crewai install
# or: uv sync

# 4. Set API keys in .env
OPENAI_API_KEY=sk-...
SERPER_API_KEY=...   # if using SerperDevTool for web search
```

---

## Running

```bash
# Default run (sector: Technology)
crewai run

# Or directly
uv run python src/stock_picker/main.py
```

Output written to `report.md` in the project root.

---

## Extending the Crew

| Goal | Where to change |
|---|---|
| Add a new agent | `agents.yaml` + new `@agent` method in `crew.py` |
| Add a new task | `tasks.yaml` + new `@task` method in `crew.py` |
| Change sector at runtime | Edit `inputs['sector']` in `main.py` |
| Add web search | `uv add crewai-tools`, attach `SerperDevTool()` to agent |
| Switch to hierarchical process | `process=Process.hierarchical, manager_llm="openai/gpt-4o"` in `crew.py` |
| Persist memory across runs | `memory=True` on `Crew(...)` |
