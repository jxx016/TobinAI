"""Follow-up polling and the nightly reflection job."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from src.agent.graph import follow_up_input, get_graph, initial_state, thread_config
from src.config import get_settings
from src.reflection.optimizer import run_nightly_reflection
from src.tools.crm import claim_due_jobs, get_lead_impl, set_job_status

logger = logging.getLogger(__name__)


def run_due_followups(now: datetime | None = None) -> int:
    """Fire due follow-ups. Threads waiting on a human are left alone."""

    graph = get_graph()
    ran = 0
    for job in claim_due_jobs(now or datetime.now(timezone.utc)):
        lead_id = job["lead_id"]
        config = thread_config(lead_id)
        try:
            snapshot = graph.get_state(config)
            if getattr(snapshot, "interrupts", ()):
                set_job_status(job["id"], "skipped")
                continue
            if getattr(snapshot, "values", None):
                graph.invoke(follow_up_input(), config)
            else:
                lead = get_lead_impl(lead_id)
                if not lead.get("found"):
                    set_job_status(job["id"], "failed")
                    continue
                profile = dict(lead.get("profile") or {})
                profile.update(
                    {
                        "name": lead.get("name") or profile.get("name") or "",
                        "email": lead.get("email") or "",
                        "phone": lead.get("phone") or "",
                        "company": lead.get("company") or "",
                        "role": lead.get("role") or "",
                        "source": lead.get("source") or "",
                        "industry": lead.get("industry") or "",
                        "stage": lead.get("stage") or "GHOSTING",
                        "touchpoint_count": lead.get("touchpoint_count") or 0,
                        "last_angle_used": lead.get("last_angle_used") or "",
                    }
                )
                state = initial_state(lead_id, **profile)
                state.update(follow_up_input())
                graph.invoke(state, config)
            set_job_status(job["id"], "done")
            ran += 1
        except Exception:
            logger.exception("follow-up failed for %s", lead_id)
            set_job_status(job["id"], "failed")
    return ran


def start_scheduler() -> BackgroundScheduler:
    settings = get_settings()
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        run_due_followups,
        IntervalTrigger(seconds=max(15, settings.followup_poll_seconds)),
        id="lead-chase-followups",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.add_job(
        run_nightly_reflection,
        CronTrigger(hour=settings.nightly_reflection_hour, minute=5),
        id="lead-chase-nightly-reflection",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    return scheduler
