# 🤖 AI Developer Productivity Platform

A production-grade, multi-agent AI platform that simulates workflows used inside modern engineering organizations — built as a portfolio project targeting Amazon ML School, Microsoft, Google, Uber, and AI engineering internships.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI Dev Productivity Platform                   │
│                                                                   │
│  ┌──────────────────┐    ┌──────────────────────────────────────┐│
│  │   React Frontend  │    │          FastAPI Backend             ││
│  │  (Vite + JSX)    │◄──►│                                      ││
│  │                  │    │  ┌──────────┐  ┌──────────────────┐  ││
│  │ • Dashboard      │    │  │ Prompt   │  │  Multi-Agent     │  ││
│  │ • Prompt Lab     │    │  │ Engine   │  │  Bug Triage      │  ││
│  │ • Bug Triage     │    │  │          │  │                  │  ││
│  │ • PR Review      │    │  │ baseline │  │ Agent1: Analyzer │  ││
│  │ • Error Analyzer │    │  │ cot      │  │ Agent2: Classify │  ││
│  │ • Experiments    │    │  │ few-shot │  │ Agent3: RootCause│  ││
│  │ • Context Files  │    │  │ negative │  │ Agent4: FixGen   │  ││
│  └──────────────────┘    │  │ reflect  │  │ Agent5: Reporter │  ││
│                           │  │ context  │  └──────────────────┘  ││
│                           │  └──────────┘                        ││
│                           │  ┌──────────┐  ┌──────────────────┐  ││
│                           │  │Evaluation│  │  Context Manager │  ││
│                           │  │Framework │  │  (CLAUDE.md-like)│  ││
│                           │  │          │  │                  │  ││
│                           │  │correctns │  │project_overview  │  ││
│                           │  │relevance │  │architecture      │  ││
│                           │  │hallucin  │  │coding_standards  │  ││
│                           │  │cost/lat  │  │api_docs          │  ││
│                           │  └──────────┘  │team_guidelines   │  ││
│                           │                └──────────────────┘  ││
│                           │  ┌──────────────────────────────────┐ ││
│                           │  │     Claude API (Anthropic)        │ ││
│                           │  │  claude-sonnet-4-20250514         │ ││
│                           │  └──────────────────────────────────┘ ││
│                           │  ┌─────────────────────────────────┐  ││
│                           │  │     SQLite / PostgreSQL          │  ││
│                           │  │  (experiments, bugs, PRs, evals) │  ││
│                           │  └─────────────────────────────────┘  ││
│                           └──────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
ai-dev-platform/
├── backend/
│   ├── main.py                    # FastAPI app + all API routes
│   ├── agents/
│   │   ├── bug_triage.py          # 5-agent LangChain-style pipeline
│   │   ├── pr_reviewer.py         # PR diff analysis agent
│   │   └── error_fix.py           # 2-stage error→fix synthesis
│   ├── core/
│   │   └── llm_client.py          # Claude API client + mock fallback
│   ├── database/
│   │   ├── db.py                  # SQLite connection + seeding
│   │   └── schema.sql             # Full DB schema (9 tables)
│   ├── evaluation/
│   │   └── evaluator.py           # Scoring pipeline (5 metrics)
│   ├── models/
│   │   └── schemas.py             # Pydantic request/response models
│   ├── prompts/
│   │   └── templates.py           # 6 prompt strategy templates
│   └── utils/
│       └── context_manager.py     # CLAUDE.md-inspired context loader
│
├── frontend/
│   ├── index.html
│   └── src/
│       ├── main.jsx               # React entry point
│       └── App.jsx                # Complete SPA (all 7 pages)
│
├── context/                       # Project context files (auto-loaded)
│   ├── project_overview.md
│   ├── architecture.md
│   ├── coding_standards.md
│   ├── api_docs.md
│   └── team_guidelines.md
│
├── tests/
│   ├── unit/
│   │   ├── test_evaluator.py      # 25+ unit tests for scoring logic
│   │   └── test_agents.py         # 20+ unit tests for agent workflows
│   └── integration/
│       └── test_api.py            # 30+ integration tests for all endpoints
│
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── nginx.conf
│
├── .github/workflows/
│   └── ci.yml                     # GitHub Actions CI/CD pipeline
│
├── docker-compose.yml
├── requirements.txt
├── pytest.ini
└── README.md
```

---

## 🚀 Quick Start

### Option 1: Local Development (No Docker)

**Backend:**
```bash
# Clone and set up
cd ai-dev-platform
pip install -r requirements.txt

