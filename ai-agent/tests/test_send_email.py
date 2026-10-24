"""AgentMail send uses a visible inbox when AGENTMAIL_INBOX_ID 404s. No network."""

import tools
from demo_leads import _email_error


class _Missing(Exception):
    def __init__(self):
        super().__init__("headers: secret, status_code: 404, body: Inbox not found")
        self.status_code = 404


class _Messages:
    def __init__(self, fail_ids=()):
        self.fail_ids = set(fail_ids)
        self.sent = []

    def send(self, inbox_id, **kwargs):
        if inbox_id in self.fail_ids:
            raise _Missing()
        self.sent.append((inbox_id, kwargs))


class _Inbox:
    def __init__(self, inbox_id, email="", display_name=""):
        self.inbox_id = inbox_id
        self.email = email
        self.display_name = display_name


class _Client:
    def __init__(self, messages, inboxes=(), created=None):
        self.messages = messages
        self._inboxes = list(inboxes)
        self.created = created
        self.list_calls = 0
        self.create_calls = 0
        holder = self

        class _Inboxes:
            def list(self, limit=20):
                holder.list_calls += 1
                return type("Listed", (), {"inboxes": holder._inboxes})()

            def create(self, **kwargs):
                holder.create_calls += 1
                return holder.created

            messages = holder.messages

        self.inboxes = _Inboxes()


def _env(monkeypatch):
    tools._resolved_inbox_id = None
    monkeypatch.setenv("AGENTMAIL_API_KEY", "test-key")
    monkeypatch.setenv("AGENTMAIL_INBOX_ID", "tobin")


def test_send_email_uses_configured_inbox(monkeypatch):
    _env(monkeypatch)
    messages = _Messages()
    monkeypatch.setattr(tools, "_agentmail_client", lambda: _Client(messages))
    tools.send_email("landlord@example.com", "Hi", "<p>x</p>")
    assert messages.sent[0][0] == "tobin"
    assert messages.sent[0][1]["to"] == "landlord@example.com"
    assert tools._resolved_inbox_id == "tobin"


def test_send_email_uses_matching_visible_inbox_when_configured_id_404s(monkeypatch):
    _env(monkeypatch)
    messages = _Messages(fail_ids={"tobin"})
    client = _Client(
        messages,
        inboxes=[_Inbox("tobin@agentmail.to", email="tobin@agentmail.to", display_name="Tobin")],
    )
    monkeypatch.setattr(tools, "_agentmail_client", lambda: client)
    tools.send_email("landlord@example.com", "Hi", "<p>x</p>")
    assert messages.sent[0][0] == "tobin@agentmail.to"
    assert client.list_calls == 1
    assert client.create_calls == 0
    assert tools._resolved_inbox_id == "tobin@agentmail.to"


def test_send_email_creates_inbox_when_none_are_visible(monkeypatch):
    _env(monkeypatch)
    messages = _Messages(fail_ids={"tobin"})
    client = _Client(messages, inboxes=[], created=_Inbox("tobin@agentmail.to", email="tobin@agentmail.to"))
    monkeypatch.setattr(tools, "_agentmail_client", lambda: client)
    tools.send_email("landlord@example.com", "Hi", "<p>lead</p>")
    assert client.create_calls == 1
    assert messages.sent[0][0] == "tobin@agentmail.to"


def test_email_error_hides_upstream_headers():
    class Err(Exception):
        def __init__(self):
            super().__init__("headers: {secret}, status_code: 404")
            self.body = type("Body", (), {"message": "Inbox not found"})()

    text = _email_error(Err())
    assert text == "Could not email lead: Inbox not found"
    assert "secret" not in text
