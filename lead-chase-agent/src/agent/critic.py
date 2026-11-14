"""Deterministic rubric for outbound drafts.

The critic is code, not a second model, so a failed draft is explained the same
way in tests and in production. A live model may write the draft; it does not grade it.
"""

from __future__ import annotations

import re
from typing import Any

MAX_WORDS = 80

FILLER_PHRASES: tuple[str, ...] = (
    "just checking in",
    "hope this finds you well",
    "hope this email finds you well",
    "hope you're doing well",
    "hope you are doing well",
    "touching base",
    "circle back",
    "circling back",
    "per my last email",
    "per my last message",
    "just wanted to",
    "gentle reminder",
    "just a nudge",
    "bumping this up",
)

# Unapproved commercial language. The playbook may discuss prices internally;
# outbound copy may not invent them.
PRICING_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\$\s?\d"),
    re.compile(r"\b\d+\s?%\s*(off)?", re.IGNORECASE),
    re.compile(r"\b\d{2,}\s*(usd|dollars)\b", re.IGNORECASE),
    re.compile(r"\b(usd|dollars)\s*\d{2,}\b", re.IGNORECASE),
    re.compile(
        r"\b(discount|discounts|free month|custom price|custom pricing|"
        r"special rate|kickback|price break|on the house|percent off)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(i'll|i will)\s+waive\b", re.IGNORECASE),
)

_CTA_RE = re.compile(
    r"(\?|\b(?:grab|reply|pick)\b|\bshould i\b|\bwant the\b|\bwant a\b|\bopen to\b)",
    re.IGNORECASE,
)
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def word_count(text: str) -> int:
    return len(re.findall(r"\S+", text or ""))


def count_ctas(text: str) -> int:
    parts = [part for part in _SENTENCE_RE.split((text or "").strip()) if part.strip()]
    if not parts:
        return 0
    return sum(1 for part in parts if _CTA_RE.search(part))


def _detail_tokens(state: dict[str, Any]) -> list[str]:
    profile = state.get("lead_profile") or {}
    tokens: list[str] = []
    for key in ("name", "company", "role", "source"):
        value = str(profile.get(key) or "").strip()
        if len(value) >= 2:
            tokens.append(value)
            if key == "name" and " " in value:
                tokens.append(value.split()[0])
    notes = str(profile.get("enrichment_notes") or "")
    for token in re.findall(r"[A-Za-z][A-Za-z0-9'-]{4,}", notes):
        tokens.append(token)
    stopwords = {
        "this", "that", "with", "from", "have", "your", "about", "would",
        "could", "please", "thanks", "there", "their", "them", "they",
        "just", "checking", "hope", "well", "email", "message",
    }
    for message in state.get("messages") or []:
        content = getattr(message, "content", "")
        if not isinstance(content, str):
            continue
        for chunk in re.findall(r"[A-Za-z][A-Za-z0-9'-]{4,}", content):
            if chunk.lower() in stopwords:
                continue
            tokens.append(chunk)
    # Preserve order while dropping duplicates.
    seen: set[str] = set()
    unique: list[str] = []
    for token in tokens:
        marker = token.lower()
        if marker in seen:
            continue
        seen.add(marker)
        unique.append(token)
    return unique


def concrete_detail_present(draft: str, state: dict[str, Any]) -> bool:
    haystack = (draft or "").lower()
    return any(token.lower() in haystack for token in _detail_tokens(state))


def evaluate_draft(draft: str | None, state: dict[str, Any]) -> tuple[bool, str]:
    """Return whether the draft passes and a single feedback string when it does not."""

    text = (draft or "").strip()
    failures: list[str] = []
    if not text:
        return False, "Draft failed the rubric: the draft is empty."

    words = word_count(text)
    if words >= MAX_WORDS:
        failures.append(f"{words} words (limit is under {MAX_WORDS})")

    lowered = text.lower()
    for phrase in FILLER_PHRASES:
        if phrase in lowered:
            failures.append(f"contains filler '{phrase}'")

    if not concrete_detail_present(text, state):
        failures.append("missing a concrete detail from the lead profile or history")

    ctas = count_ctas(text)
    if ctas != 1:
        failures.append(f"found {ctas} CTAs (need exactly 1)")

    for pattern in PRICING_PATTERNS:
        if pattern.search(text):
            failures.append("contains unapproved pricing or a discount")
            break

    if not failures:
        return True, ""
    return False, "Draft failed the rubric: " + "; ".join(failures) + "."
