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
    val = (os.getenv("AGENTMAIL_INBOX_ID") or "").strip()
    if not val:
        raise RuntimeError("AGENTMAIL_INBOX_ID not set — run setup_inbox.py first")
    return val


# Filled after a successful send so a bad AGENTMAIL_INBOX_ID does not list inboxes every time.
_resolved_inbox_id: str | None = None


def _missing_inbox(exc: Exception) -> bool:
    return getattr(exc, "status_code", None) == 404


def _inbox_label(inbox) -> str:
    inbox_id = str(getattr(inbox, "inbox_id", "") or "").strip()
    email = str(getattr(inbox, "email", "") or "").strip()
    return inbox_id or email


def _pick_inbox(configured: str, inboxes) -> str | None:
    """Prefer an inbox that matches AGENTMAIL_INBOX_ID, else the only visible one."""
    want = configured.strip().lower()
    exact = []
    partial = []
    labels = []
    for inbox in inboxes:
        label = _inbox_label(inbox)
        if not label:
            continue
        labels.append(label)
        email = str(getattr(inbox, "email", "") or "").strip().lower()
        display = str(getattr(inbox, "display_name", "") or "").strip().lower()
        local = email.split("@", 1)[0]
        identities = {label.lower(), email, local, display}
        identities.discard("")
        if want and want in identities:
            exact.append(label)
        elif want and any(want in item for item in identities):
            partial.append(label)
    if exact:
        return exact[0]
    if partial:
        return partial[0]
    if len(labels) == 1:
        return labels[0]
    return None


def _resolve_fallback_inbox(client, configured: str) -> str:
    listed = client.inboxes.list(limit=20)
    chosen = _pick_inbox(configured, getattr(listed, "inboxes", []) or [])
    if chosen:
        return chosen
    try:
        from agentmail.inboxes.types.create_inbox_request import CreateInboxRequest

        created = client.inboxes.create(
            request=CreateInboxRequest(
                username="tobin",
                display_name="Tobin AI",
                client_id="tobin-ai-main",
            )
        )
    except TypeError:
        created = client.inboxes.create(
            username="tobin",
            display_name="Tobin AI",
            client_id="tobin-ai-main",
        )
    label = _inbox_label(created)
    if not label:
        raise RuntimeError("AgentMail inbox not found and a replacement could not be created")
    return label


def _deliver_email(client, inbox_id: str, to: str, subject: str, html_body: str) -> None:
    client.inboxes.messages.send(
        inbox_id,
        to=to,
        subject=subject,
        html=html_body,
    )


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
    """Send via AgentMail. If AGENTMAIL_INBOX_ID 404s, use a visible inbox or create one."""
    global _resolved_inbox_id
    client = _agentmail_client()
    inbox_id = _resolved_inbox_id or _inbox_id()
    try:
        _deliver_email(client, inbox_id, to, subject, html_body)
    except Exception as exc:
        if not _missing_inbox(exc):
            raise
        fallback = _resolve_fallback_inbox(client, _inbox_id())
        if fallback == inbox_id:
            raise
        print(f"AgentMail inbox {inbox_id!r} not found; sending from {fallback}")
        _deliver_email(client, fallback, to, subject, html_body)
        _resolved_inbox_id = fallback
        return
    _resolved_inbox_id = inbox_id
