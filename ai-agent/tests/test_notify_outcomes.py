"""Failed SMS/email must not claim sent. No real Twilio/AgentMail calls."""

from fastapi.testclient import TestClient

from nodes import notify_tenant, notify_vendor, _email_landlord_approval


def _tenant_state(**overrides):
    state = {
        "tenant_name": "Ada",
        "tenant_phone": "+15555550100",
        "property_address": "1 Main St",
        "apartment_unit": "2A",
        "issue_description": "Kitchen leak",
        "request_id": "TM-TEST-0001",
        "urgency": "Medium",
        "ai_reasoning": ["📝 Request saved"],
        "notifications": [],
    }
    state.update(overrides)
    return state


def _vendor_state(**overrides):
    state = _tenant_state(
        category="plumbing",
        summary="Kitchen leak",
        handyman_notes="Shut off valve",
        estimated_time="1-2hrs",
        vendor_name="City Plumbing Co",
        vendor_phone="+15552345678",
        vendor_email="plumber@example.com",
    )
    state.update(overrides)
    return state


def _boom(message):
    def _raise(*_a, **_k):
        raise RuntimeError(message)

    return _raise


def test_notify_tenant_failure_does_not_claim_sent(monkeypatch):
    monkeypatch.setattr("nodes.send_sms", _boom("Twilio 21211 Invalid 'To'"))

    out = notify_tenant(_tenant_state())
    joined = "\n".join(out["ai_reasoning"])
    assert "Tenant SMS sent" not in joined
    assert "❌" in joined
    assert "Twilio 21211" in joined
    assert out["notifications"] == [
        {
            "channel": "sms",
            "to": "+15555550100",
            "ok": False,
            "error": "Twilio 21211 Invalid 'To'",
        }
    ]


def test_notify_tenant_missing_twilio_env_does_not_claim_sent_or_call_network(monkeypatch):
    """Real send_sms, no mock: missing env must fail locally (no Twilio HTTP)."""
    monkeypatch.delenv("TWILIO_ACCOUNT_SID", raising=False)
    monkeypatch.delenv("TWILIO_AUTH_TOKEN", raising=False)

    out = notify_tenant(_tenant_state())
    joined = "\n".join(out["ai_reasoning"])
    assert "Tenant SMS sent" not in joined
    assert "❌" in joined
    assert out["notifications"][0]["ok"] is False
    assert "TWILIO_ACCOUNT_SID" in (out["notifications"][0]["error"] or "")
    called = {}

    def ok(to, msg):
        called["to"] = to
        called["msg"] = msg

    monkeypatch.setattr("nodes.send_sms", ok)
    out = notify_tenant(_tenant_state())
    assert any("Tenant SMS sent to +15555550100" in line for line in out["ai_reasoning"])
    assert "❌" not in "\n".join(out["ai_reasoning"])
    assert out["notifications"][0]["ok"] is True
    assert out["notifications"][0]["error"] is None
    assert called["to"] == "+15555550100"


def test_notify_vendor_failure_does_not_claim_notified(monkeypatch):
    monkeypatch.setattr("nodes.send_sms", _boom("Twilio timeout"))
    monkeypatch.setattr("nodes.send_email", _boom("AgentMail 401"))

    out = notify_vendor(_vendor_state())
    joined = "\n".join(out["ai_reasoning"])
    assert "Vendor notified" not in joined
    assert "Vendor SMS sent" not in joined
    assert "Vendor email sent" not in joined
    assert "❌" in joined
    assert all(n["ok"] is False for n in out["notifications"])
    assert {n["channel"] for n in out["notifications"]} == {"sms", "email"}


def test_notify_vendor_success_claims_notified(monkeypatch):
    monkeypatch.setattr("nodes.send_sms", lambda *_a, **_k: None)
    monkeypatch.setattr("nodes.send_email", lambda *_a, **_k: None)

    out = notify_vendor(_vendor_state())
    joined = "\n".join(out["ai_reasoning"])
    assert "Vendor notified: City Plumbing Co" in joined
    assert "❌" not in joined
    assert all(n["ok"] is True for n in out["notifications"])
    assert len(out["notifications"]) == 2


def test_notify_vendor_sms_fail_email_ok_records_both(monkeypatch):
    monkeypatch.setattr("nodes.send_sms", _boom("Twilio timeout"))
    monkeypatch.setattr("nodes.send_email", lambda *_a, **_k: None)

    out = notify_vendor(_vendor_state())
    joined = "\n".join(out["ai_reasoning"])
    assert "Vendor SMS sent" not in joined
    assert "Vendor notified: City Plumbing Co" in joined
    assert "❌" in joined
    sms = next(n for n in out["notifications"] if n["channel"] == "sms")
    email = next(n for n in out["notifications"] if n["channel"] == "email")
    assert sms["ok"] is False
    assert "Twilio timeout" in sms["error"]
    assert email["ok"] is True


