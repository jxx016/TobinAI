import os
import json
import re
from datetime import datetime, timezone
from typing import Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent
from db import get_conn
from tools import lookup_vendor_by_specialty, send_sms, send_email
from vendor_research import search_vendors_nearby, save_outreach_candidates
import psycopg2.extras

SYSTEM_PROMPT = """You are Tobin, a professional maintenance coordination assistant for landlords.

For each maintenance request you must:
1. Assess urgency: "Emergency" (flooding/gas/no heat in winter), "High" (24-48hrs), "Medium" (within a week), "Low" (routine)
2. Classify category: "plumbing", "electrical", "hvac", or "general"
3. Use the lookup_vendor_by_specialty tool to find the best vendor
4. Write a professional summary and handyman_notes

After calling the vendor lookup tool, respond ONLY with this JSON (no markdown, no extra text):
{
  "urgency": "Emergency|High|Medium|Low",
  "category": "plumbing|electrical|hvac|general",
  "summary": "Brief professional description",
  "handyman_notes": "Specific instructions for the handyman",
  "requires_photos": true/false,
  "estimated_time": "30min|1-2hrs|half-day|full-day",
  "vendor_id": <integer from tool result>,
  "vendor_name": "<name from tool result>",
  "vendor_phone": "<phone from tool result>",
  "vendor_email": "<email from tool result>"
}"""


def save_initial_request(state: dict) -> dict:
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            temp_id = f"REQ-{ts}-000"
            cur.execute(
                """
                INSERT INTO maintenance_requests
                  (request_id, tenant_name, tenant_phone, property_address, apartment_unit, issue_description, status)
                VALUES (%s, %s, %s, %s, %s, %s, 'pending')
                RETURNING id
                """,
                (
                    temp_id,
                    state["tenant_name"],
                    state["tenant_phone"],
                    state["property_address"],
                    state["apartment_unit"],
                    state["issue_description"],
                ),
            )
            row = cur.fetchone()

    return {**state, "db_id": row["id"], "ai_reasoning": ["📝 Request saved to database"]}


def analyze_issue(state: dict) -> dict:
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0,
    )
    agent = create_react_agent(llm, [lookup_vendor_by_specialty])

    prompt = (
        f"New maintenance request:\n"
        f"Tenant: {state['tenant_name']}\n"
        f"Phone: {state['tenant_phone']}\n"
        f"Property: {state['property_address']}\n"
        f"Unit: {state['apartment_unit']}\n"
        f"Issue: {state['issue_description']}"
    )

    result = agent.invoke({
        "messages": [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=prompt)]
    })

    last_msg = result["messages"][-1].content
    clean = re.sub(r"```(?:json)?", "", last_msg).strip().rstrip("`").strip()
    parsed = json.loads(clean)

    reasoning = state.get("ai_reasoning", [])
    reasoning += [
        f"⚡ Category: {parsed.get('category', 'general')}",
        f"🚨 Urgency: {parsed.get('urgency', 'medium')}",
        f"⏱️ Est. time: {parsed.get('estimated_time', '1-2hrs')}",
        f"🔍 Vendor: {parsed.get('vendor_name', 'TBD')}",
    ]

    return {
        **state,
        "urgency": parsed.get("urgency", "Medium"),
        "category": parsed.get("category", "general"),
        "summary": parsed.get("summary", state["issue_description"]),
        "handyman_notes": parsed.get("handyman_notes", ""),
        "requires_photos": parsed.get("requires_photos", False),
        "estimated_time": parsed.get("estimated_time", "1-2hrs"),
        "vendor_id": parsed.get("vendor_id"),
        "vendor_name": parsed.get("vendor_name"),
        "vendor_phone": parsed.get("vendor_phone"),
        "vendor_email": parsed.get("vendor_email"),
        "ai_reasoning": reasoning,
    }


def generate_reference(state: dict) -> dict:
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    request_id = f"TM-{date_str}-{str(state['db_id']).zfill(4)}"
    reasoning = state.get("ai_reasoning", [])
    reasoning.append(f"✅ Reference number: {request_id}")
    return {**state, "request_id": request_id, "ai_reasoning": reasoning}


def notify_tenant(state: dict) -> dict:
    urgency = state.get("urgency", "Medium").lower()
    if urgency == "emergency":
        msg = (
            f"🚨 URGENT: Hi {state['tenant_name']}, we received your emergency maintenance request "
            f"at {state['property_address']}. We are dispatching a vendor NOW. - Tobin AI"
        )
    else:
        msg = (
            f"Hi {state['tenant_name']}! We received your maintenance request "
            f"(Issue: {state['issue_description']}) at {state['property_address']}. "
            f"We're contacting a vendor now. Ref: {state['request_id']} - Tobin AI"
        )
    try:
        send_sms(state["tenant_phone"], msg)
    except Exception as e:
        print(f"Tenant SMS failed: {e}")

    reasoning = state.get("ai_reasoning", [])
    reasoning.append(f"📱 Tenant SMS sent to {state['tenant_phone']}")
    return {**state, "ai_reasoning": reasoning}


