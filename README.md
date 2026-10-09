# Mitlex — цифровая модернизация операционных процессов

> Боевой кейс в ООО «МИТЛЕКС ТД»: от диагностики процессов и проектирования TO-BE к запуску рабочих маршрутов и Python/Flask-интеграции Yandex Tracker × Yandex Messenger.

![Business case](https://img.shields.io/badge/type-commercial%20case-2E8B57) ![Domain](https://img.shields.io/badge/domain-construction-6C63FF) ![Integration](https://img.shields.io/badge/integration-Tracker%20%C3%97%20Messenger-005BFF) ![Stack](https://img.shields.io/badge/stack-Python%20%2B%20Flask-3776AB)

## Кейс

[**Открыть полный разбор →**](docs/CASE_STUDY.md)

В Mitlex операционные заявки, согласование счетов, оплаты и контроль поставки проходили через чаты, таблицы и ручные пересылки. Я собрал целевую модель процесса, настроил маршруты в Yandex Tracker и реализовал сервис, который доставляет события и контекст задач в Yandex Messenger.

Результат: сроки ключевых заявок и счетов сократились на **25–30%**, доля задач, выполненных в срок, выросла с **45% до 70%+**, а количество ручных уточнений и возвратов снизилось примерно на **треть**.

## Материалы

| Раздел | Что внутри |
| --- | --- |
| [Разбор кейса](docs/CASE_STUDY.md) | Контекст, диагностика, решение, внедрение и результаты |
| [Требования](docs/REQUIREMENTS.md) | User stories, критерии приёмки и бизнес-правила |
| [TO-BE-процесс](docs/PROCESS_MODEL.md) | Сквозной BPMN: инициатор → снабжение → финансы → бухгалтерия → контроль поставки |
| [Архитектура](docs/ARCHITECTURE.md) | Компоненты, поток данных, надёжность и границы системы |
| [Webhook API](docs/API_CONTRACT.md) | Контракт и примеры payloads |
| [Стратегия тестирования](docs/TEST_STRATEGY.md) | Сквозные и приёмочные сценарии |
| [Риски](docs/RISKS.md) | Операционные, интеграционные и организационные риски |
| [Рабочий Flask-сервис](src/mitlex_webhook_service.py) | Webhook-сценарии, маршрутизация, статусы и тредовые уведомления |
| [Тестовый контур](src/tracker_bridge) | Изолированная реализация и pytest-проверки |
| [BPMN 2.0](docs/diagrams/mitlex_procurement_to_payment.bpmn) | Редактируемая схема процесса |
| [BPMN PDF](docs/diagrams/mitlex_procurement_to_payment.pdf) | Векторная версия схемы для быстрого просмотра |

## Ключевой результат

Yandex Tracker стал единым источником статуса и ответственности по заявке, а Yandex Messenger — каналом своевременных уведомлений и контекста. Это сохранило привычный для сотрудников формат коммуникации, но убрало необходимость вручную пересылать статусы и вложения между участниками процесса.

## Навыки

`Business analysis` · `Product discovery` · `AS-IS / TO-BE` · `BPMN` · `Requirements engineering` · `User stories` · `Acceptance criteria` · `Backlog prioritisation` · `Yandex Tracker` · `Yandex Messenger` · `REST API` · `Webhooks` · `Python` · `Flask` · `UAT` · `Rollout`