# Set your API key (optional — demo mode works without it)
export ANTHROPIC_API_KEY=your_key_here

# Start backend
uvicorn backend.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

### Option 2: Docker Compose

```bash
# Copy env template
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Start everything
docker compose up -d

# View logs
docker compose logs -f backend

# Access: http://localhost:3000
```

### Option 3: Demo Mode (No API Key)
The platform runs fully in **demo mode** without any API keys. All LLM calls return realistic mock responses that demonstrate the workflows. Perfect for portfolio demos.

---

## 🔑 Environment Variables

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...          # Claude API (optional - demo mode if absent)
OPENAI_API_KEY=sk-...                 # OpenAI (optional, future integration)
DATABASE_URL=sqlite:///./data/dev_platform.db  # SQLite default
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/prompts/test` | Test all 6 prompt strategies |
| `GET` | `/prompts/experiments` | List past experiments |
| `GET` | `/prompts/experiments/{id}` | Get experiment detail |
| `POST` | `/bugs/analyze` | Run 5-agent bug triage |
| `GET` | `/bugs/list` | List bug reports |
| `POST` | `/pr/review` | AI PR code review |
| `GET` | `/pr/list` | List reviewed PRs |
| `POST` | `/errors/fix` | Error-to-fix synthesis |
| `POST` | `/evaluations/run` | Run evaluation batch |
| `GET` | `/evaluations/history` | Evaluation history |
| `GET` | `/evaluations/strategy-comparison` | Strategy metrics |
| `GET` | `/dashboard/stats` | Platform dashboard stats |
| `GET` | `/context/{project_id}` | Get project context files |
| `POST` | `/context` | Save/update context file |
| `GET` | `/agents/executions` | Agent execution history |

### Example: Test Prompt Strategies
```bash
curl -X POST http://localhost:8000/prompts/test \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Review this function for SQL injection vulnerabilities",
    "code": "def get_user(id): return db.execute(\"SELECT * FROM users WHERE id=\" + id)",
    "strategies": ["baseline", "chain_of_thought", "negative_example"],
    "model": "claude-sonnet-4-20250514"
  }'
```

### Example: Analyze Bug
```bash
curl -X POST http://localhost:8000/bugs/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "title": "NullPointerException in UserService.getProfile()",
    "description": "500 errors on /profile since deploy v2.4.1",
    "stack_trace": "at UserService.java:87\n  at ProfileController.java:42"
  }'
```

---

## 🧪 Running Tests

```bash
# All tests
pytest tests/ -v

# Unit tests only (fast, no API calls)
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# With coverage report
pytest tests/ --cov=backend --cov-report=html
open htmlcov/index.html

