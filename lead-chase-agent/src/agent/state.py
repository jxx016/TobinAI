"""Graph state keyed by ``thread_id = lead_id``."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from typing_extensions import TypedDict

Stage = Literal[
    "NEW",
    "ENRICHED",
    "ENGAGED",
    "OBJECTION",
    "GHOSTING",
    "READY_TO_BOOK",
    "BOOKED",
    "DISQUALIFIED",
    "UNSUBSCRIBED",
]

TERMINAL_STAGES: frozenset[str] = frozenset({"UNSUBSCRIBED", "DISQUALIFIED", "BOOKED"})

ANGLES: tuple[str, ...] = (
    "direct_value",
    "social_proof",
    "micro_question",
    "breakup_note",
)

# Hours until the next chase after 1, 2, and 3 unanswered outbound touches.
BACKOFF_HOURS: tuple[int, ...] = (24, 72, 120)


class LeadChaseState(TypedDict):
    lead_id: str
    lead_profile: dict[str, Any]
    stage: Stage
    messages: Annotated[list[AnyMessage], add_messages]
    touchpoint_count: int
    last_angle_used: str
    next_follow_up_at: datetime | None
    draft_message: str | None
    critic_feedback: str | None
    critic_retries: int
    requires_human_approval: bool
    approval_reason: str | None
    outcome_label: str | None


def next_angle(last: str | None) -> str:
    """Rotate chase angles. The same angle is never chosen twice in a row."""

    if last not in ANGLES:
        return ANGLES[0]
    index = ANGLES.index(last)
    return ANGLES[(index + 1) % len(ANGLES)]
