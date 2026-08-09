from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


DEFAULT_INPUT = Path("data") / "generated" / "knowledge_chunks.jsonl"
DEFAULT_OUT = Path("data") / "generated" / "knowledge_chunks_summarized.jsonl"
DEFAULT_MODEL = "gpt-4.1-mini"


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def as_lines(value: object) -> str:
    if isinstance(value, list):
        return "\n".join(f"- {str(item).strip()}" for item in value if str(item).strip())
    return str(value or "").strip()


def call_openai(api_key: str, model: str, language: str, title: str, content: str, retries: int) -> dict:
    if language == "es":
        system = (
            "Estructuras guías de soporte de HolyHosting en español. "
            "Devuelve solo JSON válido sin markdown. No inventes información."
        )
        user = (
            "Resume y estructura esta guía para que sea fácil de leer desde una base de datos.\n"
            "Devuelve JSON con estas claves exactas:\n"
            "summary: resumen breve de 1-3 frases\n"
            "steps: lista de pasos concretos si existen, o []\n"
            "keywords: lista de términos de búsqueda útiles\n"
            "common_errors: lista de errores/problemas mencionados, o []\n\n"
            f"Título: {title}\n\nContenido:\n{content[:12000]}"
        )
    else:
        system = (
            "You structure HolyHosting support guides in English. "
            "Return valid JSON only, with no markdown. Do not invent information."
        )
        user = (
            "Summarize and structure this guide so it is easy to read from a database.\n"
            "Return JSON with these exact keys:\n"
            "summary: short 1-3 sentence summary\n"
            "steps: concrete step list when available, or []\n"
            "keywords: useful search terms\n"
            "common_errors: mentioned errors/problems, or []\n\n"
            f"Title: {title}\n\nContent:\n{content[:12000]}"
        )

    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        method="POST",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )

    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                data = json.loads(response.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8")
            if error.code not in (429, 500, 502, 503, 504) or attempt >= retries:
                raise RuntimeError(f"OpenAI summary error {error.code}: {body}") from error
            time.sleep(2**attempt)
        except TimeoutError:
            if attempt >= retries:
                raise
            time.sleep(2**attempt)

    content = data["choices"][0]["message"]["content"]
    return json.loads(content)


def load_existing(path: Path) -> dict[str, list[dict]]:
    existing: dict[str, list[dict]] = defaultdict(list)
    if not path.exists():
        return existing
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            row = json.loads(line)
            existing[row["document_id"]].append(row)
    return existing


def build_search_text(row: dict, summary: str, steps: str, keywords: str, common_errors: str) -> str:
    parts = [
        f"Title: {row['title']}",
        f"Language: {row['language']}",
        f"Summary: {summary}",
        f"Steps:\n{steps}" if steps else "",
        f"Keywords: {keywords}" if keywords else "",
        f"Common errors:\n{common_errors}" if common_errors else "",
        f"Content: {row['content']}",
    ]
    return "\n".join(part for part in parts if part)


def safe_console(text: str) -> str:
    return text.encode("ascii", errors="backslashreplace").decode("ascii")


def summarize_document(api_key: str, model: str, document_id: str, chunks: list[dict], retries: int) -> tuple[str, list[dict], str]:
    first = chunks[0]
    full_content = first.get("document_content") or "\n\n".join(chunk["content"] for chunk in chunks)
    summary_data = call_openai(api_key, model, first["language"], first["title"], full_content, retries=retries)
    summary = as_lines(summary_data.get("summary"))
    steps = as_lines(summary_data.get("steps"))
    keywords = as_lines(summary_data.get("keywords"))
    common_errors = as_lines(summary_data.get("common_errors"))

    enriched_chunks = []
    for chunk in chunks:
        enriched = dict(chunk)
        enriched["summary"] = summary
        enriched["steps"] = steps
        enriched["keywords"] = keywords
        enriched["common_errors"] = common_errors
        enriched["search_text"] = build_search_text(enriched, summary, steps, keywords, common_errors)
        if enriched.get("chunk_index") == 0:
            enriched["document_summary"] = summary
            enriched["document_steps"] = steps
            enriched["document_keywords"] = keywords
            enriched["document_common_errors"] = common_errors
        enriched_chunks.append(enriched)

    return document_id, enriched_chunks, first["title"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize HolyHosting knowledge chunks with OpenAI.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--model", default=os.getenv("OPENAI_SUMMARY_MODEL", DEFAULT_MODEL))
    parser.add_argument("--sleep", type=float, default=0.2)
    parser.add_argument("--limit", type=int, default=0, help="Optional max new documents for testing.")
    parser.add_argument("--concurrency", type=int, default=4, help="Parallel OpenAI summary requests.")
    parser.add_argument("--retries", type=int, default=3, help="Retries for transient OpenAI errors.")
    args = parser.parse_args()

    load_dotenv(Path(".env"))
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY in environment or .env")
    if not args.input.exists():
        raise FileNotFoundError(f"Missing generated file: {args.input}")

    rows = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["document_id"]].append(row)

    existing = load_existing(args.out)
    args.out.parent.mkdir(parents=True, exist_ok=True)

    pending = [(document_id, chunks) for document_id, chunks in grouped.items() if document_id not in existing]
    if args.limit:
        pending = pending[: args.limit]

    processed_docs = len(existing)
    total_docs = len(grouped)
    safe_concurrency = max(1, args.concurrency)

    with args.out.open("a", encoding="utf-8") as file:
        with ThreadPoolExecutor(max_workers=safe_concurrency) as executor:
            futures = [
                executor.submit(summarize_document, api_key, args.model, document_id, chunks, args.retries)
                for document_id, chunks in pending
            ]
            for future in as_completed(futures):
                document_id, enriched_chunks, title = future.result()
                if document_id in existing:
                    continue
                for enriched in enriched_chunks:
                    file.write(json.dumps(enriched, ensure_ascii=False) + "\n")
                file.flush()
                existing[document_id] = enriched_chunks
                processed_docs += 1
                print(safe_console(f"Summarized {processed_docs}/{total_docs} documents: {title}"))
                if args.sleep:
                    time.sleep(args.sleep)

    print(f"Wrote summarized chunks to {args.out}")


if __name__ == "__main__":
    main()
