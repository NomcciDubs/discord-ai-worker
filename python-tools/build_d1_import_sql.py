from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_INPUT = Path("data") / "generated" / "knowledge_chunks_summarized.jsonl"
FALLBACK_INPUT = Path("data") / "generated" / "knowledge_chunks.jsonl"
DEFAULT_OUT = Path("data") / "generated" / "d1_import.sql"


def sql(value: object) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, int):
        return str(value)
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a D1 SQL import file from generated knowledge chunks.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    if not args.input.exists() and args.input == DEFAULT_INPUT and FALLBACK_INPUT.exists():
        args.input = FALLBACK_INPUT
    if not args.input.exists():
        raise FileNotFoundError(f"Missing generated file: {args.input}")

    documents = {}
    chunks = []

    with args.input.open("r", encoding="utf-8") as file:
        for line in file:
            row = json.loads(line)
            if row["document_id"] not in documents:
                documents[row["document_id"]] = {
                    "id": row["document_id"],
                    "language": row["language"],
                    "title": row["title"],
                    "link": row["link"],
                    "content": row.get("document_content") or row["content"],
                    "summary": row.get("document_summary") or row.get("summary") or "",
                    "steps": row.get("document_steps") or row.get("steps") or "",
                    "keywords": row.get("document_keywords") or row.get("keywords") or "",
                    "common_errors": row.get("document_common_errors") or row.get("common_errors") or "",
                }
            chunks.append(row)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as file:
        for doc in documents.values():
            file.write(
                "INSERT OR REPLACE INTO documents (id, language, title, link, content, summary, steps, keywords, common_errors) VALUES "
                f"({sql(doc['id'])}, {sql(doc['language'])}, {sql(doc['title'])}, {sql(doc['link'])}, {sql(doc['content'])}, "
                f"{sql(doc['summary'])}, {sql(doc['steps'])}, {sql(doc['keywords'])}, {sql(doc['common_errors'])});\n"
            )
        for chunk in chunks:
            file.write(
                "INSERT OR REPLACE INTO document_chunks (id, document_id, language, chunk_index, title, link, content, summary, steps, keywords, common_errors, search_text) VALUES "
                f"({sql(chunk['id'])}, {sql(chunk['document_id'])}, {sql(chunk['language'])}, {sql(chunk['chunk_index'])}, "
                f"{sql(chunk['title'])}, {sql(chunk['link'])}, {sql(chunk['content'])}, {sql(chunk.get('summary', ''))}, "
                f"{sql(chunk.get('steps', ''))}, {sql(chunk.get('keywords', ''))}, {sql(chunk.get('common_errors', ''))}, "
                f"{sql(chunk.get('search_text') or chunk['content'])});\n"
            )
    print(f"Wrote {len(documents)} documents and {len(chunks)} chunks to {args.out}")


if __name__ == "__main__":
    main()
