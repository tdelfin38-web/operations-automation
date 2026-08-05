"""Reference webhook bridge for an anonymised Tracker → Messenger integration."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from flask import Flask, jsonify, request


@dataclass
class InMemoryEventStore:
    """Replace with a transactional persistent store in production."""

    processed: set[str] = field(default_factory=set)

    def claim(self, event_id: str) -> bool:
        if event_id in self.processed:
            return False
        self.processed.add(event_id)
        return True


@dataclass
class RecordingMessenger:
    """Safe local replacement for a Messenger Bot API client."""

    sent: list[dict[str, str | None]] = field(default_factory=list)

    def send(self, *, chat_id: str, text: str, thread_id: str | None) -> None:
        self.sent.append({"chat_id": chat_id, "thread_id": thread_id, "text": text})


def _message(issue: dict[str, Any]) -> str:
    attachments = issue.get("attachments", [])
    suffix = f"\nAttachments: {len(attachments)}" if attachments else ""
    return f"[{issue['key']}] Status: {issue['status']}\n{issue['summary']}{suffix}"


def create_app(
    *,
    webhook_secret: str | None = None,
    event_store: InMemoryEventStore | None = None,
    messenger: RecordingMessenger | None = None,
) -> Flask:
    app = Flask(__name__)
    app.config["WEBHOOK_SECRET"] = webhook_secret or os.getenv("WEBHOOK_SECRET", "")
    app.extensions["event_store"] = event_store or InMemoryEventStore()
    app.extensions["messenger"] = messenger or RecordingMessenger()

    @app.post("/webhooks/tracker")
    def tracker_webhook():
        if request.headers.get("X-Webhook-Secret") != app.config["WEBHOOK_SECRET"]:
            return jsonify(error="unauthorized"), 401
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify(error="invalid JSON"), 400
        event_id = payload.get("event_id")
        issue = payload.get("issue")
        required = ("key", "summary", "status")
        if not isinstance(event_id, str) or not isinstance(issue, dict) or any(not issue.get(key) for key in required):
            return jsonify(error="event_id and issue.key, issue.summary, issue.status are required"), 400
        chat_id = issue.get("chat_id") or os.getenv("DEFAULT_CHAT_ID")
        if not chat_id:
            return jsonify(error="chat_id is required"), 400
        store: InMemoryEventStore = app.extensions["event_store"]
        if not store.claim(event_id):
            return jsonify(status="duplicate"), 200
        client: RecordingMessenger = app.extensions["messenger"]
        client.send(chat_id=chat_id, thread_id=issue.get("thread_id"), text=_message(issue))
        return jsonify(status="accepted"), 202

    return app


app = create_app()
