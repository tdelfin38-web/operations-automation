import unittest

from src.automation_service import ValidationError, WorkflowAutomationService


class WorkflowAutomationServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = WorkflowAutomationService()
        self.payload = {
            "event_id": "event-1",
            "issue_id": "REQ-42",
            "request_type": "procurement",
            "status": "invoice_ready",
            "initiator": "demo.requester",
        }

    def test_routes_procurement_invoice_to_finance(self) -> None:
        result = self.service.process(self.payload)
        self.assertFalse(result.duplicate)
        self.assertEqual(result.action, "create_linked_issue")
        self.assertEqual(result.target_queue, "finance_approval")

    def test_repeated_event_does_not_create_duplicate(self) -> None:
        self.service.process(self.payload)
        result = self.service.process(self.payload)
        self.assertTrue(result.duplicate)
        self.assertEqual(result.action, "skip_duplicate")

    def test_missing_required_field_is_rejected(self) -> None:
        invalid_payload = self.payload | {"initiator": ""}
        with self.assertRaises(ValidationError):
            self.service.process(invalid_payload)


if __name__ == "__main__":
    unittest.main()
