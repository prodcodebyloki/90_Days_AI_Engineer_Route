# 🤖 90 Days of AI Engineering

> A Product Manager's journey to becoming an AI Engineer — one day at a time.

[![Days Completed](https://img.shields.io/badge/Days%20Completed-2-blue)](https://github.com/prodcodebyloki/90_Days_AI_Engineer_Route)
[![Language](https://img.shields.io/badge/Language-Python%203.12-yellow)](https://python.org)
[![Follow on YouTube](https://img.shields.io/badge/YouTube-Subscribe-red)](https://youtube.com/@prodcodebyloki)
---

## 🎯 The Challenge

I'm a **Product Manager** taking on a 90-day challenge to learn the skills of an AI Engineer from scratch. No shortcuts. No prior engineering degree. Just daily learning, building, and documenting the entire journey.

Every single day gets posted on YouTube — the wins, the confusion, and the failures.

---

## 📂 Project Structure

```
90_Days_AI_Engineer_Route/
├── Day2/
│   ├── salesdev_rep.ipynb            # 3 AI sales agents with different personas
│   ├── salesdev_rep_guardrail.ipynb  # Sales agents + input guardrails
│   └── day2.ipynb                    # Day 2 experiments
├── .env.example                      # Template for environment variables
├── .gitignore
├── pyproject.toml
└── README.md
```

---

## 🗓️ Progress Log

| Day | Topic | What I Built |
|-----|-------|-------------|
| 🗓️ Day 2 | AI Agents + Personas | 3 sales agents (Professional, Humorous, Concise) that write cold emails using OpenAI Agents SDK + guardrails |

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| 🐍 Python 3.12 | Core language |
| 🤖 OpenAI Agents SDK | Agent framework |
| 🧠 GPT-4o-mini | LLM backbone |
| 🔗 LangChain / LangGraph | Agent orchestration |
| 🦾 AutoGen | Multi-agent experiments |
| 🧩 Anthropic Claude | Alternative LLM |
| 📧 SendGrid | Email sending |
| 🎨 Gradio | UI for demos |
| 🗺️ MCP | Model Context Protocol tools |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Setup

```bash
# Clone the repo
git clone https://github.com/prodcodebyloki/90_Days_AI_Engineer_Route.git
cd 90_Days_AI_Engineer_Route

# Install dependencies with uv
uv sync

# Or with pip
pip install -r requirments.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your API keys
```

### Environment Variables

Create a `.env` file (never commit this!):

```env
OPENAI_API_KEY=your_openai_key_here
SENDGRID_API_KEY=your_sendgrid_key_here
EMAIL_FROM=your_email@example.com
EMAIL_TO=recipient@example.com
```

---

## 📚 What to Expect

- 📦 **Daily hands-on projects** — real code, not toy examples
- 💥 **Real learning** — including the bugs and failures
- 🔧 **Tools covered** — agents, LLMs, RAG, MCP, multi-agent systems, and more
- 🧠 **A PM's perspective** — how an AI Engineer thinks vs how a PM thinks

---

## 👥 Who Is This For?

- 🧑‍💼 Product Managers curious about AI Engineering
- 🌱 Beginners wanting to learn AI/ML from a non-traditional background
- 🔨 Builders who want a real, unfiltered learning journey
- 👀 Anyone who learns better by watching someone else figure it out

---

## 📺 Follow Along

Subscribe on YouTube to catch every day of the journey as it happens. New video every single day.

---

## ⚠️ Security Note

Never commit your `.env` file. Add secrets via environment variables only. See `.env.example` for the required keys.
