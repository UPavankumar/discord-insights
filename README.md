# Exaqube Analytics - Conversational Discord Intelligence Platform

**Exaqube Analytics** is an AI-powered conversational analytics application built over a synthetic Discord activity dataset. It empowers users to explore server metrics, channel statistics, member activity, and message volumes through natural language queries, visual interactive charts, executive summaries, and a persistent pinned dashboard.

---

## ✨ Features at a Glance

- **💬 Conversational AI Agent**: Ask questions in plain English, and the AI agent automatically writes read-only SQL queries, generates interactive charts, or creates executive summaries.
- **📊 Interactive Visual Charts**: Renders interactive Line, Bar, and Pie charts in real time using Chart.js.
- **🔌 Dynamic Plugin Architecture**: Modular plugin system (`QueryPlugin`, `ChartPlugin`, `SummaryPlugin`) allowing new capabilities to be added by dropping a single Python file into `backend/app/plugins/`.
- **🎛️ Left Plugin Manager Sidebar**: Select or deselect plugins on the fly with sticky bottom apply controls and single-occurrence tip notifications.
- **📌 Pinned Analytics Dashboard**: Pin any generated chart directly to a persistent dashboard for executive tracking.
- **🎨 Glassmorphism Responsive UI**: Modern dark theme with a 100% fixed top navigation bar, right-corner scrollbar, and fluid responsiveness down to 320px screen width.
- **⚡ Smart LLM Provider Chain**: Multi-provider failover chaining Groq (Llama 3.3 70B) $\rightarrow$ Google Gemini (gemini-2.5-flash) $\rightarrow$ OpenAI (gpt-4o-mini) $\rightarrow$ Offline Deterministic Engine.

---

## ⚡ Prerequisites

Before launching the application, ensure you have:
1. **Docker & Docker Compose** installed.
2. Free LLM API Keys:
   - **Groq API Key** (100% Free): [console.groq.com/keys](https://console.groq.com/keys)
   - **Google Gemini API Key** (100% Free): [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)


---

## 🚀 How to Run (1-Command Launch)

Start PostgreSQL, the FastAPI backend, the React web frontend, database schema migrations, and initial dataset load with **one command**:

```bash
docker compose up --build
```

### 🌐 Live Application URLs:
- **Web App Dashboard:** `http://localhost:3000`
- **Backend API Docs:** `http://localhost:8000/docs`
- **Health Check Endpoint:** `http://localhost:8000/health`

---

## 🔑 Environment Variables Setup

Create a `.env` file in the project root (or copy `.env.example`):

```bash
cp .env.example .env
```

| Variable | Description | Link / Default |
| :--- | :--- | :--- |
| `DATABASE_URL` | Async PostgreSQL connection string | `postgresql+asyncpg://exaqube:exaqube_dev@localhost:5432/exaqube` |
| `GROQ_API_KEY` | **100% Free** API key for Meta's Llama 3.3 70B model | [console.groq.com/keys](https://console.groq.com/keys) |
| `GEMINI_API_KEY` | **100% Free** API key for Google Gemini 2.5 Flash | [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) |
| `OPENAI_API_KEY` | OpenAI API key for GPT-4o-mini | Optional paid key |

---

## 💻 Local Development Setup (Without Docker)

If running directly on your host machine:

```bash
# 1. Start PostgreSQL container
docker compose up -d postgres

# 2. Setup Python environment & load dataset
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/load_data.py

# 3. Start Backend server (Terminal 1)
python -m uvicorn app.main:app --reload --port 8000

# 4. Start Frontend dev server (Terminal 2)
cd ../frontend
npm install
npm run dev
```

Open `http://localhost:3001` in your browser!

---

## 📊 Dataset Scope

The synthetic Discord dataset covers **6 months of activity** (Dec 18, 2025 – June 16, 2026):
- **10 Servers**: `us-east`, `us-west`, `europe`, `asia`, `brazil`
- **62 Channels**: Text and voice channels
- **2,775 Members**: User activity and join dates
- **1,810 Server Daily Stats**: Message counts and active member metrics
- **6,878 Channel Daily Stats**: Granular channel traffic breakdown
- **5,000 Messages**: Sample message records

---

## 🛡️ Security & Defense Matrix

| Risk / Attack Vector | Defense Mechanism | Implementation Details |
| :--- | :--- | :--- |
| **SQL Injection / DDL Mutation** | `sqlglot` AST Validation | Parses SQL into AST `exp.Select`. Rejects `DROP`, `DELETE`, `INSERT`, `UPDATE`, and multi-statement queries. |
| **Non-Whitelisted Schema Access** | Table Whitelisting | Rejects queries referencing tables outside `servers`, `channels`, `members`, `daily_stats`, `channel_daily_stats`, `messages`. |
| **Database Escalation** | Read-Only DB User | Restricted `exaqube_readonly` role in `schema.sql` with `SELECT`-only privileges. |
| **Resource Exhaustion** | Row Caps & Timeout | Enforces `MAX_ROW_LIMIT = 500` and `statement_timeout = '5000ms'`. |
| **LLM Parameter Errors** | Pydantic Alias Mapping | `@model_validator` automatically maps `query`, `sql_query`, or `statement` into `sql`. |

---

## 🔌 How to Create a New Plugin

Creating a new plugin requires **writing one Python file in `backend/app/plugins/`**. No manual route registration or orchestrator modification is needed.

```python
from pydantic import BaseModel, Field
from app.plugins.base import Plugin, PluginContext

class SummaryInput(BaseModel):
    text_content: str = Field(..., description="Text content to summarize")
    title: str = Field(..., description="Title for report")

class SummaryPlugin(Plugin):
    name = "summary"
    description = "Generates a structured executive summary from dataset details."
    input_schema = SummaryInput

    async def execute(self, arguments: SummaryInput, context: PluginContext) -> dict:
        return {
            "title": arguments.title,
            "summary": f"Executive summary generated for '{arguments.title}'.",
        }
```

On application boot, `discovery.py` automatically registers and exposes `SummaryPlugin` to the LLM agent tool definitions.
