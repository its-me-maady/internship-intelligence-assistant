# Internship Intelligence Assistant (IIA)

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Package Manager: uv](https://img.shields.io/badge/managed%20by-uv-purple.svg)](https://astral.sh/uv)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-LCEL-1C3C3C.svg)](https://python.langchain.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-VectorStore-orange.svg)](https://www.trychroma.com/)
[![Tests](https://img.shields.io/badge/tests-57%20passed-brightgreen.svg)](https://pytest.org)

> An intelligent, retrieval-augmented intelligence platform that ingests unstructured internship job postings, extracts structured requirements, provides citation-backed grounded conversational RAG, and executes deterministic skill gap analysis with prioritized learning roadmaps.

---

## Architecture Overview

The platform follows a decoupled, service-oriented architecture designed for deterministic reliability, speed, and strict hallucination prevention:

- **Backend Web Framework:** FastAPI with asynchronous non-blocking routes, strict Pydantic validation schemas, and automated OpenAPI (Swagger) documentation.
- **RAG & Orchestration:** LangChain Expression Language (LCEL) chains with XML-delimited prompt grounding and anti-hallucination refusal guardrails.
- **LLM Engine:** Google Gemini (`gemini-3.5-flash`) utilizing native JSON structured output (`with_structured_output`).
- **Embedding & Vector Storage:** Dual-mode embeddings supporting **FastEmbed** (local CPU-optimized ONNX `sentence-transformers/all-MiniLM-L6-v2` for offline execution) and **Google Generative AI** (`models/text-embedding-004`), backed by persistent ChromaDB.
- **Skill Matching & Analytics:** Pure deterministic Python intelligence engine combining multi-stage alias normalization, RapidFuzz token similarity, mathematical scoring, and prioritized preparation roadmaps.
- **Dependency & Environment Management:** Astral `uv` for sub-second, deterministic dependency resolution.

For detailed system specifications and developer guidelines, refer to:
- [`Internship Intelligence Assistant — Product Requirements Document.md`](./Internship%20Intelligence%20Assistant%20—%20Product%20Requirements%20Document.md)
- [`AGENTS.md`](./AGENTS.md)

---

## Directory Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application entrypoint, CORS, & health router
│   │   ├── config.py            # Pydantic BaseSettings environment configuration
│   │   ├── api/                 # REST API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── documents.py     # Document upload, parsing, listing, and deletion
│   │   │   ├── chat.py          # Conversational grounded RAG endpoint
│   │   │   └── analysis.py      # Structured extraction and deterministic skill gap engine
│   │   ├── models/              # Pydantic request/response data contracts
│   │   │   ├── __init__.py
│   │   │   ├── document_models.py
│   │   │   ├── chat_models.py
│   │   │   └── analysis_models.py
│   │   ├── rag/                 # Retrieval-Augmented Generation components
│   │   │   ├── __init__.py
│   │   │   ├── chains.py        # LCEL grounded RAG chains and citation formatters
│   │   │   ├── prompts.py       # Strict XML grounding prompts and refusal templates
│   │   │   └── retrievers.py    # Vector store retrieval adapters
│   │   ├── services/            # Core business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── ingestion_service.py   # Multi-format parsing (PDF, DOCX, TXT, MD) & sanitization
│   │   │   ├── chunking_service.py    # Context-aware text chunking with overlap
│   │   │   ├── vector_service.py      # ChromaDB integration and dual embedding providers
│   │   │   ├── document_service.py    # Document lifecycle orchestration
│   │   │   ├── extraction_service.py  # LLM structured parameter extraction
│   │   │   ├── matching_service.py    # Deterministic skill matching, scoring, and roadmaps
│   │   │   └── llm_service.py         # Google Gemini client factory
│   │   └── utils/               # Shared utilities
│   │       ├── __init__.py
│   │       └── synonyms.py      # Canonical skill synonym dictionary and sanitization
│   └── tests/                   # Automated test suite (57 passing tests)
│       ├── __init__.py
│       ├── conftest.py          # Shared pytest fixtures and vector store isolation
│       ├── test_health.py       # Operational readiness and infrastructure tests
│       ├── unit/                # Isolated unit tests (parsers, chunker, chains, matching)
│       │   ├── test_parsers.py
│       │   ├── test_chunker.py
│       │   ├── test_vector_service.py
│       │   ├── test_retrievers.py
│       │   ├── test_chains.py
│       │   ├── test_extraction_service.py
│       │   └── test_matching_service.py
│       └── integration/         # API and end-to-end pipeline integration tests
│           ├── test_documents_api.py
│           ├── test_chat_api.py
│           ├── test_extraction_api.py
│           ├── test_matching_api.py
│           └── test_ingestion_vector_flow.py
├── pyproject.toml               # PEP 621 metadata & dependency specifications
├── uv.lock                      # Deterministic dependency lockfile
├── .env.example                 # Environment variables configuration template
├── .gitignore                   # Git ignore specifications
├── AGENTS.md                    # Autonomous development protocol & guidelines
└── README.md
```

---

## Features Implemented (FR-1 through FR-6)

### 1. Multi-Format Document Ingestion & Validation (FR-1, FR-2)
- Ingests internship job postings across standard formats: **PDF (`.pdf`)**, **Microsoft Word (`.docx`)**, **Plain Text (`.txt`)**, and **Markdown (`.md`)**.
- Enforces strict security safeguards: validates file extensions, MIME types, 15MB file size limits, and protects against decompression bombs.
- Cleans and normalizes raw text while retaining page numbers and structural section boundaries.

### 2. Context-Aware Recursive Chunking & Vector Indexing (FR-3, FR-4)
- Partitions extracted text using recursive character chunking (800-character windows with 150-character overlap) to preserve semantic context across sentence boundaries.
- Generates high-dimensional vector embeddings via **FastEmbed** (`all-MiniLM-L6-v2`, running locally on CPU with zero network calls) or **Google Gemini** (`text-embedding-004`).
- Indexes chunks with rich metadata (`document_id`, `chunk_index`, `page_number`, `source_filename`) in persistent **ChromaDB** collections.

### 3. Grounded Conversational RAG with Citations & Guardrails
- Answers user queries exclusively from retrieved document context using strict XML-delimited prompt grounding.
- **Anti-Hallucination Refusal Guardrail:** If an uploaded document does not contain the information required to answer a query (e.g. stipend details or sponsorship policies omitted in the posting), the system returns a polite, explicit refusal rather than hallucinating or speculating.
- Returns verified source citations with precise document IDs, file names, page numbers, chunk indices, and relevance preview snippets.

### 4. Structured Job Requirement Extraction (FR-5)
- Automatically parses unstructured job postings into a strongly-typed Pydantic schema (`JobRequirementsSchema`) using Gemini structured outputs.
- Extracts standardized fields: job title, company name, location, work arrangement (On-site/Hybrid/Remote), stipend/salary, duration, deadlines, minimum education, target graduation years, required technical skills, preferred technical skills, required soft skills, and key responsibilities.

### 5. Deterministic Skill Gap & Match Scoring Engine (FR-6)
- **100% Deterministic & Zero-LLM:** Evaluates candidate skill sets against extracted job requirements using pure algorithmic logic without any non-deterministic AI calls.
- **Canonical Synonym Resolution:** Normalizes skill variants and abbreviations (e.g. `py` $\rightarrow$ `python`, `k8s` $\rightarrow$ `kubernetes`, `postgres` $\rightarrow$ `postgresql`, `ts` $\rightarrow$ `typescript`, `gcp` $\rightarrow$ `google cloud platform`).
- **Fuzzy Token Matching:** Uses RapidFuzz token sort and token set ratios to match compound phrases and minor spelling variations.
- **Mathematical Scoring Formula:**
  $$\text{Match Score} = \min\left(100, \left(\frac{\text{Matched Required}}{\text{Total Required}} \times 70\right) + \left(\frac{\text{Matched Preferred}}{\text{Total Preferred}} \times 30\right)\right)$$
  *(Includes dynamic reweighting safeguards when preferred or required lists are empty).*
- **Prioritized Learning Roadmap:** Generates an ordered study plan for missing skills categorized by criticality, with estimated study hours and concrete learning topics.
- **Sub-Millisecond Fast Path:** Accepts pre-extracted requirements in the request payload to execute match scoring instantaneously with 0 API latency.

---

## API Reference

All endpoints are prefixed with `/api/v1` (except `/health`). Interactive OpenAPI Swagger documentation is available at `/docs`.

### System & Health
| Method | Endpoint | Description | Key Request / Response Fields |
|---|---|---|---|
| `GET` | `/health` | System readiness and telemetry check | **Response:** `status`, `app_name`, `version`, `llm_model`, `embedding_provider`, `indexed_documents_count`, `total_chunks_count` |

### Document Management
| Method | Endpoint | Description | Key Request / Response Fields |
|---|---|---|---|
| `POST` | `/api/v1/documents/upload` | Uploads, validates, parses, chunks, and indexes a JD | **Request:** `multipart/form-data` with `file` (`.pdf`, `.docx`, `.txt`, `.md`)<br>**Response:** `DocumentUploadResponse` (`document_id`, `filename`, `file_size_bytes`, `page_count`, `chunk_count`, `status`, `created_at`) |
| `GET` | `/api/v1/documents` | Lists metadata summaries for all uploaded documents | **Response:** `List[DocumentSummary]` (`document_id`, `filename`, `file_size_bytes`, `page_count`, `chunk_count`, `status`, `created_at`) |
| `GET` | `/api/v1/documents/{document_id}` | Retrieves detailed metadata and all parsed chunks | **Path:** `document_id`<br>**Response:** `DocumentDetailResponse` (metadata + `chunks` array with `chunk_id`, `document_id`, `filename`, `content`, `chunk_index`, `page_number`, `character_start`, `character_end`, `total_chunks`, `uploaded_at`) |
| `DELETE` | `/api/v1/documents/{document_id}` | Deletes document files and purges ChromaDB vector embeddings | **Path:** `document_id`<br>**Response:** `DocumentDeleteResponse` (`success`: bool, `message`: str) |
| `POST` | `/api/v1/documents/{document_id}/extract` | Convenience alias route for structured extraction | **Path:** `document_id`<br>**Response:** `JobRequirementsSchema` |

### Grounded Conversational RAG Chat
| Method | Endpoint | Description | Key Request / Response Fields |
|---|---|---|---|
| `POST` | `/api/v1/chat` | Grounded conversational Q&A with citation tracking and refusal guardrail | **Request:** `query` (str), `document_id` (optional filter), `top_k` (default 4), `chat_history` (optional list)<br>**Response:** `ChatResponse` (`answer` (str), `is_grounded` (bool) — false when the refusal guardrail triggers, `sources` (list of citations with `document_id`, `filename`, `page_number`, `chunk_index`, `snippet`)) |

### Analysis & Skill Intelligence
| Method | Endpoint | Description | Key Request / Response Fields |
|---|---|---|---|
| `POST` | `/api/v1/analysis/extract/{document_id}` | Extracts structured JD parameters using LLM structured output | **Path:** `document_id`<br>**Response:** `JobRequirementsSchema` (title, company, compensation, required/preferred skills, education, deadlines, responsibilities) |
| `POST` | `/api/v1/analysis/skill-gap` | Evaluates student skills against JD requirements with zero LLM calls | **Request:** `document_id` (or `extracted_requirements`), `user_skills` (list of candidate skills)<br>**Response:** `match_score_percentage`, `score_breakdown` (weights + formula), `matched_required_skills`, `missing_required_skills`, `matched_preferred_skills`, `missing_preferred_skills`, `priority_learning_roadmap` |

---

## Quickstart Demo Walkthrough

Follow this copy-pasteable sequence to demonstrate the complete pipeline end-to-end using `curl` and `jq`:

### 1. Verify Backend Health
```bash
curl -s http://127.0.0.1:8000/health | jq
```

### 2. Upload an Internship Job Description
```bash
# Upload a sample posting and capture the returned document_id
UPLOAD_RES=$(curl -s -X POST -F "file=@samples/google_swe_intern_jd.txt" http://127.0.0.1:8000/api/v1/documents/upload)
echo $UPLOAD_RES | jq
DOCUMENT_ID=$(echo $UPLOAD_RES | jq -r '.document_id')
echo "Uploaded Document ID: $DOCUMENT_ID"
```

### 3. Grounded Conversational Query with Citations
```bash
# Ask a specific question answerable by the document
curl -s -X POST http://127.0.0.1:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"What are the mandatory qualifications and compensation details?\",
    \"document_id\": \"$DOCUMENT_ID\"
  }" | jq
```

```bash
# Test the anti-hallucination refusal guardrail (asking about unmentioned topics)
curl -s -X POST http://127.0.0.1:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"Does this company offer full-time H1B visa sponsorship upon graduation?\",
    \"document_id\": \"$DOCUMENT_ID\"
  }" | jq
```

### 4. Extract Structured Job Requirements
```bash
# Parse unstructured text into a validated JSON schema
curl -s -X POST http://127.0.0.1:8000/api/v1/analysis/extract/$DOCUMENT_ID | jq
```

### 5. Run Deterministic Skill Gap Analysis & Roadmap
```bash
# Evaluate student skills against the job posting (instantaneous, 0 LLM calls)
curl -s -X POST http://127.0.0.1:8000/api/v1/analysis/skill-gap \
  -H "Content-Type: application/json" \
  -d "{
    \"document_id\": \"$DOCUMENT_ID\",
    \"user_skills\": [\"py\", \"Java\", \"git\", \"linux\", \"postgres\", \"k8s\", \"gcp\", \"ts\", \"FastAPI\", \"Rust\"]
  }" | jq
```

---

## Getting Started

### 1. Prerequisites
- **Python 3.12+**
- **Astral `uv`** package and environment manager:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **Google Gemini API Key** (Required for LLM extraction and chat). Get one from [Google AI Studio](https://aistudio.google.com/).

### 2. Installation & Environment Synchronization
Clone the repository and synchronize the environment:
```bash
git clone git@github.com:its-me-maady/internship-intelligence-assistant.git
cd internship-intelligence-assistant

# Synchronize virtual environment with uv
uv sync --all-groups
```

### 3. Environment Configuration
Copy `.env.example` to `.env` and set your configuration:
```bash
cp .env.example .env
```
Edit `.env`:
```env
# Google Gemini API Key
GEMINI_API_KEY=AIzaSyYourActualApiKeyHere

# LLM Model Configuration
LLM_MODEL=gemini-3.5-flash

# Embedding Provider: local (CPU FastEmbed, zero cost) or gemini
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=models/text-embedding-004

# Storage Paths
CHROMA_PERSIST_DIRECTORY=data/chroma
UPLOAD_DIRECTORY=data/uploads
MAX_FILE_SIZE_MB=15
```

---

## Running the Application

### Start Development Server
```bash
uv run uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000
```
- **Interactive API Documentation (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative Documentation (ReDoc):** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Telemetry Endpoint:** [http://localhost:8000/health](http://localhost:8000/health)

---

## Running Tests & Quality Verification

The test suite contains **57 passing unit and integration tests** verifying document ingestion, chunking, ChromaDB vector indexing, LCEL RAG chains, anti-hallucination guardrails, structured extraction, and deterministic skill matching.

```bash
# Run all tests (executes in ~5 seconds with zero network calls via mock fixtures)
uv run pytest

# Run tests with verbose output
uv run pytest -v
```

### Run Linters and Formatting
```bash
# Check code style and linting
uv run ruff check .

# Check formatting compliance
uv run ruff format --check .
```

---

## Known Limitations & Planned Scope

1. **Backend API Only:** The current delivery comprises the complete backend REST API layer with OpenAPI/Swagger interaction. A frontend web UI is planned for a subsequent milestone.
2. **Upcoming Features (FR-7 & FR-8):** Tailored behavioral/technical interview question generation (FR-7) and multi-job description comparison matrix (FR-8) are part of the future product roadmap.
3. **Local Embedding Model Download:** When running with `EMBEDDING_PROVIDER=local` (default), FastEmbed downloads the `sentence-transformers/all-MiniLM-L6-v2` ONNX weights (~90MB) on first execution. Subsequent executions run 100% offline.
4. **Gemini Free-Tier API Latency:** Calls involving cloud LLM generation (`/chat` and `/analysis/extract`) depend on Google Gemini API response latency, taking approximately 10–30 seconds per request on free-tier quotas. In contrast, the skill-gap analysis endpoint (`/analysis/skill-gap`) executes in < 5ms when provided pre-extracted data.

---

## License
MIT License. Developed as an academic final project submission for NM.

