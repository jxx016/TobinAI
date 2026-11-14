"""Booking slots and links. Mock mode returns a stable sandbox URL."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone

from langchain_core.tools import tool

from src.config import get_settings

logger = logging.getLogger(__name__)


def _slug(lead_id: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]", "", lead_id or "")
    return cleaned or "lead"


def get_available_slots_impl(lead_id: str, timezone_name: str = "America/Los_Angeles") -> list[dict]:
    settings = get_settings()
    if not settings.mock_external_services and settings.calcom_api_key.strip() and settings.calcom_event_type_id:
        return _calcom_slots(settings, timezone_name)
    start = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    slots: list[dict] = []
    cursor = start + timedelta(days=1)
    while len(slots) < 4:
        if cursor.weekday() < 5:
            slot = cursor.replace(hour=17)
            slots.append(
                {
                    "start": slot.isoformat(),
                    "end": (slot + timedelta(minutes=15)).isoformat(),
                    "timezone": timezone_name,
                    "provider": "mock",
                }
            )
        cursor += timedelta(days=1)
    logger.info("mock slots lead_id=%s count=%s", lead_id, len(slots))
    return slots


def create_booking_link_impl(lead_id: str, event_name: str = "Tobin intro") -> str:
    settings = get_settings()
    slug = _slug(lead_id)
    if settings.mock_external_services or not settings.calcom_api_key.strip():
        if not settings.mock_external_services and not settings.calcom_api_key.strip():
            raise RuntimeError("CALCOM_API_KEY is required when MOCK_EXTERNAL_SERVICES=false")
        return f"https://cal.example.com/book/{slug}"
    username = settings.calcom_username.strip()
    if username:
        return f"https://cal.com/{username}/{event_name.replace(' ', '-').lower()}?lead={slug}"
    return f"https://cal.com/booking?eventTypeId={settings.calcom_event_type_id}&lead={slug}"


def _calcom_slots(settings, timezone_name: str) -> list[dict]:
    import httpx

    start = datetime.now(timezone.utc).date().isoformat()
    end = (datetime.now(timezone.utc) + timedelta(days=7)).date().isoformat()
    response = httpx.get(
        f"{settings.calcom_api_url.rstrip('/')}/slots",
        headers={"Authorization": f"Bearer {settings.calcom_api_key.strip()}"},
        params={
            "eventTypeId": settings.calcom_event_type_id,
            "start": start,
            "end": end,
            "timeZone": timezone_name,
        },
        timeout=20.0,
    )
    response.raise_for_status()
    payload = response.json()
    data = payload.get("data") or payload.get("slots") or {}
    slots: list[dict] = []
    if isinstance(data, dict):
        for day, entries in data.items():
            for entry in entries or []:
                start_at = entry.get("start") or entry.get("time")
                if start_at:
                    slots.append({"start": start_at, "timezone": timezone_name, "day": day, "provider": "calcom"})
    elif isinstance(data, list):
        for entry in data:
            if isinstance(entry, dict) and entry.get("start"):
                slots.append({"start": entry["start"], "timezone": timezone_name, "provider": "calcom"})
    return slots[:8]


@tool
def get_available_slots(lead_id: str, timezone_name: str = "America/Los_Angeles") -> list[dict]:
    """Return upcoming 15-minute intro slots. Mock mode synthesizes weekday times."""

    return get_available_slots_impl(lead_id=lead_id, timezone_name=timezone_name)


@tool
def create_booking_link(lead_id: str, event_name: str = "Tobin intro") -> str:
    """Return a booking URL. Mock mode returns a stable sandbox link and does not create a meeting."""

    return create_booking_link_impl(lead_id=lead_id, event_name=event_name)
