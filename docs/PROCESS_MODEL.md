# Process model: procurement request to payment

Это упрощённая обезличенная публичная версия процесса, смоделированного в BPMN в ходе проекта. Исходный файл выполнен в стандарте BPMN 2.0 и открывается в Camunda Modeler.

![BPMN: заявка на закупку — от создания до оплаты](diagrams/mitlex_procurement_to_payment.svg)

[Открыть исходник BPMN для Camunda Modeler](diagrams/mitlex_procurement_to_payment.bpmn)

```mermaid
flowchart LR
  start((Start)) --> form[Initiator submits request\nin Yandex Forms]
  form --> tracker[Tracker issue created\nwith type, object, due date, files]
  tracker --> check{Mandatory fields\ncomplete?}
  check -- No --> clarify[Return for clarification]
  clarify --> form
  check -- Yes --> procurement[Procurement review]
  procurement --> finance[Finance approval\nrelated task and fields synced]
  finance --> approved{Approved?}
  approved -- No --> rejected[Record decision and notify]
  approved -- Yes --> accounting[Accounting payment\nand payment document]
  accounting --> delivery[Delivery control\nand closing documents]
  delivery --> done((Completed))

  tracker -. webhook event .-> bridge[Flask webhook bridge]
  bridge -. status update in chat/thread .-> messenger[Yandex Messenger]
```

## Automation boundaries

| Stage | Workflow responsibility | Integration responsibility |
| --- | --- | --- |
| Request | Tracker stores a structured source-of-truth issue | Form supplies required inputs |
| Finance hand-off | Trigger creates/links a financial task and synchronises permitted fields | Bridge posts an update to the relevant discussion |
| Approval / rejection | Authorised employee makes the decision in Tracker | Bridge reports the status; it does not decide it |
| Payment documents | Accounting attaches confirmation and moves state | Bridge preserves chat/thread context for the update |
| Completion | Tracker records completion and ownership | Messenger remains a communication layer, not a record system |

## Why BPMN was useful

The model made ownership, hand-offs, gateway decisions, exceptions, and automation points discussable with procurement, finance, accounting, IT, and project teams before implementation. It also provided the basis for user stories, acceptance tests, Tracker statuses, and webhook scenarios.
