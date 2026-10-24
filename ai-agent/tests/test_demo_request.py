"""Demo-request capture emails LANDLORD_EMAIL. No AgentMail network calls."""

from fastapi.testclient import TestClient

from demo_leads import DemoLeadError, deliver_demo_lead, parse_demo_lead
from main import app

ORIGIN = "https://cool-cannoli-68cac9.netlify.app"

LEAD = {
    "email": "ada@example.com",
    "name": "Ada Landlord",
    "phone": "+15555550100",
    "property_count": 4,
    "message": "Need help with <leaks> & vendors",
    "source": "demo-request",
    "timestamp": "2026-10-24T09:00:00.000Z",
}


def _client():
    return TestClient(app)


def test_parse_requires_name_and_email():
    try:
        parse_demo_lead({"email": "ada@example.com", "name": "  "})
        raised = False
    except DemoLeadError as exc:
        raised = True
        assert exc.status_code == 400
        assert "name" in str(exc)
    assert raised

    try:
        parse_demo_lead({"email": "not-an-email", "name": "Ada"})
        raised = False
    except DemoLeadError as exc:
        raised = True
        assert "email" in str(exc)
    assert raised


def test_deliver_includes_lead_fields_and_escapes_html(monkeypatch):
    monkeypatch.setenv("LANDLORD_EMAIL", "landlord@example.com")
    sent = {}

    def fake(to, subject, html):
        sent["to"] = to
        sent["subject"] = subject
        sent["html"] = html

    lead = parse_demo_lead(LEAD)
    assert deliver_demo_lead(lead, fake) == "landlord@example.com"
    assert sent["to"] == "landlord@example.com"
    assert "Ada Landlord" in sent["subject"]
    assert "ada@example.com" in sent["html"]
    assert "+15555550100" in sent["html"]
    assert ">4<" in sent["html"] or "Properties:</strong> 4" in sent["html"]
    assert "demo-request" in sent["html"]
    assert "2026-10-24T09:00:00.000Z" in sent["html"]
    assert "&lt;leaks&gt;" in sent["html"]
    assert "<leaks>" not in sent["html"]


def test_subject_collapses_header_injection(monkeypatch):
    monkeypatch.setenv("LANDLORD_EMAIL", "landlord@example.com")
    sent = {}

    def fake(to, subject, html):
        sent["subject"] = subject
        sent["html"] = html

    lead = parse_demo_lead({**LEAD, "name": "Ada\r\nBcc: evil@example.com"})
    deliver_demo_lead(lead, fake)
    assert "\n" not in sent["subject"]
    assert "\r" not in sent["subject"]
    assert sent["subject"] == "New demo request — Ada Bcc: evil@example.com"
    assert "Ada Bcc: evil@example.com" in sent["html"]


def test_deliver_missing_landlord_email(monkeypatch):
    monkeypatch.delenv("LANDLORD_EMAIL", raising=False)
    try:
        deliver_demo_lead(parse_demo_lead(LEAD), lambda *_a, **_k: None)
        raised = False
    except DemoLeadError as exc:
        raised = True
        assert exc.status_code == 503
    assert raised


def test_post_demo_request_success_and_cors(monkeypatch):
    monkeypatch.setenv("LANDLORD_EMAIL", "landlord@example.com")
    sent = {}

    def fake(to, subject, html):
        sent["to"] = to
        sent["subject"] = subject
        sent["html"] = html

    monkeypatch.setattr("main.send_email", fake)
    response = _client().post(
        "/webhook/demo-request",
        json=LEAD,
        headers={"Origin": ORIGIN},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"]
    assert sent["to"] == "landlord@example.com"
    assert "Ada Landlord" in sent["html"]
    assert response.headers["access-control-allow-origin"] in {"*", ORIGIN}


def test_post_demo_request_rejects_invalid_lead_without_email(monkeypatch):
    called = {"n": 0}

    def fake(*_a, **_k):
        called["n"] += 1

    monkeypatch.setattr("main.send_email", fake)
    response = _client().post(
        "/webhook/demo-request",
        json={"email": "nope", "name": ""},
        headers={"Origin": ORIGIN},
    )
    assert response.status_code == 400
    assert response.json()["success"] is False
    assert called["n"] == 0


def test_post_demo_request_email_failure_is_not_success(monkeypatch):
    monkeypatch.setenv("LANDLORD_EMAIL", "landlord@example.com")

    def boom(*_a, **_k):
        raise RuntimeError("AgentMail down")

    monkeypatch.setattr("main.send_email", boom)
    response = _client().post("/webhook/demo-request", json=LEAD)
    assert response.status_code == 502
    body = response.json()
    assert body["success"] is False
    assert "AgentMail down" in body["error"]


def test_post_demo_request_unconfigured_landlord(monkeypatch):
    monkeypatch.delenv("LANDLORD_EMAIL", raising=False)
    monkeypatch.setattr("main.send_email", lambda *_a, **_k: None)
    response = _client().post("/webhook/demo-request", json=LEAD)
    assert response.status_code == 503
    assert response.json()["success"] is False