def notify_vendor(state: dict) -> dict:
    urgency = state.get("urgency", "Medium").lower()
    vendor_phone = state.get("vendor_phone")
    vendor_email = state.get("vendor_email")

    if urgency == "emergency":
        sms_body = (
            f"🚨 EMERGENCY MAINTENANCE 🚨\n"
            f"Property: {state['property_address']} Unit: {state['apartment_unit']}\n"
            f"Type: {state['category'].upper()}\n"
            f"Issue: {state['summary']}\n"
            f"Instructions: {state['handyman_notes']}\n"
            f"Est. time: {state['estimated_time']}\n"
            f"Tenant: {state['tenant_name']} 📞 {state['tenant_phone']}\n"
            f"⚡ Reply YES to accept"
        )
    else:
        sms_body = (
            f"[{urgency.upper()}] Maintenance request - {state['category'].upper()}\n"
            f"Property: {state['property_address']} Unit: {state['apartment_unit']}\n"
            f"Issue: {state['summary']}\n"
            f"Tenant: {state['tenant_name']} 📞 {state['tenant_phone']}\n"
            f"Reply YES to accept | Ref: {state['request_id']}"
        )

    if vendor_phone:
        try:
            send_sms(vendor_phone, sms_body)
        except Exception as e:
            print(f"Vendor SMS failed: {e}")

    if vendor_email:
        subject = f"[{urgency.upper()}] Maintenance - Unit {state['apartment_unit']} - {state['category'].upper()}"
        html = f"""
        <h2>Maintenance Request - {state['request_id']}</h2>
        <p><strong>Urgency:</strong> {state['urgency']}</p>
        <p><strong>Property:</strong> {state['property_address']}, Unit {state['apartment_unit']}</p>
        <p><strong>Category:</strong> {state['category']}</p>
        <p><strong>Summary:</strong> {state['summary']}</p>
        <p><strong>Instructions:</strong> {state['handyman_notes']}</p>
        <p><strong>Estimated time:</strong> {state['estimated_time']}</p>
        <hr/>
        <p><strong>Tenant:</strong> {state['tenant_name']} — {state['tenant_phone']}</p>
        """
        try:
            send_email(vendor_email, subject, html)
        except Exception as e:
            print(f"Vendor email failed: {e}")

    reasoning = state.get("ai_reasoning", [])
    reasoning.append(f"📨 Vendor notified: {state.get('vendor_name', 'N/A')}")
    return {**state, "ai_reasoning": reasoning}


def research_vendors(state: dict) -> dict:
    """Search Google Places for vendors when none found in DB."""
    category = state.get("category", "general")
    address = state.get("property_address", "")
    request_id = state.get("request_id", "")

    candidates = search_vendors_nearby(category, address)

    reasoning = state.get("ai_reasoning", [])
    if candidates:
        reasoning.append(f"🔎 Found {len(candidates)} vendors via Google Places")
        save_outreach_candidates(request_id, candidates, source="google_places")
        # Use the top result as the assigned vendor for notifications
        top = candidates[0]
        return {
            **state,
            "vendor_name": top["name"],
            "vendor_phone": top["phone"],
            "vendor_email": None,
            "researched_candidates": candidates,
            "ai_reasoning": reasoning,
        }
    else:
        reasoning.append("⚠️ No vendors found via Google Places — manual assignment needed")
        return {**state, "researched_candidates": [], "ai_reasoning": reasoning}


def outreach_vendors(state: dict) -> dict:
    """SMS all researched vendor candidates asking for availability."""
    candidates = state.get("researched_candidates", [])
    urgency = state.get("urgency", "Medium")
    request_id = state.get("request_id", "")

    msg = (
        f"Hi, this is Tobin AI (property maintenance coordination). "
        f"We have a {urgency} {state.get('category', 'general')} job at "
        f"{state['property_address']} Unit {state['apartment_unit']}. "
        f"Are you available? Reply YES or NO. Ref: {request_id}"
    )

    reached = 0
    for vendor in candidates:
        if vendor.get("phone"):
            try:
                send_sms(vendor["phone"], msg)
                reached += 1
            except Exception as e:
                print(f"Outreach SMS failed for {vendor['name']}: {e}")

    reasoning = state.get("ai_reasoning", [])
    reasoning.append(f"📲 Outreach sent to {reached} vendor(s) — awaiting reply")
    return {**state, "ai_reasoning": reasoning}


def update_db(state: dict) -> dict:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE maintenance_requests SET
                    request_id = %s,
                    category = %s,
                    urgency = %s,
                    summary = %s,
                    handyman_notes = %s,
                    ai_processed_at = NOW(),
                    last_updated_at = NOW()
                WHERE id = %s
                """,
                (
                    state["request_id"],
                    state.get("category"),
                    state.get("urgency"),
                    state.get("summary"),
                    state.get("handyman_notes"),
                    state["db_id"],
                ),
            )
    return state
