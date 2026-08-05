# Requirements and acceptance criteria

## User stories

### Request initiator

As a request initiator, I want to submit a request with type, project/object, deadline, attachments, and responsible functional block, so that the process starts without a parallel chat clarification.

**Acceptance criteria:** mandatory fields are validated; issue enters the correct queue; next owner and status are visible; attachments are available to subsequent participants.

### Finance and accounting

As a finance or accounting specialist, I want to receive a related task with synchronised key fields and files, so that I can approve and pay without re-entering information.

**Acceptance criteria:** related issue is created by workflow rules; approved information is transferred; relevant chat receives one status update; a payment document can be returned to the process context.

### Project participant

As a project participant, I want notifications for my object to arrive in the correct chat and thread, so that events from unrelated projects do not mix.

**Acceptance criteria:** routing is driven by project/context; saved thread is reused; duplicate webhooks do not create duplicate messages; TEST and production routes are isolated.

## Functional requirements

- Handle issue creation, status change, and attachment events.
- Extract issue data without coupling notification logic to undocumented field IDs.
- Route to chat/thread by explicit metadata, with a configuration fallback per functional block.
- Provide idempotent processing by stable event ID.
- Return machine-readable HTTP outcomes and record diagnostic context safely.

## Non-functional requirements

- Never store or expose access tokens in source, payload samples, or logs.
- Process normal events quickly enough for an operational notification (target: under 30 seconds including downstream delivery).
- Make delivery failures observable and replayable.
- Keep TEST and production configuration separate.

## Out of scope

User provisioning, financial approval rules, changing Tracker workflow states from the bridge, and long-term attachment storage are out of scope for this service.

