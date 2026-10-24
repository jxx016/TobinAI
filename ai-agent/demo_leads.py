"""Landlord demo / waitlist leads. Email only — no n8n, no database."""

import html
import os
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_SUCCESS_MESSAGE = "Demo request received. We'll be in touch within 24 hours!"


class DemoLeadError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class DemoLead(BaseModel):
    model_config = ConfigDict(extra="ignore")

    email: str
    name: str
    phone: str = ""
    property_count: str = ""
    message: str = ""
    source: str = ""
    timestamp: str = ""

    @field_validator(
        "email",
        "name",
        "phone",
        "property_count",
        "message",
        "source",
        "timestamp",
        mode="before",
    )
    @classmethod
    def _coerce(cls, value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @field_validator("name")
    @classmethod
    def _name(cls, value: str) -> str:
        if not value:
            raise ValueError("name is required")
        if len(value) > 200:
            raise ValueError("name is too long")
        return value

    @field_validator("email")
    @classmethod
    def _email(cls, value: str) -> str:
        if len(value) > 320 or not _EMAIL.fullmatch(value):
            raise ValueError("a valid email is required")
        return value

    @field_validator("message")
    @classmethod
    def _message(cls, value: str) -> str:
        if len(value) > 4000:
            raise ValueError("message is too long")
        return value

    @field_validator("phone", "property_count", "source", "timestamp")
    @classmethod
    def _bounded(cls, value: str) -> str:
        if len(value) > 500:
            raise ValueError("field is too long")
        return value


def parse_demo_lead(payload: Any) -> DemoLead:
    if not isinstance(payload, dict):
        raise DemoLeadError("JSON object is required")
    try:
        return DemoLead.model_validate(payload)
    except ValidationError as exc:
        msg = exc.errors()[0]["msg"]
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, ") :]
        raise DemoLeadError(msg) from exc


def _cell(value: str) -> str:
    text = " ".join(value.split())
    return html.escape(text) if text else "—"


def demo_lead_email(lead: DemoLead) -> tuple[str, str]:
    subject_name = " ".join(lead.name.split())
    subject = f"New demo request — {subject_name}"
    body = f"""
    <h2>New Tobin demo request</h2>
    <p>A landlord submitted the waitlist / demo form.</p>
    <ul>
      <li><strong>Name:</strong> {_cell(lead.name)}</li>
      <li><strong>Email:</strong> {_cell(lead.email)}</li>
      <li><strong>Phone:</strong> {_cell(lead.phone)}</li>
      <li><strong>Properties:</strong> {_cell(lead.property_count)}</li>
      <li><strong>Source:</strong> {_cell(lead.source)}</li>
      <li><strong>Submitted:</strong> {_cell(lead.timestamp)}</li>
    </ul>
    <h3>Message</h3>
    <p>{_cell(lead.message)}</p>
    """
    return subject, body


def success_body() -> dict:
    return {"success": True, "message": _SUCCESS_MESSAGE}


def deliver_demo_lead(lead: DemoLead, send) -> str:
    """Email the lead to LANDLORD_EMAIL. Returns the destination address."""
    to = (os.getenv("LANDLORD_EMAIL") or "").strip()
    if not to or any(ch in to for ch in "\r\n"):
        raise DemoLeadError("LANDLORD_EMAIL is not configured", status_code=503)
    subject, html_body = demo_lead_email(lead)
    try:
        send(to, subject, html_body)
    except Exception as exc:
        raise DemoLeadError(f"Could not email lead: {exc}", status_code=502) from exc
    return to
