from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_INPUT = Path("data") / "generated" / "knowledge_chunks.jsonl"
REQUIRED_FIELDS = {"id", "document_id", "language", "chunk_index", "title", "link", "content", "search_text"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate generated HolyHosting knowledge chunks.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args()

    if not args.input.exists():
      raise FileNotFoundError(f"Missing generated file: {args.input}")

    count = 0
    languages = {"es": 0, "en": 0}
    seen_ids = set()

    with args.input.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            row = json.loads(line)
            missing = REQUIRED_FIELDS - set(row)
            if missing:
                raise ValueError(f"Line {line_number} missing fields: {sorted(missing)}")
            if row["language"] not in languages:
                raise ValueError(f"Line {line_number} has invalid language: {row['language']}")
            if row["id"] in seen_ids:
                raise ValueError(f"Duplicate chunk id at line {line_number}: {row['id']}")
            seen_ids.add(row["id"])
            languages[row["language"]] += 1
            count += 1

    print(f"Valid chunks: {count}. Spanish: {languages['es']}. English: {languages['en']}.")


if __name__ == "__main__":
    main()
