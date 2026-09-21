import os
import psycopg2.extras
from langchain_core.tools import tool
from twilio.rest import Client as TwilioClient
from agentmail import AgentMail
from db import get_conn


def _twilio_client():
    sid = (os.getenv("TWILIO_ACCOUNT_SID") or "").strip()
    token = (os.getenv("TWILIO_AUTH_TOKEN") or "").strip()
    if not sid or not token:
        raise RuntimeError(
            "Twilio not configured: TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set"
        )
    return TwilioClient(sid, token)


def _twilio_from() -> str:
    return os.getenv("TWILIO_PHONE_NUMBER", "+12064893667")


def _agentmail_client():
    key = (os.getenv("AGENTMAIL_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("AgentMail not configured: AGENTMAIL_API_KEY must be set")
    return AgentMail(api_key=key)


def _inbox_id() -> str:
    val = os.getenv("AGENTMAIL_INBOX_ID")
    if not val:
        raise RuntimeError("AGENTMAIL_INBOX_ID not set — run setup_inbox.py first")
    return val


@tool
def lookup_vendor_by_specialty(specialty: str) -> str:
    """Find the best available vendor for a maintenance category.

    Args:
        specialty: One of 'hvac', 'plumbing', 'electrical', 'general'
    """
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, name, phone, email, specialty, rating, hourly_rate
                FROM vendors
                WHERE specialty = %s AND is_active = true
                ORDER BY is_primary DESC, rating DESC
                LIMIT 1
                """,
                (specialty.lower().strip(),),
            )
            row = cur.fetchone()

    if not row:
        return f"No vendor found for specialty '{specialty}'"

    return (
        f"vendor_id={row['id']}, name={row['name']}, "
        f"phone={row['phone']}, email={row['email']}, "
        f"rating={row['rating']}"
    )


def send_sms(to: str, message: str) -> None:
    to = to.rstrip("!").strip()
    _twilio_client().messages.create(body=message, from_=_twilio_from(), to=to)


def send_email(to: str, subject: str, html_body: str) -> None:
    _agentmail_client().inboxes.messages.send(
        _inbox_id(),
        to=to,
        subject=subject,
        html=html_body,
    )