def test_notify_vendor_places_gate_does_not_send(monkeypatch):
    sent = []
    monkeypatch.setattr("nodes.send_sms", lambda *_a, **_k: sent.append("sms"))
    monkeypatch.setattr("nodes.send_email", lambda *_a, **_k: sent.append("email"))

    out = notify_vendor(
        _vendor_state(
            researched_candidates=[{"name": "X"}],
            status="awaiting_vendor_approval",
        )
    )
    assert sent == []
    assert "Vendor notified" not in "\n".join(out["ai_reasoning"])
    assert "awaiting human approval" in "\n".join(out["ai_reasoning"])


def test_email_landlord_approval_failure_does_not_claim_sent(monkeypatch):
    monkeypatch.setenv("LANDLORD_EMAIL", "landlord@example.com")
    monkeypatch.setattr("nodes.send_email", _boom("AgentMail down"))

    out = _email_landlord_approval("TM-TEST-0001", _tenant_state(), [])
    joined = "\n".join(out["ai_reasoning"])
    assert "Landlord approval email sent" not in joined
    assert "❌" in joined
    assert out["notifications"][0]["ok"] is False
    assert "AgentMail down" in out["notifications"][0]["error"]


def test_email_landlord_approval_success_claims_sent(monkeypatch):
    monkeypatch.setenv("LANDLORD_EMAIL", "landlord@example.com")
    monkeypatch.setattr("nodes.send_email", lambda *_a, **_k: None)

    out = _email_landlord_approval("TM-TEST-0001", _tenant_state(), [])
    assert any(
        "Landlord approval email sent to landlord@example.com" in line
        for line in out["ai_reasoning"]
    )
    assert out["notifications"][0]["ok"] is True


def test_email_landlord_missing_env_is_visible(monkeypatch):
    monkeypatch.delenv("LANDLORD_EMAIL", raising=False)

    out = _email_landlord_approval("TM-TEST-0001", _tenant_state(), [])
    assert out["notifications"][0]["ok"] is False
    assert out["notifications"][0]["error"] == "LANDLORD_EMAIL not set"
    assert "❌" in "\n".join(out["ai_reasoning"])
    assert "Landlord approval email sent" not in "\n".join(out["ai_reasoning"])


def test_webhook_exposes_notification_failures(monkeypatch):
    import main

    def fake_invoke(state):
        return {
            **state,
            "request_id": "TM-TEST-0001",
            "urgency": "Medium",
            "category": "plumbing",
            "summary": "leak",
            "estimated_time": "1-2hrs",
            "ai_reasoning": ["❌ Tenant SMS failed to +15555550100: Twilio 21211"],
            "notifications": [
                {
                    "channel": "sms",
                    "to": "+15555550100",
                    "ok": False,
                    "error": "Twilio 21211",
                }
            ],
        }

    monkeypatch.setattr(main.graph, "invoke", fake_invoke)
    client = TestClient(main.app)
    response = client.post(
        "/webhook/maintenance-request",
        json={
            "tenant_name": "Ada",
            "tenant_phone": "+15555550100",
            "property_address": "1 Main",
            "apartment_unit": "2A",
            "issue_description": "leak",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["reference_number"] == "TM-TEST-0001"
    assert body["notifications"][0]["ok"] is False
    assert body["notifications"][0]["error"] == "Twilio 21211"
    assert "Tenant SMS sent" not in "".join(body["ai_reasoning"])


def test_health_env_presence_flags_not_values(monkeypatch):
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "ACsecretvalue")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "auth-secret")
    monkeypatch.setenv("TWILIO_PHONE_NUMBER", "+12065550100")
    monkeypatch.setenv("AGENTMAIL_API_KEY", "am-secret")
    monkeypatch.setenv("AGENTMAIL_INBOX_ID", "tobin")
    monkeypatch.delenv("LANDLORD_EMAIL", raising=False)

    import main

    client = TestClient(main.app)
    body = client.get("/health").json()
    dumped = str(body)
    assert "ACsecretvalue" not in dumped
    assert "auth-secret" not in dumped
    assert "am-secret" not in dumped
    assert body["status"] == "ok"
    assert body["twilio_configured"] is True
    assert body["agentmail_configured"] is True
    assert body["landlord_email_configured"] is False
    assert body["demo_request"] is True
    assert body["agentmail_inbox_fallback"] is True
