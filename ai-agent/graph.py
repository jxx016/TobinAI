from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
from settings import auto_outreach_enabled
from nodes import (
    save_initial_request,
    analyze_issue,
    generate_reference,
    notify_tenant,
    notify_vendor,
    research_vendors,
    outreach_vendors,
    update_db,
)


class TobinState(TypedDict):
    # Input
    tenant_name: str
    tenant_phone: str
    property_address: str
    apartment_unit: str
    issue_description: str
    # Generated
    db_id: Optional[int]
    request_id: Optional[str]
    # AI analysis
    urgency: Optional[str]
    category: Optional[str]
    summary: Optional[str]
    handyman_notes: Optional[str]
    requires_photos: Optional[bool]
    estimated_time: Optional[str]
    # Vendor
    vendor_id: Optional[int]
    vendor_name: Optional[str]
    vendor_phone: Optional[str]
    vendor_email: Optional[str]
    # Tracking
    ai_reasoning: list[str]
    # Vendor research
    researched_candidates: Optional[list]
    status: Optional[str]


def _route_after_analysis(state: dict) -> str:
    """If AI found a vendor in DB, proceed normally. Otherwise research externally."""
    if state.get("vendor_phone"):
        return "generate_reference"
    return "research_vendors"


def _route_after_research(state: dict) -> str:
    """Cold Places SMS only when AUTO_OUTREACH is explicitly true."""
    if auto_outreach_enabled() and state.get("researched_candidates"):
        return "outreach_vendors"
    return "generate_reference"


def build_graph():
    workflow = StateGraph(TobinState)

    workflow.add_node("save_initial_request", save_initial_request)
    workflow.add_node("analyze_issue", analyze_issue)
    workflow.add_node("research_vendors", research_vendors)
    workflow.add_node("outreach_vendors", outreach_vendors)
    workflow.add_node("generate_reference", generate_reference)
    workflow.add_node("notify_tenant", notify_tenant)
    workflow.add_node("notify_vendor", notify_vendor)
    workflow.add_node("update_db", update_db)

    workflow.set_entry_point("save_initial_request")
    workflow.add_edge("save_initial_request", "analyze_issue")

    # If DB vendor found → skip research. If not → research; outreach only if AUTO_OUTREACH.
    workflow.add_conditional_edges("analyze_issue", _route_after_analysis, {
        "generate_reference": "generate_reference",
        "research_vendors": "research_vendors",
    })
    workflow.add_conditional_edges("research_vendors", _route_after_research, {
        "outreach_vendors": "outreach_vendors",
        "generate_reference": "generate_reference",
    })
    workflow.add_edge("outreach_vendors", "generate_reference")

    workflow.add_edge("generate_reference", "notify_tenant")
    workflow.add_edge("notify_tenant", "notify_vendor")
    workflow.add_edge("notify_vendor", "update_db")
    workflow.add_edge("update_db", END)

    return workflow.compile()


graph = build_graph()
