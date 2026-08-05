# Webhook API contract

This is a portfolio-level contract. Field names are intentionally generic and not a claim about a specific vendor payload schema.

## `POST /webhooks/tracker`

### Request headers

| Header | Required | Description |
| --- | --- | --- |
| `Content-Type` | yes | `application/json` |
| `X-Webhook-Secret` | yes | Shared secret, compared in constant time in production |

### Minimal body

```json
{
  "event_id": "evt-demo-001",
  "event_type": "issue.status_changed",
  "issue": {
    "key": "OPS-1042",
    "summary": "Invoice approval: project Alpha",
    "status": "Ready for accounting",
    "functional_block": "finance",
    "chat_id": "chat-finance-demo",
    "thread_id": "thread-ops-1042",
    "attachments": [{"id": "file-1", "name": "invoice.pdf"}]
  }
}
```

### Responses

| Status | Body | Meaning |
| --- | --- | --- |
| `202` | `{"status":"accepted"}` | Event was validated and notification was accepted for delivery |
| `200` | `{"status":"duplicate"}` | Same event had already been processed |
| `401` | `{"error":"unauthorized"}` | Missing or invalid secret |
| `400` | `{"error":"..."}` | Invalid JSON or missing required business fields |

## Mapping and routing rules

| Source field | Bridge action |
| --- | --- |
| `event_id` | Idempotency key |
| `issue.key`, `summary`, `status` | Included in compact notification |
| `issue.chat_id` | Preferred target chat; otherwise derive from functional block in configuration |
| `issue.thread_id` | Reuse discussion context when present |
| `issue.attachments` | Include attachment count; avoid exposing URLs in public logs |

## Example outgoing message

```text
[OPS-1042] Status: Ready for accounting
Invoice approval: project Alpha
Attachments: 1
```

## Error policy

Do not acknowledge an event as delivered if the downstream API call fails in a real asynchronous implementation. Queue it with retry metadata and alert after the configured retry budget is exhausted.

