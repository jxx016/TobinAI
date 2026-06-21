import os
import psycopg2.extras
from langchain_core.tools import tool
from twilio.rest import Client as TwilioClient
from agentmail import AgentMail
from db import get_conn

twilio_client = TwilioClient(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN"),
)
TWILIO_FROM = os.getenv("TWILIO_PHONE_NUMBER", "+12064893667")

_agentmail = AgentMail(api_key=os.getenv("AGENTMAIL_API_KEY"))
TOBIN_INBOX_ID = os.getenv("AGENTMAIL_INBOX_ID")


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
    twilio_client.messages.create(body=message, from_=TWILIO_FROM, to=to)


def send_email(to: str, subject: str, html_body: str) -> None:
    _agentmail.inboxes.messages.send(
        TOBIN_INBOX_ID,
        to=to,
        subject=subject,
        html=html_body,
    )
