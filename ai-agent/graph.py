from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
from nodes import (
    save_initial_request,
    analyze_issue,
    generate_reference,
    notify_tenant,
    notify_vendor,
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


def build_graph():
    workflow = StateGraph(TobinState)

    workflow.add_node("save_initial_request", save_initial_request)
    workflow.add_node("analyze_issue", analyze_issue)
    workflow.add_node("generate_reference", generate_reference)
    workflow.add_node("notify_tenant", notify_tenant)
    workflow.add_node("notify_vendor", notify_vendor)
    workflow.add_node("update_db", update_db)

    workflow.set_entry_point("save_initial_request")
    workflow.add_edge("save_initial_request", "analyze_issue")
    workflow.add_edge("analyze_issue", "generate_reference")
    workflow.add_edge("generate_reference", "notify_tenant")
    workflow.add_edge("notify_tenant", "notify_vendor")
    workflow.add_edge("notify_vendor", "update_db")
    workflow.add_edge("update_db", END)

    return workflow.compile()


graph = build_graph()
