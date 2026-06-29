"""
Build ChromaDB from AI_Human.csv (columns: text, generated).

generated: 0 = human, 1 = AI

Usage (from server/):
  python build_knowledge_base.py
  python build_knowledge_base.py --max-per-label 500 --reset
"""

import argparse
import csv
import random
import shutil
import sys
from pathlib import Path

import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

import config
from app.rag.embeddings import get_embeddings

EMBED_BATCH_SIZE = 64


def parse_label(generated_value: str) -> str:
    value = str(generated_value).strip().lower()
    if value in {"0", "0.0", "false"}:
        return "human"
    if value in {"1", "1.0", "true"}:
        return "ai"
    raise ValueError(f"Unexpected generated value: {generated_value!r}")


def reservoir_sample_csv(csv_path: Path, max_per_label: int, seed: int):
    random.seed(seed)
    human_reservoir = []
    ai_reservoir = []
    human_seen = 0
    ai_seen = 0

    with csv_path.open(encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        if "text" not in reader.fieldnames or "generated" not in reader.fieldnames:
            raise ValueError("CSV must have columns: text, generated")

        for row_index, row in enumerate(reader):
            text = (row.get("text") or "").strip()
            if not text:
                continue

            try:
                label = parse_label(row.get("generated", ""))
            except ValueError:
                continue

            item = {"text": text, "label": label, "row_index": row_index}

            if label == "human":
                human_seen += 1
                if len(human_reservoir) < max_per_label:
                    human_reservoir.append(item)
                else:
                    slot = random.randint(0, human_seen - 1)
                    if slot < max_per_label:
                        human_reservoir[slot] = item
            else:
                ai_seen += 1
                if len(ai_reservoir) < max_per_label:
                    ai_reservoir.append(item)
                else:
                    slot = random.randint(0, ai_seen - 1)
                    if slot < max_per_label:
                        ai_reservoir[slot] = item

    return human_reservoir + ai_reservoir, human_seen, ai_seen


def chunk_samples(samples, chunk_size: int, chunk_overlap: int):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = []
    for sample in samples:
        parts = splitter.split_text(sample["text"])
        for chunk_index, text in enumerate(parts):
            chunks.append(
                {
                    "text": text,
                    "metadata": {
                        "label": sample["label"],
                        "source": "AI_Human.csv",
                        "generated": "1" if sample["label"] == "ai" else "0",
                        "category": f"{sample['label']}_patterns",
                        "row_index": sample["row_index"],
                        "chunk_index": chunk_index,
                    },
                }
            )
    return chunks


def ingest_chunks(chunks, chroma_dir: Path):
    embeddings = get_embeddings()

    vectorstore = Chroma(
        persist_directory=str(chroma_dir),
        embedding_function=embeddings,
        collection_name=config.COLLECTION_NAME,
    )

    for start in range(0, len(chunks), EMBED_BATCH_SIZE):
        batch = chunks[start : start + EMBED_BATCH_SIZE]
        vectorstore.add_texts(
            texts=[item["text"] for item in batch],
            metadatas=[item["metadata"] for item in batch],
        )
        print(f"  embedded {min(start + EMBED_BATCH_SIZE, len(chunks))}/{len(chunks)}")

    vectorstore.persist()
    return vectorstore._collection.count()


def reset_chroma_db(chroma_dir: Path) -> None:
    """Clear the collection without deleting locked files when possible."""
    if not chroma_dir.exists():
        return

    try:
        client = chromadb.PersistentClient(path=str(chroma_dir))
        client.delete_collection(config.COLLECTION_NAME)
        print(f"Cleared collection '{config.COLLECTION_NAME}' in {chroma_dir}")
        return
    except Exception:
        pass

    try:
        shutil.rmtree(chroma_dir)
        print(f"Removed existing {chroma_dir}")
    except PermissionError as exc:
        print(
            "\nCannot reset chroma_db because files are locked by another process.\n"
            "Usually the FastAPI server (uvicorn) is still running.\n\n"
            "Fix:\n"
            "  1. Stop uvicorn with Ctrl+C in its terminal\n"
            "  2. If port 8000 is still in use, find and kill the process:\n"
            "       netstat -ano | findstr :8000\n"
            "       taskkill /PID <pid> /F /T\n"
            "  3. Close any other terminal running build_knowledge_base.py\n"
            "  4. Retry: python build_knowledge_base.py --reset\n",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc


def main():
    parser = argparse.ArgumentParser(description="Ingest AI_Human.csv into ChromaDB")
    parser.add_argument("--csv", type=Path, default=config.DEFAULT_CSV, help="Path to AI_Human.csv")
    parser.add_argument(
        "--max-per-label",
        type=int,
        default=500,
        help="Random sample size per label (human and ai). Full dataset is ~487k rows.",
    )
    parser.add_argument("--chunk-size", type=int, default=500)
    parser.add_argument("--chunk-overlap", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing chroma_db before ingesting",
    )
    args = parser.parse_args()

    if not args.csv.exists():
        raise SystemExit(f"CSV not found: {args.csv.resolve()}")

    if args.reset:
        reset_chroma_db(Path(config.CHROMA_DIR))

    print(f"Sampling up to {args.max_per_label} rows per label from {args.csv.name}...")
    samples, human_seen, ai_seen = reservoir_sample_csv(
        args.csv, args.max_per_label, args.seed
    )
    print(f"  scanned dataset: {human_seen} human, {ai_seen} ai rows")
    print(f"  selected sample: {len(samples)} rows")

    print("Chunking text...")
    chunks = chunk_samples(samples, args.chunk_size, args.chunk_overlap)
    print(f"  produced {len(chunks)} chunks")

    print("Embedding and writing to ChromaDB (this may take several minutes)...")
    total = ingest_chunks(chunks, Path(config.CHROMA_DIR))
    print(f"Done. chroma_db now contains {total} documents.")


if __name__ == "__main__":
    main()
