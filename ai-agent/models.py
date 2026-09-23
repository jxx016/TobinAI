from typing import Optional
from pydantic import BaseModel, Field


class MaintenanceRequest(BaseModel):
    tenant_name: str
    tenant_phone: str
    property_address: str
    apartment_unit: str
    issue_description: str


class NotificationResult(BaseModel):
    """One SMS/email attempt. `ok` is delivery-attempt success, not ticket-save success."""
    channel: str
    to: Optional[str] = None
    ok: bool
    error: Optional[str] = None


class MaintenanceResponse(BaseModel):
    success: bool
    reference_number: str
    urgency: str
    category: str
    summary: str
    estimated_time: str
    ai_reasoning: list[str]
    notifications: list[NotificationResult] = Field(default_factory=list)


class StatusResponse(BaseModel):
    found: bool
    reference: Optional[str] = None
    status: Optional[str] = None
    urgency: Optional[str] = None
    category: Optional[str] = None
    summary: Optional[str] = None
    submitted: Optional[str] = None
    property: Optional[str] = None
    unit: Optional[str] = None


class ApproveOutreachRequest(BaseModel):
    request_id: str
