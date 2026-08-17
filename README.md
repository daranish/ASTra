# ASTra

**AI-Powered Codebase Analyzer ChatBot** — point it at a GitHub repo, ask questions in plain English, get cited answers grounded in the actual source code.

Built on **AST-based code parsing** + **retrieval-augmented generation (RAG)**:

- 🌳 **Parsing**: [tree-sitter-language-pack](https://pypi.org/project/tree-sitter-language-pack/) (Rust-backed, 300+ languages) extracts symbol-level chunks (functions, classes, methods, structs).
- 🔢 **Embeddings**: [Google Gemini `text-embedding-004`](https://ai.google.dev/) — 768-dim vectors with proper `RETRIEVAL_DOCUMENT`/`RETRIEVAL_QUERY` task-type separation.
- 🗄️ **Vector store**: [Qdrant](https://qdrant.tech/) — in-process `:memory:` by default, remote server via `QDRANT_URL`.
- 🧠 **LLM**: [DeepSeek](https://platform.deepseek.com/) (via the OpenAI SDK pointed at their base URL).
- 🚀 **Interface**: FastAPI HTTP server with `POST /ingest`, `GET /ingest/{job_id}`, `POST /query`, `GET /health`.

## Quickstart

```bash
# 1. Install dependencies
poetry install

# 2. Configure secrets
cat > .env <<'EOF'
DEEPSEEK_API_KEY=sk-...
GOOGLE_API_KEY=...
EOF

# 3. Run the server
poetry run uvicorn astra.api.app:app --reload
```

The server is now at `http://localhost:8000`. OpenAPI docs at `/docs`.

## Usage

```bash
# Ingest a repo (returns immediately with a job_id; ingestion runs in the background)
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/pallets/flask"}'

# Poll ingestion status
curl http://localhost:8000/ingest/<job_id>

# Once status is "completed", ask questions
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "repo": "https://github.com/pallets/flask",
    "question": "How does Flask handle request routing?"
  }'
```

Example response:

```json
{
  "answer": "Flask uses Werkzeug's routing layer ([src/flask/app.py:602-650](...)). ...",
  "sources": [
    {
      "file_path": "src/flask/app.py",
      "symbol_name": "Flask.dispatch_request",
      "symbol_kind": "method",
      "start_line": 480,
      "end_line": 510,
      "score": 0.89,
      "snippet": "def dispatch_request(self):\n    ..."
    }
  ]
}
```

## Environment Variables

| Var | Required | Default | Notes |
| --- | --- | --- | --- |
| `DEEPSEEK_API_KEY` | ✅ | — | platform.deepseek.com |
| `GOOGLE_API_KEY` | ✅ | — | aistudio.google.com |
| `QDRANT_URL` | | `None` | None → in-memory. Set to `http://localhost:6333` for Docker. |
| `QDRANT_API_KEY` | | `None` | Required for Qdrant Cloud |
| `EMBEDDING_MODEL` | | `text-embedding-004` | |
| `EMBEDDING_DIMS` | | `768` | MUST match the collection |
| `LLM_MODEL` | | `deepseek-chat` | |
| `LLM_BASE_URL` | | `https://api.deepseek.com` | |
| `LOG_LEVEL` | | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `LOG_JSON` | | `true` | `false` for human-readable in dev |

See `CLAUDE.md` for the full architecture and design notes.

## Development

```bash
# Run tests
poetry run pytest

# Lint and format
poetry run ruff check .
poetry run ruff format .
```

## License

MIT
