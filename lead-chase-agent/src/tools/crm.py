"""SQLite CRM tools. The same models run on Postgres when DATABASE_URL points there."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from langchain_core.tools import tool

from src.db.models import Lead, ReflectionLog, ScheduledJob, Touchpoint, utcnow
from src.db.session import session_scope


def _parse_dt(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _lead_dict(lead: Lead) -> dict:
    try:
        profile = json.loads(lead.profile_json or "{}")
    except json.JSONDecodeError:
        profile = {}
    if not isinstance(profile, dict):
        profile = {}
    return {
        "found": True,
        "lead_id": lead.id,
        "name": lead.name,
        "email": lead.email,
        "phone": lead.phone,
        "company": lead.company,
        "role": lead.role,
        "source": lead.source,
        "industry": lead.industry,
        "stage": lead.stage,
        "enrichment_notes": lead.enrichment_notes,
        "touchpoint_count": lead.touchpoint_count,
        "last_angle_used": lead.last_angle_used,
        "next_follow_up_at": lead.next_follow_up_at.isoformat() if lead.next_follow_up_at else None,
        "outcome_label": lead.outcome_label,
        "profile": profile,
    }


def get_lead_impl(lead_id: str) -> dict:
    with session_scope() as db:
        lead = db.get(Lead, lead_id)
        if lead is None:
            return {"found": False, "lead_id": lead_id, "profile": {}}
        return _lead_dict(lead)


def upsert_lead_impl(
    lead_id: str,
    name: str = "",
    email: str = "",
    phone: str = "",
    company: str = "",
    role: str = "",
    source: str = "",
    industry: str = "",
    enrichment_notes: str = "",
    stage: str = "NEW",
    touchpoint_count: int = 0,
    last_angle_used: str = "",
    next_follow_up_iso: str = "",
    outcome_label: str = "",
    profile_json: str = "",
) -> dict:
    with session_scope() as db:
        lead = db.get(Lead, lead_id)
        if lead is None:
            lead = Lead(id=lead_id)
            db.add(lead)
        lead.name = name
        lead.email = email
        lead.phone = phone
        lead.company = company
        lead.role = role
        lead.source = source
        lead.industry = industry
        lead.enrichment_notes = enrichment_notes
        lead.stage = stage or "NEW"
        lead.touchpoint_count = int(touchpoint_count or 0)
        lead.last_angle_used = last_angle_used or ""
        if next_follow_up_iso:
            lead.next_follow_up_at = _parse_dt(next_follow_up_iso)
        else:
            lead.next_follow_up_at = None
        if outcome_label:
            lead.outcome_label = outcome_label
        if profile_json:
            lead.profile_json = profile_json
        else:
            lead.profile_json = json.dumps(
                {
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "company": company,
                    "role": role,
                    "source": source,
                    "industry": industry,
                    "enrichment_notes": enrichment_notes,
                }
            )
        lead.updated_at = utcnow()
        db.flush()
        return _lead_dict(lead)


def insert_touchpoint(
    lead_id: str,
    channel: str,
    direction: str,
    body: str,
    angle: str = "",
    payload_json: str = "{}",
) -> dict:
    with session_scope() as db:
        row = Touchpoint(
            lead_id=lead_id,
            channel=channel or "system",
            direction=direction or "system",
            body=body or "",
            angle=angle or "",
            payload_json=payload_json or "{}",
        )
        db.add(row)
        db.flush()
        return {"id": row.id, "lead_id": lead_id, "channel": row.channel, "direction": row.direction}


def list_touchpoints(lead_id: str) -> list[dict]:
    with session_scope() as db:
        rows = db.query(Touchpoint).filter_by(lead_id=lead_id).order_by(Touchpoint.id.asc()).all()
        return [
            {
                "id": row.id,
                "lead_id": row.lead_id,
                "channel": row.channel,
                "direction": row.direction,
                "body": row.body,
                "angle": row.angle,
                "payload_json": row.payload_json,
            }
            for row in rows
        ]


def schedule_followup_impl(lead_id: str, run_at_iso: str, kind: str = "follow_up") -> dict:
    run_at = _parse_dt(run_at_iso)
    with session_scope() as db:
        pending = (
            db.query(ScheduledJob)
            .filter_by(lead_id=lead_id, status="pending", kind=kind)
            .all()
        )
        for row in pending:
            row.status = "cancelled"
        job = ScheduledJob(lead_id=lead_id, run_at=run_at, kind=kind, status="pending", payload_json="{}")
        db.add(job)
        db.flush()
        return {"id": job.id, "lead_id": lead_id, "run_at": run_at.isoformat(), "status": job.status}


def cancel_scheduled_followups(lead_id: str) -> int:
    with session_scope() as db:
        rows = db.query(ScheduledJob).filter_by(lead_id=lead_id, status="pending").all()
        for row in rows:
            row.status = "cancelled"
        return len(rows)


def claim_due_jobs(now: datetime | None = None) -> list[dict]:
    moment = now or datetime.now(timezone.utc)
    with session_scope() as db:
        rows = db.query(ScheduledJob).filter(ScheduledJob.status == "pending").all()
        claimed: list[dict] = []
        for row in rows:
            run_at = row.run_at
            if run_at is None:
                continue
            if run_at.tzinfo is None:
                run_at = run_at.replace(tzinfo=timezone.utc)
            if run_at <= moment:
                row.status = "running"
                claimed.append({"id": row.id, "lead_id": row.lead_id, "kind": row.kind})
        return claimed


def set_job_status(job_id: int, status: str) -> None:
    with session_scope() as db:
        row = db.get(ScheduledJob, job_id)
        if row is not None:
            row.status = status


def load_failure_threads() -> list[dict]:
    with session_scope() as db:
        leads = db.query(Lead).filter(Lead.stage.in_(["GHOSTING", "UNSUBSCRIBED"])).all()
        records: list[dict] = []
        for lead in leads:
            inbound = (
                db.query(Touchpoint)
                .filter_by(lead_id=lead.id, direction="inbound")
                .order_by(Touchpoint.id.asc())
                .all()
            )
            records.append(
                {
                    "lead_id": lead.id,
                    "stage": lead.stage,
                    "touchpoint_count": lead.touchpoint_count,
                    "last_angle_used": lead.last_angle_used,
                    "industry": lead.industry,
                    "role": lead.role,
                    "inbound_text": "\n".join(row.body for row in inbound),
                }
            )
        return records


def save_reflection_log(summary: str, report_json: str, playbook_diff: str) -> int:
    with session_scope() as db:
        row = ReflectionLog(summary=summary, report_json=report_json, playbook_diff=playbook_diff)
        db.add(row)
        db.flush()
        return int(row.id)


@tool
def get_lead(lead_id: str) -> dict:
    """Fetch a CRM lead, or a not-found payload when the id is unknown."""

    return get_lead_impl(lead_id)


@tool
def upsert_lead(
    lead_id: str,
    name: str = "",
    email: str = "",
    phone: str = "",
    company: str = "",
    role: str = "",
    source: str = "",
    industry: str = "",
    enrichment_notes: str = "",
    stage: str = "NEW",
    touchpoint_count: int = 0,
    last_angle_used: str = "",
    next_follow_up_iso: str = "",
    outcome_label: str = "",
    profile_json: str = "",
) -> dict:
    """Create or update a lead row, including stage, angle, and next follow-up."""

    return upsert_lead_impl(
        lead_id=lead_id,
        name=name,
        email=email,
        phone=phone,
        company=company,
        role=role,
        source=source,
        industry=industry,
        enrichment_notes=enrichment_notes,
        stage=stage,
        touchpoint_count=touchpoint_count,
        last_angle_used=last_angle_used,
        next_follow_up_iso=next_follow_up_iso,
        outcome_label=outcome_label,
        profile_json=profile_json,
    )


@tool
def log_touchpoint(
    lead_id: str,
    channel: str,
    direction: str,
    body: str,
    angle: str = "",
    payload_json: str = "{}",
) -> dict:
    """Append an inbound, outbound, or system interaction to the lead timeline."""

    return insert_touchpoint(
        lead_id=lead_id,
        channel=channel,
        direction=direction,
        body=body,
        angle=angle,
        payload_json=payload_json,
    )


@tool
def schedule_followup(lead_id: str, run_at_iso: str, kind: str = "follow_up") -> dict:
    """Replace any pending follow-up for this lead with a new run time."""

    return schedule_followup_impl(lead_id=lead_id, run_at_iso=run_at_iso, kind=kind)
