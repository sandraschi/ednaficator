"""Tests for ednaficator/concierge/email_tools.py and EmailConcierge."""

from __future__ import annotations

from ednaficator.concierge import email_tools
from ednaficator.concierge.email_concierge import EmailConcierge


def test_list_unread_summaries_parses_inbox(monkeypatch):
    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "emails": [
                    {
                        "id": "42",
                        "subject": "Hallo Edna",
                        "from": "Max <max@example.com>",
                        "date": "2026-07-28",
                        "text_body": "Kurzer Text für die Vorschau.",
                        "unread": True,
                    }
                ]
            }

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, path, params=None):
            assert path == "/api/inbox"
            assert params["unread_only"] is True
            return FakeResponse()

    monkeypatch.setattr(email_tools.httpx, "Client", FakeClient)
    rows = email_tools.list_unread_summaries(limit=3)
    assert len(rows) == 1
    assert rows[0].subject == "Hallo Edna"
    assert "Kurzer Text" in rows[0].preview


def test_send_short_message_success(monkeypatch):
    class FakeResponse:
        status_code = 200

        def json(self):
            return {"success": True, "message_id": "sent-1"}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, path, json=None):
            assert path == "/api/send"
            assert json["to"] == "edna@example.com"
            return FakeResponse()

    monkeypatch.setattr(email_tools.httpx, "Client", FakeClient)
    result = email_tools.send_short_message(
        to="edna@example.com",
        subject="Test",
        body="Servus",
    )
    assert result["success"] is True


def test_email_concierge_unread_empty(monkeypatch):
    monkeypatch.setattr(email_tools, "list_unread_summaries", lambda **kw: [])
    concierge = EmailConcierge()
    result = concierge.unread_summaries()
    assert result.success is True
    assert "Keine ungelesenen" in result.message


def test_email_concierge_send_validation():
    concierge = EmailConcierge()
    result = concierge.send(to="", subject="Hi", body="Body")
    assert result.success is False
