import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from langchain_core.tools import tool
from twilio.rest import Client as TwilioClient
from db import get_conn

twilio_client = TwilioClient(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN"),
)
TWILIO_FROM = os.getenv("TWILIO_PHONE_NUMBER", "+12064893667")


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
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = os.getenv("FROM_EMAIL", "jsoh0118@gmail.com")
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT", "587"))) as server:
        server.starttls()
        server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
        server.sendmail(msg["From"], to, msg.as_string())


import psycopg2.extras
