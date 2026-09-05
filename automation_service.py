"""Safe portfolio implementation of a webhook-driven workflow service.

The module uses synthetic data only. It illustrates the Python logic used in
an internal-process automation project: validation, idempotency and routing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class ValidationError(ValueError):
    """Raised when an incoming workflow event is incomplete."""


@dataclass(frozen=True)
class WorkflowEvent:
    event_id: str
    issue_id: str
    request_type: str
    status: str
    initiator: str


@dataclass(frozen=True)
class AutomationResult:
    duplicate: bool
    action: str
    target_queue: str | None
    notification: str | None


class WorkflowAutomationService:
    """Routes events and prevents duplicate actions for retry-safe webhooks."""

    _ROUTES = {
        ("procurement", "invoice_ready"): ("finance_approval", "Invoice sent for approval"),
        ("procurement", "payment_confirmed"): ("delivery_control", "Payment confirmed"),
        ("invoice_approval", "approved"): ("accounting_payment", "Invoice approved"),
    }

    def __init__(self) -> None:
        self._processed_event_ids: set[str] = set()

    @staticmethod
    def parse_event(payload: dict[str, Any]) -> WorkflowEvent:
        required = ("event_id", "issue_id", "request_type", "status", "initiator")
        missing = [field for field in required if not payload.get(field)]
        if missing:
            raise ValidationError(f"Missing required fields: {', '.join(missing)}")
        return WorkflowEvent(**{field: str(payload[field]) for field in required})

    def process(self, payload: dict[str, Any]) -> AutomationResult:
        event = self.parse_event(payload)
        if event.event_id in self._processed_event_ids:
            return AutomationResult(True, "skip_duplicate", None, None)

        self._processed_event_ids.add(event.event_id)
        route = self._ROUTES.get((event.request_type, event.status))
        if route is None:
            return AutomationResult(False, "no_automation_rule", None, None)

        target_queue, message = route
        notification = f"{message}: source issue {event.issue_id}"
        return AutomationResult(False, "create_linked_issue", target_queue, notification)
