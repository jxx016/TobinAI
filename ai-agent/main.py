import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import Body, FastAPI, HTTPException, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from models import MaintenanceRequest, MaintenanceResponse, StatusResponse, ApproveOutreachRequest
from graph import graph
from db import get_conn
from demo_leads import DemoLeadError, deliver_demo_lead, parse_demo_lead, success_body
from tools import send_email, send_sms
from vendor_research import (
    mark_vendor_accepted,
    mark_vendor_declined,
    get_pending_outreach,
    send_unsent_outreach,
)
from settings import approve_key_ok
import psycopg2.extras


def _env_present(*names: str) -> bool:
    """True when every named env var is set and non-empty. Never returns the values."""
    return all(bool((os.getenv(n) or "").strip()) for n in names)


app = FastAPI(title="Tobin AI", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "tobin-ai",
        "twilio_configured": _env_present(
            "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER"
        ),
        "agentmail_configured": _env_present("AGENTMAIL_API_KEY", "AGENTMAIL_INBOX_ID"),
        "landlord_email_configured": _env_present("LANDLORD_EMAIL"),
        "demo_request": True,
    }


@app.post("/webhook/demo-request")
async def demo_request(payload: dict = Body(...)):
    """Capture a waitlist/demo lead and email it to LANDLORD_EMAIL.

    The cool-cannoli SPA posts here via the Netlify function. HTTP 200 is what
    the form treats as success (thank-you state + Meta Lead). A failed email
    must not return success.
    """
    try:
        lead = parse_demo_lead(payload)
        deliver_demo_lead(lead, send_email)
    except DemoLeadError as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "error": exc.message},
        )
    return success_body()


@app.post("/webhook/maintenance-request", response_model=MaintenanceResponse)
async def maintenance_request(req: MaintenanceRequest):
    try:
        result = graph.invoke({
            "tenant_name": req.tenant_name,
            "tenant_phone": req.tenant_phone,
            "property_address": req.property_address,
            "apartment_unit": req.apartment_unit,
            "issue_description": req.issue_description,
            "db_id": None,
            "request_id": None,
            "urgency": None,
            "category": None,
            "summary": None,
            "handyman_notes": None,
            "requires_photos": None,
            "estimated_time": None,
            "vendor_id": None,
            "vendor_name": None,
            "vendor_phone": None,
            "vendor_email": None,
            "ai_reasoning": [],
            "notifications": [],
            "researched_candidates": None,
            "status": None,
        })

        return MaintenanceResponse(
            success=True,
            reference_number=result["request_id"],
            urgency=result.get("urgency", "Medium"),
            category=result.get("category", "general"),
            summary=result.get("summary", ""),
            estimated_time=result.get("estimated_time", "1-2hrs"),
            ai_reasoning=result.get("ai_reasoning", []),
            notifications=result.get("notifications") or [],
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhook/vendor-reply")
async def vendor_reply(From: str = Form(...), Body: str = Form(...)):
    """Twilio calls this endpoint when a vendor replies to an outreach SMS."""
    reply = Body.strip().upper()
    vendor_phone = From.strip()

    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT vo.id, vo.request_id, vo.vendor_name,
                       mr.tenant_name, mr.tenant_phone, mr.property_address,
                       mr.apartment_unit, mr.urgency, mr.category
                FROM vendor_outreach vo
                JOIN maintenance_requests mr ON mr.request_id = vo.request_id
                WHERE vo.vendor_phone = %s AND vo.accepted IS NULL
                ORDER BY vo.id ASC
                LIMIT 1
                """,
                (vendor_phone,),
            )
            outreach = cur.fetchone()

    if not outreach:
        return {"message": "No pending outreach found"}

    if reply.startswith("YES"):
        mark_vendor_accepted(outreach["id"])

        confirmation = (
            f"✅ Thank you {outreach['vendor_name']}! You've been assigned:\n"
            f"Ref: {outreach['request_id']}\n"
            f"Property: {outreach['property_address']} Unit {outreach['apartment_unit']}\n"
            f"Tenant: {outreach['tenant_name']} 📞 {outreach['tenant_phone']}"
        )
        try:
            send_sms(vendor_phone, confirmation)
        except Exception as e:
            print(f"Confirmation SMS failed: {e}")

        landlord_email = os.getenv("LANDLORD_EMAIL")
        if landlord_email:
            from tools import send_email
            try:
                send_email(
                    landlord_email,
                    f"Vendor Confirmed — {outreach['request_id']}",
                    f"<p>{outreach['vendor_name']} has accepted the {outreach['urgency']} "
                    f"{outreach['category']} job at {outreach['property_address']}.</p>"
                    f"<p>Ref: {outreach['request_id']}</p>",
                )
            except Exception as e:
                print(f"Landlord email failed: {e}")

    elif reply.startswith("NO"):
        mark_vendor_declined(outreach["id"])
        remaining = get_pending_outreach(outreach["request_id"])
        if not remaining:
            try:
                send_sms(
                    outreach["tenant_phone"],
                    f"Hi {outreach['tenant_name']}, we're still searching for a vendor for your request "
                    f"({outreach['request_id']}). We'll update you shortly. - Tobin AI",
                )
            except Exception:
                pass

    return {"message": "Reply processed"}


@app.get("/webhook/check-status", response_model=StatusResponse)
async def check_status(ref: str):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT request_id, status, urgency, category, summary,
                       created_at, property_address, apartment_unit
                FROM maintenance_requests
                WHERE request_id = %s
                """,
                (ref,),
            )
            row = cur.fetchone()

    if not row:
        return StatusResponse(found=False)

    return StatusResponse(
        found=True,
        reference=row["request_id"],
        status=row["status"],
        urgency=row["urgency"],
        category=row["category"],
        summary=row["summary"],
        submitted=row["created_at"].isoformat() if row["created_at"] else None,
        property=row["property_address"],
        unit=row["apartment_unit"],
    )


@app.post("/webhook/approve-outreach")
async def approve_outreach(
    body: ApproveOutreachRequest,
    x_tobin_approve_key: str | None = Header(default=None, alias="X-Tobin-Approve-Key"),
):
    """Send pending Places outreach SMS after a human approves the candidate list."""
    if not approve_key_ok(x_tobin_approve_key):
        raise HTTPException(status_code=401, detail="Invalid or missing approve key")

    request_id = body.request_id.strip()
    if not request_id:
        raise HTTPException(status_code=400, detail="request_id is required")

    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT request_id, status FROM maintenance_requests WHERE request_id = %s",
                (request_id,),
            )
            row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Request not found")

    sent = send_unsent_outreach(request_id)
    return {
        "success": True,
        "request_id": request_id,
        "sms_sent": sent,
        "idempotent": sent == 0,
        "message": (
            f"Sent outreach SMS to {sent} vendor(s)"
            if sent
            else "No unsent Places outreach (already sent or none pending)"
        ),
    }
