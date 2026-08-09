from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


DEFAULT_ES = Path("..") / ".." / "Scriptsholy" / "holy_gg_faq_posts_with_content_es.json"
DEFAULT_EN = Path("..") / ".." / "Scriptsholy" / "holy_gg_faq_posts_with_content.json"
DEFAULT_OUT = Path("data") / "generated" / "knowledge_chunks.jsonl"


def clean_text(value: str) -> str:
    value = re.sub(r"\s+", " ", value or "").strip()
    return value


def stable_id(*parts: str) -> str:
    raw = "|".join(parts).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:32]


def load_posts(path: Path, language: str) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, list):
        posts = data
    elif isinstance(data, dict) and "results" in data:
        posts = data["results"].get(language, {}).get("posts", [])
    else:
        raise ValueError(f"Unsupported JSON shape: {path}")

    normalized = []
    for post in posts:
        title = clean_text(post.get("title", ""))
        content = clean_text(post.get("content", ""))
        link = clean_text(post.get("link") or post.get("url") or "")
        if title and content and link:
            doc_id = stable_id(language, link)
            normalized.append(
                {
                    "document_id": doc_id,
                    "language": language,
                    "title": title,
                    "link": link,
                    "content": content,
                }
            )
    return normalized


def chunk_text(text: str, max_chars: int, overlap: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            boundary = text.rfind(". ", start, end)
            if boundary > start + max_chars // 2:
                end = boundary + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = max(end - overlap, end)
    return chunks


def build_records(posts: list[dict], max_chars: int, overlap: int) -> list[dict]:
    records = []
    for post in posts:
        chunks = chunk_text(post["content"], max_chars=max_chars, overlap=overlap)
        for index, chunk in enumerate(chunks):
            chunk_id = stable_id(post["document_id"], str(index), chunk[:80])
            records.append(
                {
                    "id": chunk_id,
                    "document_id": post["document_id"],
                    "language": post["language"],
                    "chunk_index": index,
                    "title": post["title"],
                    "link": post["link"],
                    "content": chunk,
                    "summary": "",
                    "steps": "",
                    "keywords": "",
                    "common_errors": "",
                    "search_text": f"Title: {post['title']}\nLanguage: {post['language']}\nContent: {chunk}",
                    "document_content": post["content"] if index == 0 else None,
                }
            )
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare HolyHosting guide chunks for D1 and Vectorize imports.")
    parser.add_argument("--es", type=Path, default=DEFAULT_ES)
    parser.add_argument("--en", type=Path, default=DEFAULT_EN)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--max-chars", type=int, default=1400)
    parser.add_argument("--overlap", type=int, default=180)
    args = parser.parse_args()

    posts = []
    if args.es.exists():
        posts.extend(load_posts(args.es, "es"))
    if args.en.exists():
        posts.extend(load_posts(args.en, "en"))

    records = build_records(posts, max_chars=args.max_chars, overlap=args.overlap)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Prepared {len(posts)} documents and {len(records)} chunks at {args.out}")


if __name__ == "__main__":
    main()
