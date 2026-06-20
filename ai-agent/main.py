import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import MaintenanceRequest, MaintenanceResponse, StatusResponse
from graph import graph
from db import get_conn
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
