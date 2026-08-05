# Test strategy

The test suite checks the integration risks most likely to damage user trust: a missed update, a message in the wrong context, and a duplicate message.

| Scenario | Expected result |
| --- | --- |
| Issue enters a route | One message with issue key, summary, and status |
| Status changes | New event creates a status update in the stored thread |
| Attachment is added | Message reports attachment presence/count without leaking a URL |
| Provider retries same webhook | `200 duplicate`; no second Messenger call |
| Secret is wrong | `401`; no event is stored or delivered |
| Required routing data absent | `400`; no partial delivery |

Run locally:

```bash
pytest -q
```

For a production rollout, add contract tests against a sandbox, load tests for burst events, secret-rotation tests, and end-to-end acceptance scripts in the TEST queue before any OPS change.

