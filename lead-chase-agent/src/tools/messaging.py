"""Email and SMS/WhatsApp adapters. Mock mode records the payload and prints it."""

from __future__ import annotations

import json
import logging

from langchain_core.tools import tool

from src.config import get_settings
from src.tools.crm import insert_touchpoint

logger = logging.getLogger(__name__)


def _record(channel: str, direction: str, lead_id: str, body: str, angle: str, payload: dict) -> dict:
    line = (
        f"[lead-chase-mock] channel={channel} to={payload.get('to')} "
        f"lead_id={lead_id} bytes={len(body)}"
    )
    logger.info(line)
    print(line)
    saved = insert_touchpoint(
        lead_id=lead_id,
        channel=channel,
        direction=direction,
        body=body,
        angle=angle,
        payload_json=json.dumps(payload),
    )
    return {"status": "mocked", "channel": channel, "to": payload.get("to"), "touchpoint_id": saved["id"]}


def send_email_impl(to: str, subject: str, body: str, lead_id: str, angle: str = "") -> dict:
    settings = get_settings()
    payload = {"to": to, "subject": subject, "body": body, "lead_id": lead_id, "provider": "mock"}
    if settings.mock_external_services:
        return _record("email", "outbound", lead_id, body, angle, payload)
    if not settings.resend_api_key.strip():
        raise RuntimeError("RESEND_API_KEY is required when MOCK_EXTERNAL_SERVICES=false")
    import httpx

    response = httpx.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {settings.resend_api_key.strip()}"},
        json={
            "from": settings.resend_from_email,
            "to": [to],
            "subject": subject,
            "text": body,
        },
        timeout=20.0,
    )
    response.raise_for_status()
    data = response.json()
    payload["provider"] = "resend"
    payload["id"] = data.get("id")
    saved = insert_touchpoint(
        lead_id=lead_id,
        channel="email",
        direction="outbound",
        body=body,
        angle=angle,
        payload_json=json.dumps(payload),
    )
    return {"status": "sent", "provider": "resend", "id": data.get("id"), "touchpoint_id": saved["id"]}


def send_sms_or_whatsapp_impl(
    to: str,
    body: str,
    lead_id: str,
    channel: str = "sms",
    angle: str = "",
) -> dict:
    settings = get_settings()
    channel_name = "whatsapp" if channel == "whatsapp" else "sms"
    payload = {"to": to, "body": body, "lead_id": lead_id, "channel": channel_name, "provider": "mock"}
    if settings.mock_external_services:
        return _record(channel_name, "outbound", lead_id, body, angle, payload)
    if not (settings.twilio_account_sid and settings.twilio_auth_token and settings.twilio_from_number):
        raise RuntimeError("Twilio credentials are required when MOCK_EXTERNAL_SERVICES=false")
    import httpx

    from_number = settings.twilio_from_number
    destination = to
    if channel_name == "whatsapp":
        from_number = settings.twilio_whatsapp_from or f"whatsapp:{settings.twilio_from_number}"
        if not destination.startswith("whatsapp:"):
            destination = f"whatsapp:{destination}"
    response = httpx.post(
        f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}/Messages.json",
        auth=(settings.twilio_account_sid, settings.twilio_auth_token),
        data={"From": from_number, "To": destination, "Body": body},
        timeout=20.0,
    )
    response.raise_for_status()
    data = response.json()
    payload["provider"] = "twilio"
    payload["id"] = data.get("sid")
    payload["to"] = destination
    saved = insert_touchpoint(
        lead_id=lead_id,
        channel=channel_name,
        direction="outbound",
        body=body,
        angle=angle,
        payload_json=json.dumps(payload),
    )
    return {"status": "sent", "provider": "twilio", "id": data.get("sid"), "touchpoint_id": saved["id"]}


@tool
def send_email(to: str, subject: str, body: str, lead_id: str, angle: str = "") -> dict:
    """Send an email. In mock mode, log the payload to the CRM and the console."""

    return send_email_impl(to=to, subject=subject, body=body, lead_id=lead_id, angle=angle)


@tool
def send_sms_or_whatsapp(to: str, body: str, lead_id: str, channel: str = "sms", angle: str = "") -> dict:
    """Send an SMS or WhatsApp message. In mock mode, log the payload instead of delivering it."""

    return send_sms_or_whatsapp_impl(to=to, body=body, lead_id=lead_id, channel=channel, angle=angle)
