"""Local battlecard search over data/playbook.md. No network and no embeddings required."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from langchain_core.tools import tool

PLAYBOOK_PATH = Path(__file__).resolve().parents[2] / "data" / "playbook.md"
_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return {token for token in _TOKEN_RE.findall(text.lower()) if len(token) > 2}


@lru_cache(maxsize=1)
def load_chunks() -> tuple[dict[str, str], ...]:
    text = PLAYBOOK_PATH.read_text(encoding="utf-8")
    chunks: list[dict[str, str]] = []
    section = ""
    title = ""
    buffer: list[str] = []

    def flush() -> None:
        body = "\n".join(buffer).strip()
        if title and body:
            chunks.append({"section": section, "title": title, "body": body})

    for line in text.splitlines():
        if line.startswith("## "):
            flush()
            section = line[3:].strip()
            title = section
            buffer = []
        elif line.startswith("### "):
            flush()
            title = line[4:].strip()
            buffer = []
        else:
            buffer.append(line)
    flush()
    return tuple(chunks)


def search_battlecards_impl(query: str, limit: int = 3) -> list[dict]:
    chunks = load_chunks()
    query_tokens = _tokens(query)
    scored: list[dict] = []
    for chunk in chunks:
        title_tokens = _tokens(chunk["title"])
        body_tokens = _tokens(chunk["body"])
        overlap = len(query_tokens & (title_tokens | body_tokens))
        title_bonus = 2 * len(query_tokens & title_tokens)
        score = overlap + title_bonus
        if score <= 0:
            continue
        scored.append({**chunk, "score": score})
    scored.sort(key=lambda item: item["score"], reverse=True)
    if not scored and chunks:
        fallback = next((chunk for chunk in chunks if "objection" in chunk["section"].lower()), chunks[0])
        scored = [{**fallback, "score": 0}]
    return scored[: max(1, limit)]


@tool
def search_battlecards(query: str, limit: int = 3) -> list[dict]:
    """Search the local playbook for pricing guardrails, FAQs, and objection battlecards."""

    return search_battlecards_impl(query=query, limit=limit)
