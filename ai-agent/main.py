import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from models import MaintenanceRequest, MaintenanceResponse, StatusResponse
from graph import graph
from db import get_conn
from tools import send_sms
from vendor_research import mark_vendor_accepted, mark_vendor_declined, get_pending_outreach
import psycopg2.extras

app = FastAPI(title="Tobin AI", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "tobin-ai"}


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
            "researched_candidates": None,
        })

        return MaintenanceResponse(
            success=True,
            reference_number=result["request_id"],
            urgency=result.get("urgency", "Medium"),
            category=result.get("category", "general"),
            summary=result.get("summary", ""),
            estimated_time=result.get("estimated_time", "1-2hrs"),
            ai_reasoning=result.get("ai_reasoning", []),
        )
    except Exception as e:
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
