# ASTra

**AI-Powered Codebase Analyzer ChatBot**

ASTra is an intelligent codebase analysis and question-answering system. Point it at any GitHub repository, ask technical questions in plain English, and receive cited answers strictly grounded in the actual source code with file paths and line number references.

Built on Rust-backed AST code parsing, hybrid vector and full-text search, metadata-enriched chunking, and a multi-model fallback LLM architecture.

---

## Architecture Overview

The system consists of a decoupled architecture with a FastAPI backend and a web frontend:

```
[User Request] ---> [FastAPI Endpoint (/query/stream)]
                           |
                           v
              [OpenRouter Query Embedder]
                           |
                           v
        [Qdrant Hybrid Search (Vector + Tantivy Text)]
                           |
                           v
            [Context Assembly & Prompt Builder]
                           |
                           v
       [OpenRouter LLM (Primary -> Fallback 1/2/3)]
                           |
                           v
          [Server-Sent Events (SSE) Stream Output]
```

---

## Key Features

- **AST-Based Code Parsing**: Uses `tree-sitter-language-pack` for Rust-backed Abstract Syntax Tree parsing across 300+ programming languages. Extracts symbol-level chunks including functions, classes, methods, structs, and modules.
- **Language-Agnostic Metadata Enrichment**: Prepends structural location headers (file path, directory depth, symbol type, parent scope) to chunks before generating embeddings. This creates a strong semantic bridge between natural language queries and raw source code.
- **OpenRouter Embedding Pipeline**: Integrates OpenRouter embedding models (such as `nvidia/nemotron-3-embed-1b:free`) with explicit `encoding_format="float"` support.
- **Hybrid Search (Vector + Tantivy Full-Text)**: Combines semantic vector similarity search with Qdrant's built-in Tantivy full-text index on the code content. Ensures exact keyword matches (like function names or error strings) are retrieved alongside semantic matches.
- **Resilient LLM Fallback Architecture**: Automatic failover system across multiple OpenRouter models (Primary -> Fallback 1 -> Fallback 2 -> Fallback 3) to prevent downtime caused by model rate limits or temporary provider outages.
- **Real-Time Streaming Responses**: Implements Server-Sent Events (SSE) via `POST /query/stream` to stream token responses instantly to the client while returning structured source citations.
- **Asynchronous Ingestion Pipeline**: Asynchronously clones, parses, chunks, embeds, and indexes git repositories in background tasks tracked by unique `ingestion_id` identifiers.

---

## Project Structure

```
ASTra/
├── Backend/
│   ├── src/
│   │   └── astra/
│   │       ├── api/          # FastAPI routes, dependencies, schemas, middleware
│   │       ├── chunking/     # Chunk models, token counters, splitters
│   │       ├── embedding/    # OpenRouter embedding client and batcher
│   │       ├── ingestion/    # Git cloner, repo walker, job store
│   │       ├── llm/          # OpenRouter LLM client with multi-fallback logic
│   │       ├── parsing/      # Tree-Sitter AST parsers and language extractors
│   │       ├── rag/          # RAG pipeline, context builder, citation formatting
│   │       ├── vectorstore/  # Qdrant client, schema initialization, hybrid repository search
│   │       ├── config.py     # Pydantic Settings configuration
│   │       ├── errors.py     # Custom exception hierarchy
│   │       └── logging.py    # Structlog logger configuration
│   ├── pyproject.toml        # Backend dependencies and configuration
│   ├── test_queries.py       # Retrieval diagnostic tool
│   └── reset_qdrant.py       # Qdrant collection reset utility
├── Frontend/                 # Web interface application
└── README.md                 # Project documentation
```

---

## Prerequisites

- **Python**: 3.13 or higher
- **Poetry**: Package dependency manager for Python
- **Git**: Installed and accessible on system PATH
- **Vector Database**: Access to a Qdrant instance (Qdrant Cloud or local Qdrant container)
- **API Key**: OpenRouter API key

---

## Quickstart

### 1. Configure Environment Variables

Navigate to the `Backend` directory and create your `.env` configuration file:

```bash
cd Backend
cat > .env <<'EOF'
OPENROUTER_API_KEY=your_openrouter_api_key_here
QDRANT_URL=https://your-qdrant-cluster.cloud.qdrant.io:6333
QDRANT_API_KEY=your_qdrant_api_key_here
EMBEDDING_MODEL=nvidia/nemotron-3-embed-1b:free
EMBEDDING_DIMS=2048
EOF
```

### 2. Install Backend Dependencies

Register and install the package dependencies using Poetry:

