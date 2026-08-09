from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path


DEFAULT_INPUT = Path("data") / "generated" / "knowledge_chunks_summarized.jsonl"
FALLBACK_INPUT = Path("data") / "generated" / "knowledge_chunks.jsonl"
DEFAULT_OUT = Path("data") / "generated" / "vectorize_vectors.ndjson"
DEFAULT_MODEL = "text-embedding-3-small"


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def embed_batch(api_key: str, model: str, inputs: list[str]) -> list[list[float]]:
    payload = json.dumps({"model": model, "input": inputs}).encode("utf-8")
    request = urllib.request.Request(
        "https://api.openai.com/v1/embeddings",
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"OpenAI embeddings error {error.code}: {error.read().decode('utf-8')}") from error

    return [item["embedding"] for item in data["data"]]


def main() -> None:
    parser = argparse.ArgumentParser(description="Create Vectorize NDJSON records with OpenAI embeddings.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--model", default=os.getenv("OPENAI_EMBEDDING_MODEL", DEFAULT_MODEL))
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--sleep", type=float, default=0.2)
    args = parser.parse_args()

    load_dotenv(Path(".env"))
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY in environment or .env")
    if not args.input.exists() and args.input == DEFAULT_INPUT and FALLBACK_INPUT.exists():
        args.input = FALLBACK_INPUT
    if not args.input.exists():
        raise FileNotFoundError(f"Missing generated file: {args.input}")

    rows = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    args.out.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    with args.out.open("w", encoding="utf-8") as file:
        for start in range(0, len(rows), args.batch_size):
            batch = rows[start : start + args.batch_size]
            inputs = [row.get("search_text") or f"{row['title']}\n\n{row['content']}" for row in batch]
            embeddings = embed_batch(api_key, args.model, inputs)
            for row, values in zip(batch, embeddings):
                vector_record = {
                    "id": row["id"],
                    "values": values,
                    "metadata": {
                        "language": row["language"],
                        "document_id": row["document_id"],
                        "title": row["title"],
                        "link": row["link"],
                    },
                }
                file.write(json.dumps(vector_record, ensure_ascii=False) + "\n")
                written += 1
            print(f"Embedded {written}/{len(rows)} chunks")
            time.sleep(args.sleep)

    print(f"Wrote Vectorize records to {args.out}")


if __name__ == "__main__":
    main()
