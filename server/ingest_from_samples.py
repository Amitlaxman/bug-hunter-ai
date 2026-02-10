"""
One-off ingestion: build documents from samples.csv and persist index to server/storage/.

Uses the same embedding model and storage layout as mcp_server.py so search_documents
returns relevant bug-pattern and API documentation. Run from project root:

  python server/ingest_from_samples.py

Optionally set ADD_TO_EXISTING=1 to try loading the existing index and inserting
(newer LlamaIndex may support this); by default we create a fresh index from samples.
"""

import csv
import os
import sys
from pathlib import Path

# Run from project root; server/ is the package context
PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

STORAGE_PATH = PROJECT_ROOT / "server" / "storage"
EMBEDDING_MODEL_PATH = PROJECT_ROOT / "server" / "embedding_model"
SAMPLES_CSV = PROJECT_ROOT / "samples.csv"


def _build_documents_from_csv() -> list:
    """Build documents from CSV using only ID, Context, and Code (no Explanation or Correct Code)."""
    from llama_index.core import Document

    documents = []
    with open(SAMPLES_CSV, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            doc_id = row.get("ID", "")
            context = row.get("Context", "")
            code = row.get("Code", "")
            text = (
                f"ID: {doc_id}\n"
                f"Context: {context}\n"
                f"Code:\n{code}"
            )
            doc = Document(text=text.strip(), metadata={"id": doc_id})
            documents.append(doc)
    return documents


def main() -> None:
    if not SAMPLES_CSV.exists():
        print(f"Samples file not found: {SAMPLES_CSV}")
        sys.exit(1)
    if not EMBEDDING_MODEL_PATH.is_dir():
        print(f"Embedding model not found: {EMBEDDING_MODEL_PATH}")
        print("Ensure server/embedding_model exists (e.g. BAAI/bge-base-en-v1.5).")
        sys.exit(1)

    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from llama_index.core import Settings, StorageContext, VectorStoreIndex

    Settings.embed_model = HuggingFaceEmbedding(
        model_name=str(EMBEDDING_MODEL_PATH)
    )

    documents = _build_documents_from_csv()
    print(f"Built {len(documents)} documents from {SAMPLES_CSV}")

    index = VectorStoreIndex.from_documents(documents)
    STORAGE_PATH.mkdir(parents=True, exist_ok=True)
    index.storage_context.persist(persist_dir=str(STORAGE_PATH))
    print(f"Persisted index to {STORAGE_PATH}")


if __name__ == "__main__":
    main()
