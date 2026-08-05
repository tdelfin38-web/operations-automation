# Risks and mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Duplicate delivery after provider retry | Notification fatigue and loss of trust | Persistent idempotency key, atomic claim, replay audit |
| Wrong chat or thread | Information leakage / missed action | Explicit routing metadata, allowlist, TEST-to-OPS promotion checklist |
| Webhook spoofing | Unauthorised messages | TLS, secret/signature verification, secret rotation |
| Changed Tracker fields or workflow | Broken parsing | Versioned contract, schema validation, contract tests |
| Messenger API outage | Missed notification | Retry queue, dead-letter handling, monitoring, manual replay |
| Sensitive documents in logs | Data exposure | Redaction, minimal logging, restricted retention/access |
| Automation bypasses human decision | Incorrect business outcome | Keep workflow authority in Tracker and approval owners |

