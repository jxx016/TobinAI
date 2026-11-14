"""Lead chase graph.

Flow: ingest → classify → draft or stop → rubric → human gate → send and schedule.
Threads are keyed by lead id. Postgres is used for the checkpointer and tactic
store when a Postgres URL is configured; otherwise memory adapters are used.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.store.base import BaseStore
from langgraph.store.memory import InMemoryStore
from langgraph.types import Command, interrupt

from src.agent.critic import evaluate_draft
from src.agent.llm import (
    SCHEDULED_FOLLOW_UP,
    DraftRequest,
    MockChaseLLM,
    RealChaseLLM,
    build_llm,
    classify_by_rules,
    latest_human_text,
    merge_safe,
)
from src.agent.state import (
    ANGLES,
    BACKOFF_HOURS,
    TERMINAL_STAGES,
    LeadChaseState,
    next_angle,
)
from src.config import Settings, get_settings
from src.reflection.optimizer import extract_winning_tactic, tactic_namespace
from src.tools.calendar import create_booking_link
from src.tools.crm import cancel_scheduled_followups, log_touchpoint, schedule_followup, upsert_lead
from src.tools.enrichment import enrich_lead
from src.tools.knowledge_base import search_battlecards
from src.tools.messaging import send_email, send_sms_or_whatsapp

logger = logging.getLogger(__name__)

MAX_CRITIC_RETRIES = 2
_EMBED_DIMS = 64
_OPEN_CONTEXTS: list[Any] = []
_GRAPH: Any | None = None


def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    """Hashing embedder so tactic search works without a hosted embedding API."""

    vectors: list[list[float]] = []
    for text in texts:
        vec = [0.0] * _EMBED_DIMS
        tokens = re.findall(r"[a-z0-9]+", (text or "").lower()) or ["empty"]
        for token in tokens:
            digest = hashlib.sha256(token.encode()).digest()
            bucket = int.from_bytes(digest[:2], "big") % _EMBED_DIMS
            sign = 1.0 if digest[2] % 2 == 0 else -1.0
            vec[bucket] += sign
        norm = math.sqrt(sum(value * value for value in vec)) or 1.0
        vectors.append([value / norm for value in vec])
    return vectors


def make_memory_store() -> InMemoryStore:
    return InMemoryStore(index={"dims": _EMBED_DIMS, "embed": embed_texts, "fields": ["text"]})


def recall_tactics(store: BaseStore, profile: dict[str, Any]) -> list[str]:
    namespace = tactic_namespace(profile)
    query = " ".join(
        part
        for part in (
            str(profile.get("role") or ""),
            str(profile.get("industry") or ""),
            str(profile.get("company") or ""),
        )
        if part
    )
    try:
        items = store.search(namespace, query=query or None, limit=3)
    except Exception:
        logger.exception("tactic search failed")
        return []
    texts: list[str] = []
    for item in items:
        value = getattr(item, "value", {}) or {}
        text = value.get("text") or value.get("heuristic")
        if text:
            texts.append(str(text))
    return texts


def initial_state(
    lead_id: str,
    *,
    message: str | None = None,
    channel: str = "email",
    **profile: Any,
) -> LeadChaseState:
    lead_profile = {
        "name": profile.get("name") or "",
        "email": profile.get("email") or "",
        "phone": profile.get("phone") or "",
        "company": profile.get("company") or "",
        "role": profile.get("role") or "",
        "source": profile.get("source") or "",
        "enrichment_notes": profile.get("enrichment_notes") or "",
        "industry": profile.get("industry") or "",
    }
    messages: list[Any] = []
    if message:
        messages.append(
            HumanMessage(content=message, additional_kwargs={"channel": channel, "kind": "inbound"})
        )
    return {
        "lead_id": lead_id,
        "lead_profile": lead_profile,
        "stage": profile.get("stage") or "NEW",
        "messages": messages,
        "touchpoint_count": int(profile.get("touchpoint_count") or 0),
        "last_angle_used": profile.get("last_angle_used") or "",
        "next_follow_up_at": None,
        "draft_message": None,
        "critic_feedback": None,
        "critic_retries": 0,
        "requires_human_approval": False,
        "approval_reason": None,
        "outcome_label": None,
    }


def follow_up_input() -> dict[str, Any]:
    return {
        "messages": [SystemMessage(content=SCHEDULED_FOLLOW_UP)],
        "critic_feedback": None,
        "critic_retries": 0,
        "requires_human_approval": False,
        "approval_reason": None,
        "draft_message": None,
        "outcome_label": None,
    }


def reply_input(message: str, channel: str = "email") -> dict[str, Any]:
    return {
        "messages": [
            HumanMessage(content=message, additional_kwargs={"channel": channel, "kind": "inbound"})
        ],
        "critic_feedback": None,
        "critic_retries": 0,
        "requires_human_approval": False,
        "approval_reason": None,
        "draft_message": None,
        "outcome_label": None,
    }


def _thread_config(lead_id: str) -> dict[str, Any]:
    return {"configurable": {"thread_id": lead_id}, "recursion_limit": 50}


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {"summary": value}
        return parsed if isinstance(parsed, dict) else {"summary": value}
    return {"summary": str(value)}


def _profile_payload(profile: dict[str, Any]) -> str:
    return json.dumps(
        {
            "name": profile.get("name") or "",
            "email": profile.get("email") or "",
            "phone": profile.get("phone") or "",
            "company": profile.get("company") or "",
            "role": profile.get("role") or "",
            "source": profile.get("source") or "",
            "industry": profile.get("industry") or "",
            "enrichment_notes": profile.get("enrichment_notes") or "",
            "winning_tactics": profile.get("winning_tactics") or [],
            "injection_detected": bool(profile.get("injection_detected")),
        }
    )


def _persist_lead(state: LeadChaseState, **overrides: Any) -> None:
    profile = dict(state.get("lead_profile") or {})
    stage = overrides.get("stage", state.get("stage") or "NEW")
    count = overrides.get("touchpoint_count", state.get("touchpoint_count") or 0)
    angle = overrides.get("last_angle_used", state.get("last_angle_used") or "")
    outcome = overrides.get("outcome_label", state.get("outcome_label") or "")
    follow = overrides.get("next_follow_up_at", state.get("next_follow_up_at"))
    if isinstance(follow, datetime):
        follow_iso = follow.astimezone(timezone.utc).isoformat()
    elif follow:
        follow_iso = str(follow)
    else:
        follow_iso = ""
    upsert_lead.invoke(
        {
            "lead_id": state["lead_id"],
            "name": profile.get("name") or "",
            "email": profile.get("email") or "",
            "phone": profile.get("phone") or "",
            "company": profile.get("company") or "",
            "role": profile.get("role") or "",
            "source": profile.get("source") or "",
            "industry": profile.get("industry") or "",
            "enrichment_notes": profile.get("enrichment_notes") or "",
            "stage": stage,
            "touchpoint_count": int(count or 0),
            "last_angle_used": angle or "",
            "next_follow_up_iso": follow_iso,
            "outcome_label": outcome or "",
            "profile_json": _profile_payload(profile),
        }
    )


def _unanswered_streak(messages: list[Any], *, include_new: bool) -> int:
    streak = 1 if include_new else 0
    for message in reversed(messages):
        name = message.__class__.__name__
        if name == "AIMessage":
            streak += 1
        elif name == "HumanMessage":
            break
    return streak


def _drafter_for(state: LeadChaseState) -> str:
    stage = state.get("stage")
    if stage == "READY_TO_BOOK":
        return "booking_node"
    if stage == "OBJECTION":
        return "objection_handler_node"
    return "outreach_drafter_node"


def build_checkpointer(settings: Settings | None = None) -> Any:
    settings = settings or get_settings()
    url = settings.resolved_checkpoint_url()
    if url.startswith(("postgres://", "postgresql")):
        try:
            from langgraph.checkpoint.postgres import PostgresSaver

            resource = PostgresSaver.from_conn_string(url)
            if hasattr(resource, "__enter__"):
                saver = resource.__enter__()
                _OPEN_CONTEXTS.append(resource)
            else:
                saver = resource
            setup = getattr(saver, "setup", None)
            if callable(setup):
                setup()
            logger.info("using PostgresSaver")
            return saver
        except Exception as exc:
            logger.warning("PostgresSaver unavailable (%s); using InMemorySaver", exc)
    return InMemorySaver()


def build_store(settings: Settings | None = None) -> BaseStore:
    settings = settings or get_settings()
    url = settings.resolved_checkpoint_url()
    if url.startswith(("postgres://", "postgresql")):
        try:
            from langgraph.store.postgres import PostgresStore

            resource = PostgresStore.from_conn_string(url)
            if hasattr(resource, "__enter__"):
                store = resource.__enter__()
                _OPEN_CONTEXTS.append(resource)
            else:
                store = resource
            setup = getattr(store, "setup", None)
            if callable(setup):
                setup()
            logger.info("using PostgresStore")
            return store
        except Exception as exc:
            logger.warning("PostgresStore unavailable (%s); using InMemoryStore", exc)
    return make_memory_store()


def build_graph(
    *,
    checkpointer: Any | None = None,
    store: BaseStore | None = None,
    llm: Any | None = None,
    settings: Settings | None = None,
) -> Any:
    """Compile the chase graph. Tests pass an in-memory saver and a fake LLM."""

    settings = settings or get_settings()
    checkpointer = build_checkpointer(settings) if checkpointer is None else checkpointer
    store = build_store(settings) if store is None else store
    llm = build_llm(settings) if llm is None else llm

    def ingest_and_enrich(state: LeadChaseState) -> dict[str, Any]:
        profile = dict(state.get("lead_profile") or {})
        stage = state.get("stage") or "NEW"
        if stage == "NEW":
            raw = enrich_lead.invoke(
                {
                    "name": profile.get("name") or "",
                    "company": profile.get("company") or "",
                    "role": profile.get("role") or "",
                    "industry": profile.get("industry") or "",
                }
            )
            enriched = _as_dict(raw)
            profile["enrichment_notes"] = str(enriched.get("summary") or "")
            if not str(profile.get("industry") or "").strip():
                profile["industry"] = str(enriched.get("industry") or "property-management")
            stage = "ENRICHED"
        tactics = recall_tactics(store, profile)
        if tactics:
            profile["winning_tactics"] = tactics
        partial: LeadChaseState = {**state, "lead_profile": profile, "stage": stage}  # type: ignore[misc]
        _persist_lead(partial)
        return {"lead_profile": profile, "stage": stage}

    def classify_intent(state: LeadChaseState) -> dict[str, Any]:
        rules = classify_by_rules(state)
        try:
            proposed = llm.classify(state)
        except Exception:
            logger.exception("classifier failed; using rules")
            proposed = rules
        if isinstance(llm, RealChaseLLM):
            decision = merge_safe(rules, proposed)
        else:
            # Mock and scripted classifiers already implement the policy.
            # Re-apply it so a sloppy double cannot waive opt-out or injection handling.
            decision = merge_safe(rules, proposed if isinstance(proposed, type(rules)) else rules)
        profile = dict(state.get("lead_profile") or {})
        profile["injection_detected"] = bool(decision.injection_detected)
        message = (state.get("messages") or [None])[-1]
        text = latest_human_text(state)
        if message is not None and message.__class__.__name__ == "HumanMessage" and text:
            kwargs = getattr(message, "additional_kwargs", {}) or {}
            channel = str(kwargs.get("channel") or "email") if isinstance(kwargs, dict) else "email"
            log_touchpoint.invoke(
                {
                    "lead_id": state["lead_id"],
                    "channel": channel,
                    "direction": "inbound",
                    "body": text[:8000],
                    "angle": "",
                    "payload_json": json.dumps({"injection_detected": bool(decision.injection_detected)}),
                }
            )
        return {
            "stage": decision.stage,
            "requires_human_approval": bool(decision.requires_human_approval),
            "approval_reason": decision.approval_reason,
            "lead_profile": profile,
        }

    def route_strategy(state: LeadChaseState) -> str:
        stage = state.get("stage")
        if stage in TERMINAL_STAGES:
            return "log_outcome_and_end"
        if stage == "READY_TO_BOOK":
            return "booking_node"
        if stage == "OBJECTION":
            return "objection_handler_node"
        return "outreach_drafter_node"

    def outreach_drafter_node(state: LeadChaseState) -> dict[str, Any]:
        profile = state.get("lead_profile") or {}
        if state.get("critic_feedback") and state.get("last_angle_used") in ANGLES:
            angle = str(state.get("last_angle_used"))
        else:
            angle = next_angle(state.get("last_angle_used"))
        draft = llm.draft(
            DraftRequest(
                lead_profile=profile,
                stage=str(state.get("stage") or ""),
                angle=angle,
                mode="outreach",
                critic_feedback=state.get("critic_feedback"),
                history_snippet=latest_human_text(state),
                winning_tactics=list(profile.get("winning_tactics") or []),
            )
        )
        return {"draft_message": draft, "last_angle_used": angle}

    def objection_handler_node(state: LeadChaseState) -> dict[str, Any]:
        profile = state.get("lead_profile") or {}
        history = latest_human_text(state)
        cards = search_battlecards.invoke({"query": history or "objection", "limit": 3})
        if isinstance(cards, str):
            battlecard = cards
        else:
            battlecard = "\n\n".join(
                f"{card.get('title')}: {card.get('body')}" for card in (cards or []) if isinstance(card, dict)
            )
        angle = "objection" if not state.get("critic_feedback") else str(state.get("last_angle_used") or "objection")
        draft = llm.draft(
            DraftRequest(
                lead_profile=profile,
                stage=str(state.get("stage") or ""),
                angle=angle,
                mode="objection",
                critic_feedback=state.get("critic_feedback"),
                battlecard=battlecard,
                history_snippet=history,
                winning_tactics=list(profile.get("winning_tactics") or []),
            )
        )
        return {"draft_message": draft, "last_angle_used": angle}

    def booking_node(state: LeadChaseState) -> dict[str, Any]:
        profile = state.get("lead_profile") or {}
        link = create_booking_link.invoke({"lead_id": state["lead_id"], "event_name": "Tobin intro"})
        if not isinstance(link, str):
            link = str(link)
        angle = "booking_link"
        draft = llm.draft(
            DraftRequest(
                lead_profile=profile,
                stage="READY_TO_BOOK",
                angle=angle,
                mode="booking",
                critic_feedback=state.get("critic_feedback"),
                booking_link=link,
                history_snippet=latest_human_text(state),
                winning_tactics=list(profile.get("winning_tactics") or []),
            )
        )
        return {"draft_message": draft, "last_angle_used": angle}

    def rubric_critic(state: LeadChaseState) -> Command:
        ok, feedback = evaluate_draft(state.get("draft_message"), state)
        if ok:
            return Command(update={"critic_feedback": None}, goto="hitl_gate")
        retries = int(state.get("critic_retries") or 0)
        if retries < MAX_CRITIC_RETRIES:
            return Command(
                update={"critic_feedback": feedback, "critic_retries": retries + 1},
                goto=_drafter_for(state),
            )
        return Command(
            update={
                "critic_feedback": feedback,
                "requires_human_approval": True,
                "approval_reason": state.get("approval_reason") or "critic_failed",
            },
            goto="hitl_gate",
        )

    def hitl_gate(state: LeadChaseState) -> dict[str, Any]:
        if not state.get("requires_human_approval"):
            return {}
        # interrupt() pauses on the first call and, after Command(resume=...), returns
        # the operator decision when this node runs again from the top.
        decision = interrupt(
            {
                "lead_id": state["lead_id"],
                "draft_message": state.get("draft_message"),
                "stage": state.get("stage"),
                "approval_reason": state.get("approval_reason"),
                "critic_feedback": state.get("critic_feedback"),
                "lead_profile": {
                    "name": (state.get("lead_profile") or {}).get("name"),
                    "email": (state.get("lead_profile") or {}).get("email"),
                    "company": (state.get("lead_profile") or {}).get("company"),
                    "role": (state.get("lead_profile") or {}).get("role"),
                },
                "actions": ["approve", "edit", "reject"],
            }
        )
        if not isinstance(decision, dict):
            decision = {"action": "reject"}
        action = str(decision.get("action") or "reject").lower()
        if action == "approve":
            return {"requires_human_approval": False}
        if action == "edit":
            edited = str(decision.get("draft") or decision.get("edited_draft") or "").strip()
            return {
                "requires_human_approval": False,
                "draft_message": edited or state.get("draft_message"),
            }
        return {
            "requires_human_approval": False,
            "outcome_label": "human_rejected",
            "approval_reason": "rejected",
        }

    def route_after_hitl(state: LeadChaseState) -> str:
        if state.get("outcome_label") == "human_rejected":
            return "log_outcome_and_end"
        if not str(state.get("draft_message") or "").strip():
            return "log_outcome_and_end"
        return "dispatch_and_schedule"

    def dispatch_and_schedule(state: LeadChaseState) -> dict[str, Any]:
        if state.get("stage") in {"UNSUBSCRIBED", "DISQUALIFIED"}:
            return {"draft_message": None, "outcome_label": str(state.get("stage") or "").lower()}
        if state.get("outcome_label") == "human_rejected":
            return {}
        draft = str(state.get("draft_message") or "").strip()
        if not draft:
            return {"outcome_label": state.get("outcome_label") or "no_draft"}
        profile = dict(state.get("lead_profile") or {})
        angle = str(state.get("last_angle_used") or "")
        subject = f"Note for {profile.get('company') or profile.get('name') or 'your team'}"
        email = str(profile.get("email") or "").strip()
        phone = str(profile.get("phone") or "").strip()
        if email:
            channel = "email"
            send_email.invoke(
                {
                    "to": email,
                    "subject": subject,
                    "body": draft,
                    "lead_id": state["lead_id"],
                    "angle": angle,
                }
            )
        elif phone:
            channel = "sms"
            send_sms_or_whatsapp.invoke(
                {
                    "to": phone,
                    "body": draft,
                    "lead_id": state["lead_id"],
                    "channel": "sms",
                    "angle": angle,
                }
            )
        else:
            channel = "system"
            log_touchpoint.invoke(
                {
                    "lead_id": state["lead_id"],
                    "channel": "system",
                    "direction": "outbound",
                    "body": draft,
                    "angle": angle,
                    "payload_json": json.dumps({"warning": "no destination"}),
                }
            )

        streak = _unanswered_streak(list(state.get("messages") or []), include_new=True)
        count = int(state.get("touchpoint_count") or 0) + 1
        now = datetime.now(timezone.utc)
        outcome = state.get("outcome_label")
        stage = state.get("stage") or "ENGAGED"
        follow_at: datetime | None
        if stage == "READY_TO_BOOK" or angle == "booking_link":
            stage = "BOOKED"
            outcome = "booked"
            follow_at = None
            cancel_scheduled_followups(state["lead_id"])
        elif streak >= 4:
            stage = "GHOSTING"
            outcome = outcome or "ghosting"
            follow_at = None
            cancel_scheduled_followups(state["lead_id"])
        else:
            if stage == "OBJECTION":
                stage = "ENGAGED"
                outcome = "reengaged_after_objection"
            elif stage == "GHOSTING":
                stage = "GHOSTING"
            elif stage in {"NEW", "ENRICHED"}:
                stage = "ENGAGED"
            hours = BACKOFF_HOURS[min(streak, len(BACKOFF_HOURS)) - 1]
            follow_at = now + timedelta(hours=hours)
            schedule_followup.invoke(
                {
                    "lead_id": state["lead_id"],
                    "run_at_iso": follow_at.isoformat(),
                    "kind": "follow_up",
                }
            )

        updated = {
            "messages": [AIMessage(content=draft, additional_kwargs={"angle": angle, "channel": channel})],
            "touchpoint_count": count,
            "stage": stage,
            "outcome_label": outcome,
            "next_follow_up_at": follow_at,
            "draft_message": draft,
            "requires_human_approval": False,
            "last_angle_used": angle,
        }
        merged = {**state, **updated}
        _persist_lead(merged)  # type: ignore[arg-type]
        if stage == "BOOKED" or outcome == "reengaged_after_objection":
            try:
                extract_winning_tactic(merged, store, llm if not isinstance(llm, MockChaseLLM) else llm)
            except Exception:
                logger.exception("failed to store winning tactic")
        return updated

    def log_outcome_and_end(state: LeadChaseState) -> dict[str, Any]:
        stage = str(state.get("stage") or "ENGAGED")
        label = state.get("outcome_label") or stage.lower()
        follow_at = state.get("next_follow_up_at")
        if stage == "UNSUBSCRIBED":
            label = "unsubscribed"
            follow_at = None
            cancel_scheduled_followups(state["lead_id"])
        elif stage == "DISQUALIFIED":
            label = state.get("outcome_label") or "disqualified"
            follow_at = None
            cancel_scheduled_followups(state["lead_id"])
        elif stage == "BOOKED":
            label = state.get("outcome_label") or "booked"
        if label == "human_rejected":
            log_touchpoint.invoke(
                {
                    "lead_id": state["lead_id"],
                    "channel": "system",
                    "direction": "system",
                    "body": "human rejected the draft",
                    "angle": state.get("last_angle_used") or "",
                    "payload_json": "{}",
                }
            )
        elif stage in {"UNSUBSCRIBED", "DISQUALIFIED", "BOOKED"}:
            log_touchpoint.invoke(
                {
                    "lead_id": state["lead_id"],
                    "channel": "system",
                    "direction": "system",
                    "body": f"outreach halted: {label}",
                    "angle": "",
                    "payload_json": "{}",
                }
            )
        updated = {"outcome_label": label, "stage": stage, "next_follow_up_at": follow_at}
        _persist_lead({**state, **updated})  # type: ignore[arg-type]
        return updated

    builder = StateGraph(LeadChaseState)
    builder.add_node("ingest_and_enrich", ingest_and_enrich)
    builder.add_node("classify_intent", classify_intent)
    builder.add_node("outreach_drafter_node", outreach_drafter_node)
    builder.add_node("objection_handler_node", objection_handler_node)
    builder.add_node("booking_node", booking_node)
    builder.add_node("rubric_critic", rubric_critic)
    builder.add_node("hitl_gate", hitl_gate)
    builder.add_node("dispatch_and_schedule", dispatch_and_schedule)
    builder.add_node("log_outcome_and_end", log_outcome_and_end)

    builder.add_edge(START, "ingest_and_enrich")
    builder.add_edge("ingest_and_enrich", "classify_intent")
    builder.add_conditional_edges(
        "classify_intent",
        route_strategy,
        {
            "log_outcome_and_end": "log_outcome_and_end",
            "booking_node": "booking_node",
            "objection_handler_node": "objection_handler_node",
            "outreach_drafter_node": "outreach_drafter_node",
        },
    )
    builder.add_edge("outreach_drafter_node", "rubric_critic")
    builder.add_edge("objection_handler_node", "rubric_critic")
    builder.add_edge("booking_node", "rubric_critic")
    builder.add_conditional_edges(
        "hitl_gate",
        route_after_hitl,
        {
            "dispatch_and_schedule": "dispatch_and_schedule",
            "log_outcome_and_end": "log_outcome_and_end",
        },
    )
    builder.add_edge("dispatch_and_schedule", END)
    builder.add_edge("log_outcome_and_end", END)

    return builder.compile(checkpointer=checkpointer, store=store, name="lead_chase")


def get_graph() -> Any:
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_graph()
    return _GRAPH


def reset_graph() -> None:
    global _GRAPH
    _GRAPH = None


def thread_config(lead_id: str) -> dict[str, Any]:
    return _thread_config(lead_id)
