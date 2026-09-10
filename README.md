# Internship Intelligence Assistant (IIA)

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Package Manager: uv](https://img.shields.io/badge/managed%20by-uv-purple.svg)](https://astral.sh/uv)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-LCEL-1C3C3C.svg)](https://python.langchain.com)

> An intelligent, retrieval-augmented intelligence platform transforming unstructured internship descriptions into grounded insights, deterministic skill-gap analysis, and tailored interview preparation.

---

## Architecture Overview

The system is built on a modular, decoupled architecture:
- **Backend Framework:** FastAPI with asynchronous routes and Pydantic validation schemas.
- **RAG & Orchestration:** LangChain Expression Language (LCEL) for auditable retrieval pipelines.
- **LLM & Embeddings:** Google Gemini (`gemini-1.5-flash`) and `text-embedding-004`.
- **Vector Database:** ChromaDB with persistent local SQLite backing.
- **Project & Environment Management:** Astral `uv` for fast, deterministic dependency resolution.

For detailed system specifications and operational rules, refer to:
- [`Internship Intelligence Assistant — Product Requirements Document.md`](./Internship%20Intelligence%20Assistant%20—%20Product%20Requirements%20Document.md)
- [`AGENTS.md`](./AGENTS.md)

---

## Directory Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI application entrypoint & middleware
│   │   ├── config.py        # Environment & application settings (Pydantic BaseSettings)
│   │   ├── api/             # API Routers (documents, chat, analysis, compare)
│   │   ├── services/        # Business logic & service orchestration
│   │   ├── rag/             # LangChain LCEL chains, retrievers, prompts
│   │   ├── models/          # Pydantic DTOs & data schemas
│   │   └── utils/           # Helper functions & utilities
│   └── tests/
│       ├── __init__.py
│       └── test_health.py   # Health check & infrastructure tests
├── pyproject.toml           # PEP 621 metadata & dependency specifications
├── uv.lock                  # Deterministic dependency lockfile
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore rules
├── AGENTS.md                # Autonomous agent operating protocol
└── README.md
```

---

## Getting Started

### 1. Prerequisites
- **Git**
- **Astral `uv`** (Python package & environment manager):
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

### 2. Installation & Environment Setup
Clone the repository and install all dependencies:
```bash
git clone git@github.com:its-me-maady/internship-intelligence-assistant.git
cd internship-intelligence-assistant

# Synchronize virtual environment with uv
uv sync --all-groups
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and set your Google Gemini API Key:
```bash
cp .env.example .env
```
Edit `.env`:
```env
GEMINI_API_KEY=your_actual_gemini_api_key
LLM_MODEL=gemini-1.5-flash
EMBEDDING_MODEL=models/text-embedding-004
```

---

## Running the Application

### Start Backend Development Server
```bash
uv run uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000
```
- Interactive API Documentation (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check Endpoint: [http://localhost:8000/health](http://localhost:8000/health)

---

## Running Tests & Quality Checks

### Run Automated Tests
```bash
uv run pytest
```

### Run Linter & Formatter Checks
```bash
# Check code style and linting
uv run ruff check .

# Check formatting
uv run ruff format --check .
```

---

## License
MIT License. Created as an academic internship project.
