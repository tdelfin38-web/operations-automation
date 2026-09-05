from tracker_bridge.app import InMemoryEventStore, RecordingMessenger, create_app


def payload(**issue_updates):
    issue = {
        "key": "OPS-42",
        "summary": "Procurement request: project Alpha",
        "status": "Under review",
        "chat_id": "chat-procurement",
        "thread_id": "thread-ops-42",
        "attachments": [],
    }
    issue.update(issue_updates)
    return {"event_id": "evt-42", "event_type": "issue.status_changed", "issue": issue}


def client():
    messenger = RecordingMessenger()
    app = create_app(webhook_secret="test-secret", event_store=InMemoryEventStore(), messenger=messenger)
    return app.test_client(), messenger


def post(test_client, body):
    return test_client.post("/webhooks/tracker", json=body, headers={"X-Webhook-Secret": "test-secret"})


def test_issue_event_sends_routed_message():
    test_client, messenger = client()
    response = post(test_client, payload())
    assert response.status_code == 202
    assert messenger.sent == [{
        "chat_id": "chat-procurement",
        "thread_id": "thread-ops-42",
        "text": "[OPS-42] Status: Under review\nProcurement request: project Alpha",
    }]


def test_status_change_uses_new_event_and_same_thread():
    test_client, messenger = client()
    first = payload(status="Approved")
    second = payload(status="Paid")
    second["event_id"] = "evt-43"
    post(test_client, first)
    response = post(test_client, second)
    assert response.status_code == 202
    assert len(messenger.sent) == 2
    assert messenger.sent[-1]["thread_id"] == "thread-ops-42"
    assert "Paid" in messenger.sent[-1]["text"]


def test_attachment_event_reports_count_without_attachment_url():
    test_client, messenger = client()
    response = post(test_client, payload(attachments=[{"id": "file-1", "name": "invoice.pdf", "url": "https://secret.invalid/file"}]))
    assert response.status_code == 202
    assert "Attachments: 1" in messenger.sent[0]["text"]
    assert "secret.invalid" not in messenger.sent[0]["text"]


def test_duplicate_event_does_not_send_second_message():
    test_client, messenger = client()
    post(test_client, payload())
    response = post(test_client, payload())
    assert response.status_code == 200
    assert response.get_json() == {"status": "duplicate"}
    assert len(messenger.sent) == 1


def test_invalid_secret_is_rejected_without_delivery():
    test_client, messenger = client()
    response = test_client.post("/webhooks/tracker", json=payload(), headers={"X-Webhook-Secret": "wrong"})
    assert response.status_code == 401
    assert messenger.sent == []