# Specific test file
pytest tests/unit/test_evaluator.py -v -k "TestOverallScore"
```

**Test Coverage Targets:**
- Overall: ≥80%
- Evaluation module: ≥90%
- Agent workflows: ≥85%
- API endpoints: ≥80%

---

## 🧠 Modules Deep Dive

### Module 1: Prompt Engineering Lab
Tests 6 strategies on any coding task:

| Strategy | Key Technique | Best For |
|----------|--------------|----------|
| `baseline` | Direct instruction | Quick tasks |
| `chain_of_thought` | Step-by-step reasoning | Complex analysis |
| `few_shot` | 3 high-quality examples | Consistent format |
| `negative_example` | Explicit anti-patterns | Reducing errors |
| `self_reflection` | Two-pass critique | Accuracy boost |
| `context_window` | Full project context | Context-aware review |

Metrics: Correctness · Relevance · Completeness · Consistency · Hallucination Rate · Cost · Latency

### Module 2: Multi-Agent Bug Triage
5 specialized agents in a sequential pipeline:
```
BugReportAnalyzerAgent → RegressionClassifierAgent → RootCauseIdentifierAgent → FixGeneratorAgent → TechnicalReportWriterAgent
```
Each agent passes structured JSON to the next, simulating LangChain agent handoffs.

### Module 3: AI PR Reviewer
Analyzes git diffs for: SQL injection · Hardcoded secrets · N+1 queries · Missing error handling · Style violations · Security issues

### Module 4: Error-to-Fix Synthesis
Two-stage chain: `Error → [Stage 1: Root Cause Analysis] → [Stage 2: Fix Generation] → Confident Fix`

### Module 5: Context Management System
CLAUDE.md-inspired: 5 markdown files auto-loaded into the `context_window` prompt strategy, giving the AI full project awareness.

### Module 6 & 7: Evaluation + Experiment Tracking
Scores every LLM output on 5 dimensions. Stores all results with model, tokens, cost, latency. Tracks strategy performance over time.

---

## 🐳 Production Deployment

```bash
# Build and tag images
docker build -f docker/Dockerfile.backend -t ai-platform-backend:latest .
docker build -f docker/Dockerfile.frontend -t ai-platform-frontend:latest .

# Push to registry
docker tag ai-platform-backend:latest your-registry/ai-platform-backend:latest
docker push your-registry/ai-platform-backend:latest

# Deploy with compose
docker compose -f docker-compose.yml up -d
```

---

## 📊 Resume Impact

This project directly demonstrates:

> **"Daily user of Claude Code and GitHub Copilot, systematically tested prompt engineering strategies — context-window structuring, chain-of-thought scaffolding, and negative-example framing — to improve code generation accuracy and reduce hallucinations across multi-file projects."**

✅ **6 implemented strategies** (baseline, CoT, few-shot, negative, self-reflection, context-window) with side-by-side comparison  
✅ **Quantified hallucination detection** with heuristic + LLM-assisted scoring  
✅ **Multi-file Python project** with proper module boundaries and imports

> **"Designed multi-agent LangChain workflows chaining LLM calls for document triage, regression classification, and error-to-fix synthesis; logged evaluation results in structured experiment reports."**

✅ **5-agent pipeline** with structured JSON handoffs between BugAnalyzer → Classifier → RootCause → FixGenerator → ReportWriter  
✅ **SQLite-backed experiment tracking** with per-strategy aggregated metrics  
✅ **Error-to-fix synthesis** with explicit 2-stage reasoning chain

> **"Authored technical prompt templates and context files capturing system state for AI models, analogous to CLAUDE.md skill files and MCP configurations."**

✅ **5 CLAUDE.md-inspired context files** (overview, architecture, standards, API docs, team guidelines)  
✅ **6 parameterized prompt templates** with `string.Template` substitution  
✅ **Quantitative improvement tracking** across iterative experiment runs

---

## 🔮 Future Improvements

- [ ] RAG-based codebase search with vector embeddings (FAISS/Chroma)
- [ ] Semantic bug similarity using sentence transformers
- [ ] Automated prompt optimization via DSPy
- [ ] Model comparison dashboard (Claude vs GPT-4o vs Gemini)
- [ ] AI-generated release notes from commit history
- [ ] Slack/GitHub integration for real PR review workflows
- [ ] PostgreSQL backend for production deployments
- [ ] WebSocket for real-time agent execution streaming
- [ ] Prompt version control with Git-like diff view

---

## 📄 License

MIT License — use freely for portfolio, learning, and production.