```bash
poetry install
```

### 3. Start the Backend Server

Launch the Uvicorn server:

```bash
poetry run uvicorn astra.api.app:app --reload --app-dir src --reload-exclude "astra_repos/*"
```

The API server will run at `http://localhost:8000`. OpenAPI documentation is available at `http://localhost:8000/docs`.

---

## Usage Guide

### Step 1: Ingest a Codebase

Trigger asynchronous ingestion of a GitHub repository:

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/daranish/To-Do-List"
  }'
```

Response:
```json
{
  "ingestion_id": "9278bb27-1cbf-4dae-b9db-bc1c9eff4d7b",
  "status": "pending",
  "message": "Ingestion job started in background"
}
```

### Step 2: Poll Ingestion Status

Check the job status until it returns `"completed"`:

```bash
curl http://localhost:8000/ingest/9278bb27-1cbf-4dae-b9db-bc1c9eff4d7b
```

### Step 3: Stream Query Answers

Query the ingested codebase via the streaming endpoint:

```bash
curl -N -X POST http://localhost:8000/query/stream \
  -H "Content-Type: application/json" \
  -d '{
    "repo": "https://github.com/daranish/To-Do-List",
    "ingestion_id": "9278bb27-1cbf-4dae-b9db-bc1c9eff4d7b",
    "question": "Which is the entry point of the repo and how are tasks loaded?"
  }'
```

Response format (Server-Sent Events):
```text
data: {"type": "sources", "data": [{"file_path": "CLI todo app/app.py", "symbol_name": "load_tasks", "symbol_kind": "function", "start_line": 5, "end_line": 17, "score": 0.842}]}

data: {"type": "chunk", "data": "The entry point of the repository is defined in `CLI todo app/app.py`..."}

data: {"type": "done"}
```

---

## Diagnostic and Utility Scripts

### Retrieval Diagnostic Tool

To evaluate chunk retrieval quality and test query matches against Qdrant without starting the full web server, run:

```bash
poetry run python test_queries.py
```

This script automatically detects the active `ingestion_id` in your Qdrant instance, executes a suite of test queries, and outputs match scores, file paths, line numbers, and code snippets.

### Qdrant Collection Reset Utility

When switching embedding models or changing vector dimensions (e.g., from 1024 to 2048 dimensions), use this utility to safely delete the existing Qdrant collection:

```bash
poetry run python reset_qdrant.py
```

---

## Configuration Reference

| Variable | Type | Default | Description |
| --- | --- | --- | --- |
| `OPENROUTER_API_KEY` | String | Required | OpenRouter API Key |
| `OPENROUTER_BASE_URL` | String | `https://openrouter.ai/api/v1` | OpenRouter Base API URL |
| `OPENROUTER_PRIMARY_MODEL` | String | `nvidia/nemotron-3-ultra-550b-a55b:free` | Primary LLM model slug |
| `OPENROUTER_FALLBACK_1_MODEL` | String | `cohere/north-mini-code:free` | 1st Fallback LLM model slug |
| `OPENROUTER_FALLBACK_2_MODEL` | String | `z-ai/glm-5.2:free` | 2nd Fallback LLM model slug |
| `OPENROUTER_FALLBACK_3_MODEL` | String | `deepseek/deepseek-v4-flash-0731` | 3rd Fallback LLM model slug |
| `EMBEDDING_MODEL` | String | `nvidia/nemotron-3-embed-1b:free` | OpenRouter Embedding model slug |
| `EMBEDDING_DIMS` | Integer | `2048` | Vector dimensionality (MUST match Qdrant collection) |
| `QDRANT_URL` | String | `None` | Qdrant server URL (`None` uses in-memory mode) |
| `QDRANT_API_KEY` | String | `None` | API Key for Qdrant Cloud instances |
| `QDRANT_COLLECTION` | String | `astra_code_chunks` | Qdrant collection name |
| `RETRIEVAL_TOP_K` | Integer | `30` | Number of chunks to retrieve per query |
| `RETRIEVAL_SCORE_THRESHOLD` | Float | `0.5` | Minimum similarity score threshold (0.0 to 1.0) |
| `MAX_CHUNK_TOKENS` | Integer | `1500` | Maximum token limit per code chunk |
| `LOG_LEVEL` | String | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `LOG_JSON` | Boolean | `true` | Enables structured JSON log output |

---

## Development

```bash
# Run unit and integration tests
poetry run pytest

# Run linting checks
poetry run ruff check .

# Format code
poetry run ruff format .
```

---

## License

This project is licensed under the MIT License.
