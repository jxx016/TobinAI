"""Webhook, approval, reflection, and health routes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from pydantic import BaseModel, Field

from src.agent.graph import get_graph, initial_state, reply_input, thread_config
from src.config import get_settings
from src.reflection.optimizer import run_nightly_reflection
from src.tools.crm import get_lead_impl

router = APIRouter()


class LeadWebhook(BaseModel):
    lead_id: str | None = None
    name: str = ""
    email: str = ""
    phone: str = ""
    company: str = ""
    role: str = ""
    source: str = ""
    industry: str = ""
    message: str | None = None
    channel: Literal["email", "sms", "whatsapp"] = "email"


class ReplyWebhook(BaseModel):
    lead_id: str
    message: str = Field(min_length=1, max_length=8000)
    channel: Literal["email", "sms", "whatsapp"] = "email"


class ApprovalRequest(BaseModel):
    lead_id: str
    action: Literal["approve", "edit", "reject"]
    edited_draft: str | None = None


def coerce_graph_result(result: Any) -> tuple[dict[str, Any], list[Any]]:
    if isinstance(result, dict):
        data = dict(result)
        interrupts = list(data.pop("__interrupt__", ()) or ())
        return data, interrupts
    interrupts = list(getattr(result, "interrupts", ()) or ())
    value = getattr(result, "value", {}) or {}
    return dict(value), interrupts


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()
    return str(value)


def _interrupt_payload(interrupts: list[Any]) -> dict[str, Any] | None:
    if not interrupts:
        return None
    payload = getattr(interrupts[0], "value", interrupts[0])
    return payload if isinstance(payload, dict) else {"value": payload}


def public_view(result: Any) -> dict[str, Any]:
    state, interrupts = coerce_graph_result(result)
    pending = _interrupt_payload(interrupts)
    return {
        "lead_id": state.get("lead_id"),
        "stage": state.get("stage"),
        "draft_message": (pending or {}).get("draft_message") or state.get("draft_message"),
        "touchpoint_count": state.get("touchpoint_count"),
        "last_angle_used": state.get("last_angle_used"),
        "next_follow_up_at": _iso(state.get("next_follow_up_at")),
        "requires_human_approval": bool(state.get("requires_human_approval") or pending),
        "approval_reason": state.get("approval_reason") or (pending or {}).get("approval_reason"),
        "outcome_label": state.get("outcome_label"),
        "injection_detected": bool((state.get("lead_profile") or {}).get("injection_detected")),
        "interrupted": pending is not None,
        "interrupt": pending,
    }


def _ensure_not_waiting(graph: Any, config: dict[str, Any]) -> None:
    snapshot = graph.get_state(config)
    if getattr(snapshot, "interrupts", ()):
        raise HTTPException(
            status_code=409,
            detail="thread is waiting for human approval; resolve it with POST /hitl/approve",
        )


@router.get("/health")
def health() -> dict[str, Any]:
    settings = get_settings()
    return {
        "status": "ok",
        "mock_external_services": settings.mock_external_services,
        "llm_provider": settings.llm_provider,
        "tracing": settings.langchain_tracing_v2,
        "scheduler_enabled": settings.scheduler_enabled,
    }


@router.post("/webhooks/lead")
def webhook_lead(body: LeadWebhook) -> dict[str, Any]:
    from uuid import uuid4

    lead_id = (body.lead_id or "").strip() or str(uuid4())
    graph = get_graph()
    config = thread_config(lead_id)
    snapshot = graph.get_state(config)
    if getattr(snapshot, "interrupts", ()):
        raise HTTPException(status_code=409, detail="thread is waiting for human approval")
    message = (body.message or "").strip() or None
    if snapshot.values:
        if not message:
            raise HTTPException(status_code=400, detail="lead already exists; post a reply instead")
        result = graph.invoke(reply_input(message, body.channel), config)
        return public_view(result)
    state = initial_state(
        lead_id,
        message=message,
        channel=body.channel,
        name=body.name.strip(),
        email=body.email.strip(),
        phone=body.phone.strip(),
        company=body.company.strip(),
        role=body.role.strip(),
        source=body.source.strip(),
        industry=body.industry.strip(),
    )
    return public_view(graph.invoke(state, config))


@router.post("/webhooks/reply")
def webhook_reply(body: ReplyWebhook) -> dict[str, Any]:
    graph = get_graph()
    config = thread_config(body.lead_id)
    _ensure_not_waiting(graph, config)
    snapshot = graph.get_state(config)
    if snapshot.values:
        result = graph.invoke(reply_input(body.message.strip(), body.channel), config)
        return public_view(result)
    lead = get_lead_impl(body.lead_id)
    if not lead.get("found"):
        raise HTTPException(status_code=404, detail="unknown lead")
    profile = dict(lead.get("profile") or {})
    state = initial_state(
        body.lead_id,
        message=body.message.strip(),
        channel=body.channel,
        name=lead.get("name") or profile.get("name") or "",
        email=lead.get("email") or "",
        phone=lead.get("phone") or "",
        company=lead.get("company") or "",
        role=lead.get("role") or "",
        source=lead.get("source") or "",
        industry=lead.get("industry") or "",
        stage=lead.get("stage") or "ENGAGED",
        touchpoint_count=lead.get("touchpoint_count") or 0,
        last_angle_used=lead.get("last_angle_used") or "",
    )
    # initial_state already attached the human message; do not append it twice.
    if state["messages"] and isinstance(state["messages"][0], HumanMessage):
        state["messages"][0].additional_kwargs["channel"] = body.channel
    return public_view(graph.invoke(state, config))


@router.post("/hitl/approve")
def hitl_approve(body: ApprovalRequest) -> dict[str, Any]:
    if body.action == "edit" and not (body.edited_draft or "").strip():
        raise HTTPException(status_code=400, detail="edited_draft is required when action is edit")
    graph = get_graph()
    config = thread_config(body.lead_id)
    snapshot = graph.get_state(config)
    if not snapshot.values:
        raise HTTPException(status_code=404, detail="unknown lead")
    if not getattr(snapshot, "interrupts", ()):
        raise HTTPException(status_code=409, detail="thread is not waiting for approval")
    result = graph.invoke(
        Command(
            resume={
                "action": body.action,
                "draft": body.edited_draft,
                "edited_draft": body.edited_draft,
            }
        ),
        config,
    )
    return public_view(result)


@router.post("/reflection/run")
def reflection_run() -> dict[str, Any]:
    report = run_nightly_reflection()
    return {
        "threads_scanned": report.get("threads_scanned"),
        "clusters": report.get("clusters"),
        "prompt_improvements": report.get("prompt_improvements"),
        "source": report.get("source"),
        "output_dir": report.get("output_dir"),
        "playbook_diff": report.get("playbook_diff"),
    }
