from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add src/ to sys.path so it can import astra modules when run directly
src_dir = Path(__file__).parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from src.astra.config import get_settings
from src.astra.embedding.openrouter import OpenRouterEmbedder
from src.astra.vectorstore.client import make_client
from src.astra.vectorstore.repository import search

# =====================================================================
# Configuration: Target repository (or leave INGESTION_ID=None to auto-detect)
# =====================================================================
REPO_URL = "https://github.com/daranish/Library-Management-System"
INGESTION_ID = "b4cdc7a5-8454-4b5a-a866-35ce0f425cc2"  # 👈 Leave as None to automatically fetch the latest ingestion_id from Qdrant!

TEST_QUERIES = [
    "Which is the entry point of the repo?",
    "How are tasks loaded from file?",
    "Where is the CLI or application startup defined?",
    "What functions handle task deletion or completion?",
    "Extract All Route Handlers",
    "Identify Endpoints Using Auth Dependencies",
    "Detect Admin Permission Checks",
    "Extract Endpoints with Explicit Response Models",
    "Find All SQLAlchemy Model Classes",
    "Trace Foreign Keys and Cascades",
    "Detect Table Constraints (CheckConstraint)",
    "Find Pessimistic Locking Queries (with_for_update)",
    "Discover Pydantic Schemas & ORM Mode",
    "Extract Pydantic Field Validation Rules",
    "Detect Unused / Redundant Schemas",
    "Trace Password Hashing Lifecycle",
    "Locate HTTP Cookie Operations",
    "Scan for Environment Variable Reads",
    "Extract Raised HTTP Exceptions and Status Codes",
    "Verify Database Rollback in Exception Handlers",
    "Trace Function Call Graph for borrow_book",
    "Find FastAPI Startup Event Handlers",
    "Identify Database Session Injection (get_db)",
]


async def run_test_queries() -> None:
    settings = get_settings()
    qdrant = make_client(settings)
    embedder = OpenRouterEmbedder(settings)

    # Auto-detect ingestion_id from Qdrant if not explicitly set
    active_ingestion_id = INGESTION_ID
    if not active_ingestion_id:
        try:
            scroll_res, _ = qdrant.scroll(
                collection_name=settings.qdrant_collection,
                limit=1,
                with_payload=True,
            )
            if scroll_res and scroll_res[0].payload:
                active_ingestion_id = scroll_res[0].payload.get("ingestion_id")
                repo_in_qdrant = scroll_res[0].payload.get("repo")
                print(f"🔍 Auto-detected active ingestion in Qdrant:")
                print(f"   - Ingestion ID: {active_ingestion_id}")
                print(f"   - Repo URL: {repo_in_qdrant}\n")
            else:
                print("❌ ERROR: Qdrant collection is completely EMPTY!")
                print("   Please run `/ingest` on your repo first before testing.")
                return
        except Exception as e:
            print(f"❌ Could not query Qdrant collection: {e}")
            return

    print("=" * 80)
    print(f"ASTra Retrieval Diagnostic Tool")
    print(f"Model: {settings.embedding_model} ({settings.embedding_dims} dims)")
    print(f"Target Repo: {REPO_URL}")
    print(f"Using Ingestion ID: {active_ingestion_id}")
    print(f"Score Threshold: {settings.retrieval_score_threshold}")
    print("=" * 80)

    for i, question in enumerate(TEST_QUERIES, start=1):
        print(f"\n[{i}/{len(TEST_QUERIES)}] QUERY: \"{question}\"")
        print("-" * 80)

        # 1. Embed query
        query_vec = await embedder.embed_query(question)

        # 2. Retrieve chunks from Qdrant
        hits = search(
            client=qdrant,
            query_vector=query_vec,
            repo=REPO_URL,
            ingestion_id=active_ingestion_id,
            settings=settings,
            query_text=question,
            top_k=5,
        )

        if not hits:
            print("⚠️  NO CHUNKS RETRIEVED! (0 hits returned)")
            continue

        print(f"✅ RETRIEVED {len(hits)} CHUNKS:\n")
        for rank, hit in enumerate(hits, start=1):
            score = hit.get("score", 0.0)
            file_path = hit.get("file_path", "unknown")
            kind = hit.get("symbol_kind", "unknown")
            name = hit.get("symbol_name", "unknown")
            start = hit.get("start_line", "?")
            end = hit.get("end_line", "?")
            content = hit.get("content", "").strip()

            content_lines = content.splitlines()
            snippet = "\n".join(content_lines[:3])
            if len(content_lines) > 3:
                snippet += f"\n... ({len(content_lines) - 3} more lines)"

            print(f"   Hit #{rank} | Score: {score:.4f} | {kind} `{name}`")
            print(f"   Location: {file_path}:{start}-{end}")
            print("   " + "-" * 45)
            print("   Content Snippet:")
            for line in snippet.splitlines():
                print(f"     | {line}")
            print("   " + "-" * 45 + "\n")


if __name__ == "__main__":
    asyncio.run(run_test_queries())