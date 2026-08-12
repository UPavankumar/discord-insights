# Exaqube Analytics - Conversational Discord Intelligence & Plugin Architecture

A full-stack analytics platform built over a synthetic Discord activity dataset powered by FastAPI, PostgreSQL, an extensible agentic plugin system, real-time Server-Sent Events (SSE) streaming, and an interactive React frontend.

---

## ⚡ Prerequisites & Requirements

Before running the application, make sure you have:
1. **Docker & Docker Compose** (Recommended for 1-command startup)
2. **Node.js 20+** and **Python 3.11+** (Only needed if running locally without Docker)
3. Free LLM API Keys:
   - **Groq API Key** (100% Free): [console.groq.com/keys](https://console.groq.com/keys)
   - **Google Gemini API Key** (100% Free): [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

---

## 🚀 How to Run It (One-Command Docker Launch)

To bring up PostgreSQL, FastAPI backend, React web frontend, schema migrations, and full dataset initialization in one command:

```bash
docker compose up --build
```

Access the live application:
- 🌐 **Web Dashboard & Chat UI:** `http://localhost:3000`
- 📖 **Backend API Docs:** `http://localhost:8000/docs`
- 💚 **Health Check Endpoint:** `http://localhost:8000/health`

---

## 🔑 Environment Variables Setup

Create a `.env` file in the root directory (or use `.env.example`):

| Variable | Description | Free Tier / Link |
| :--- | :--- | :--- |
| `DATABASE_URL` | Async PostgreSQL connection string | `postgresql+asyncpg://exaqube:exaqube_dev@localhost:5432/exaqube` |
| `GROQ_API_KEY` | **100% Free** API key for Meta's Llama 3.3 70B model | [console.groq.com/keys](https://console.groq.com/keys) |
| `GEMINI_API_KEY` | **100% Free** API key for Google Gemini 2.5 Flash | [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) |
| `OPENAI_API_KEY` | OpenAI API key for GPT-4o-mini | Optional paid key |

---

## 💻 Alternative: Local Host Machine Setup (Without Docker)

If running directly on your host machine:

```bash
# 1. Start PostgreSQL container
docker compose up -d postgres

# 2. Setup Python environment and load dataset
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

## 📊 Dataset Scope & Scope Coverage

- **Coverage Period**: December 18, 2025 – June 16, 2026
- **Database Scale**: 10 Servers, 62 Channels, 2,775 Members, 1,810 Daily Server Stats, 6,878 Channel Stats, 5,000 Messages
- **Server Regions**: `us-east`, `us-west`, `europe`, `asia`, `brazil`

---

## 🛡️ Self-Healing Architecture & Fault Tolerance

1. **Pydantic Tool Parameter Alias Auto-Remapping**:
   - If an LLM passes `query`, `sql_query`, or `statement` instead of `sql`, `@model_validator` in `QueryInput` automatically maps it into `sql` before execution.
2. **Automatic Database Recovery**:
   - If PostgreSQL tables are missing or cleared, `QueryPlugin` catches table errors, initializes `schema.sql`, populates all 6 tables from CSV datasets, and transparently retries execution.
3. **Single-Occurrence Notifications**:
   - Provider failover badges (`⚡ Primary API limit reached...`) and unselected plugin tips display **ONCE** per transition to avoid cluttering chat history.
4. **Smart LLM Provider Chain**:
   - Groq (Llama 3.3 70B) $\rightarrow$ Google Gemini (gemini-2.5-flash) $\rightarrow$ OpenAI (gpt-4o-mini) $\rightarrow$ Offline Deterministic Engine (`FallbackNLProvider`).

---

## 🔌 How to Write a New Plugin

The plugin architecture is fully dynamic. Adding a new capability requires **writing one Python file inside `backend/app/plugins/` and nothing else**. You do **NOT** need to edit the agent orchestrator, alter system prompts, or register routes.

### Creating a Custom Plugin (e.g. `SummaryPlugin`)

1. Create a new file `backend/app/plugins/summary.py`.
2. Inherit from `Plugin` and define the LLM input schema using Pydantic:

```python
from pydantic import BaseModel, Field
from app.plugins.base import Plugin, PluginContext

class SummaryInput(BaseModel):
    text_content: str = Field(..., description="Text content to summarize")
    title: str = Field(..., description="Title for summary report")

class SummaryPlugin(Plugin):
    name = "summary"
    description = "Generates a structured executive summary from dataset details."
    input_schema = SummaryInput

    async def execute(self, arguments: SummaryInput, context: PluginContext) -> dict:
        return {
            "title": arguments.title,
            "summary": f"Executive summary generated for '{arguments.title}'.",
            "content_preview": arguments.text_content[:100],
        }
```

3. Save the file. On application startup, `discovery.py` automatically scans, instantiates, registers, and exposes `SummaryPlugin` to the LLM agent tool definitions.

---

## 🎯 Platform Features & Technical Architecture

1. **Dynamic Plugin Architecture**: `Plugin` abstract base class, `PluginContext`, `PluginError`, `PluginRegistry`, and package auto-discovery (`discovery.py`).
2. **SQL Query Plugin (`QueryPlugin`)**: Safe SQL execution with `sqlglot` AST validation, table whitelisting, Pydantic field alias auto-mapping, row limits (max 500), and 5-second statement timeouts.
3. **Visual Chart Plugin (`ChartPlugin`)**: Produces interactive chart specifications (`line`, `bar`, `pie`) with automatic type normalization and column key resolution.
4. **Agent Orchestrator & SSE Streaming**: Real-time SSE stage streaming (`reasoning`, `tool_call`, `tool_progress`, `result`, `prose`) with multi-turn tool composition.
5. **Interactive Web Frontend**: React + Vite UI featuring real-time streaming chat, fixed sticky top nav bar, responsive left plugin panel, interactive Chart.js visualizations, data table viewer, and persistent pinned dashboard.
6. **Automatic Lifespan Schema Initializer**: Automatically creates database tables and populates full synthetic Discord dataset on startup.

---

## 🛡️ Security & Defense Matrix

| Attack Vector / Risk | Defense Mechanism | Implementation Details |
| :--- | :--- | :--- |
| **SQL Injection / Malicious DDL** | `sqlglot` AST Validation | Strictly parses SQL AST into `exp.Select`. Rejects `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, and multi-statement queries (`query.py`). |
| **Non-Whitelisted Schema Access** | Table Whitelisting | Rejects any query accessing tables outside `servers`, `channels`, `members`, `daily_stats`, `channel_daily_stats`, `messages`. |
| **Database Privilege Escalation** | PostgreSQL Read-Only Role | Dedicated `exaqube_readonly` user created in `schema.sql` with restricted `SELECT` grants. |
| **Resource Exhaustion / Denial of Service** | Row Caps & Statement Timeout | Enforces `MAX_ROW_LIMIT = 500` and `statement_timeout = '5000ms'` per query execution. |
| **Prompt Injection via Chat Data** | Context Sandboxing | Query outputs are serialized into isolated tool result blocks rather than raw system instructions. |

---

## 🔮 Roadmap / Next Steps

1. **Export Plugins**: Add `.xlsx` (OpenPyXL) and `.pptx` (Python-PPTX) plugins adhering to the standard `Plugin` interface.
2. **Dashboard Persistence**: Move pinned dashboard items from client local storage to PostgreSQL user dashboard tables.
3. **Ollama Integration**: Add Ollama / vLLM local engine options in `providers.py`.
