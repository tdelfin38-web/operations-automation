
from flask import Flask, request, jsonify
import os
import json
import html
import mimetypes
import re
import traceback
import fcntl
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote
from contextlib import contextmanager

import requests

app = Flask(__name__)
QUEUE_LOCAL_FIELD_CACHE: Dict[str, Dict[str, str]] = {}

# ================= CONFIG =================
ORG_ID = os.environ.get("TRACKER_ORG_ID", "8268114")
TRACKER_TOKEN = os.environ.get("TRACKER_TOKEN", "REDACTED_TRACKER_TOKEN")
BOT_TOKEN = os.environ.get("MESSENGER_BOT_TOKEN", "REDACTED_MESSENGER_BOT_TOKEN")

SUPPLY_CHAT_ID = os.environ.get("SUPPLY_CHAT_ID", "0/0/c3e446a2-6720-44b2-a3c2-4c6d324c8cdc")
FINANCE_CHAT_ID = os.environ.get("FINANCE_CHAT_ID", "0/0/81ead10b-9b57-4f62-9827-532eb5653b68")
ACCOUNTING_CHAT_ID = os.environ.get("ACCOUNTING_CHAT_ID", "0/0/98d65d35-3e08-4f3f-90ac-12854f05ac1b")
PROJECT_NOTIFICATIONS_CHAT_ID = os.environ.get("PROJECT_NOTIFICATIONS_CHAT_ID", "0/0/34b75b3a-186b-4df5-b3f5-ffabdb964a92")
APPROVED_INVOICES_CHAT_ID = os.environ.get("APPROVED_INVOICES_CHAT_ID", "")
ADMINISTRATION_CHAT_ID = os.environ.get("ADMINISTRATION_CHAT_ID", "0/0/99f482e7-f11b-42c8-ae21-0c1a64a2a176")
ARISTOVO_PROJECT_CHAT_ID = os.environ.get("ARISTOVO_PROJECT_CHAT_ID", "0/0/6e50e0ac-acea-46d5-9089-26decf896160")

TEST_SUPPLY_CHAT_ID = os.environ.get("TEST_SUPPLY_CHAT_ID", "0/0/24ff6496-18a3-47d8-8464-bd8d2cf98cf8")
TEST_FINANCE_CHAT_ID = os.environ.get("TEST_FINANCE_CHAT_ID", "0/0/3cf9c947-25cb-4acb-be69-8699fea242ae")
TEST_ACCOUNTING_CHAT_ID = os.environ.get("TEST_ACCOUNTING_CHAT_ID", "0/0/68cc6d00-2c1b-465b-a0a0-e74ea488e144")
TEST_PROJECT_NOTIFICATIONS_CHAT_ID = os.environ.get("TEST_PROJECT_NOTIFICATIONS_CHAT_ID", "0/0/db4fe932-4304-480f-b052-f3c8f701bf7a")
TEST_APPROVED_INVOICES_CHAT_ID = os.environ.get("TEST_APPROVED_INVOICES_CHAT_ID", "")
TEST_IT_INITIATOR_CHAT_ID = os.environ.get("TEST_IT_INITIATOR_CHAT_ID", "0/0/26bea514-5695-41d0-a033-81e7eef1db37")
TEST_ADMINISTRATION_CHAT_ID = os.environ.get("TEST_ADMINISTRATION_CHAT_ID", "0/0/94730afc-3b18-46bf-bff8-97e540f6d1d7")

TRACKER_BASE = os.environ.get("TRACKER_BASE", "https://api.tracker.yandex.net/v3")
TRACKER_UI = os.environ.get("TRACKER_UI", "https://tracker.yandex.ru")

MESSENGER_SEND_TEXT_URL = "https://botapi.messenger.yandex.net/bot/v1/messages/sendText/"
MESSENGER_SEND_FILE_URL = "https://botapi.messenger.yandex.net/bot/v1/messages/sendFile/"

INVOICE_MARKER = os.environ.get("INVOICE_MARKER", "Счет на согласование")
PAID_INVOICE_MARKER = os.environ.get("PAID_INVOICE_MARKER", "Платежка")
PAID_INVOICE_RELOAD_MARKER = os.environ.get("PAID_INVOICE_RELOAD_MARKER", "Доп платежка")
CLOSING_DOCS_MARKER = os.environ.get("CLOSING_DOCS_MARKER", "Закрывающие документы")
DELIVERY_CONTROL_CREATED_FIELD = os.environ.get("DELIVERY_CONTROL_CREATED_FIELD", "DeliveryControlTaskCreated")
SUPPLY_CONTROL_APP_TYPE = os.environ.get("SUPPLY_CONTROL_APP_TYPE", "Контроль поставки (Снабжение)")
SUPPLY_CONTROL_ROUTE = os.environ.get("SUPPLY_CONTROL_ROUTE", "Снабжение → Бухгалтерия")
ADMIN_SUPPLY_CONTROL_APP_TYPE = os.environ.get("ADMIN_SUPPLY_CONTROL_APP_TYPE", "Контроль поставки (Администрация)")
ADMIN_SUPPLY_CONTROL_ROUTE = os.environ.get("ADMIN_SUPPLY_CONTROL_ROUTE", "Администрация → Бухгалтерия")
INITIATOR_FINANCE_APP_TYPE = os.environ.get("INITIATOR_FINANCE_APP_TYPE", "Согласование счета")
INITIATOR_FINANCE_APP_TYPES = os.environ.get(
    "INITIATOR_FINANCE_APP_TYPES",
    "Согласование счета,Согласование счета (Финансы)",
)
INITIATOR_FINANCE_ROUTE = os.environ.get("INITIATOR_FINANCE_ROUTE", "Инициатор → Финансы → Бухгалтерия")
INITIATOR_SUPPLY_CONTROL_APP_TYPE = os.environ.get("INITIATOR_SUPPLY_CONTROL_APP_TYPE", "Контроль поставки (Инициатор)")
INITIATOR_SUPPLY_CONTROL_ROUTE = os.environ.get("INITIATOR_SUPPLY_CONTROL_ROUTE", "Инициатор → Бухгалтерия")

DATE_SUFFIX = "desiredCompletionDate"
APPLICATION_TYPE_SUFFIX = "applicationType"
FUNCTIONAL_BLOCK_SUFFIXES = ["functional_Block", "functionalBlock", "functional_block"]
OBJECT_SUFFIX = "object"
INITIATOR_SUFFIX = "initiator"
APPLICATION_OUTLINE_SUFFIX = "applicationOutline"
SUPPLY_THREAD_FIELD = "69c45c3a3dad8074e67f0026--supplyThreadId"
FINANCE_THREAD_FIELD = "69c45c3a3dad8074e67f0026--financeThreadId"
ACCOUNTING_THREAD_FIELD = "69c45c3a3dad8074e67f0026--accountingThreadId"
PROJECT_NOTIFICATIONS_THREAD_FIELD = os.environ.get("PROJECT_NOTIFICATIONS_THREAD_FIELD", "69c45c3a3dad8074e67f0026--projectMessengerThreadId")
PROJECT_NOTIFICATIONS_CHAT_FIELD = os.environ.get("PROJECT_NOTIFICATIONS_CHAT_FIELD", "69c45c3a3dad8074e67f0026--projectMessengerChatId")
PROJECT_CHAT_LINK_FIELD = os.environ.get("PROJECT_CHAT_LINK_FIELD", "projectMessengerChatLink")
DEPARTMENT_CHAT_LINK_FIELD = os.environ.get("DEPARTMENT_CHAT_LINK_FIELD", "departmentMessengerChatLink")
SUPPLY_CONTROL_OBJECT_THREAD_FIELD = os.environ.get("SUPPLY_CONTROL_OBJECT_THREAD_FIELD", PROJECT_NOTIFICATIONS_THREAD_FIELD)
SUPPLY_CONTROL_OBJECT_CHAT_FIELD = os.environ.get("SUPPLY_CONTROL_OBJECT_CHAT_FIELD", PROJECT_NOTIFICATIONS_CHAT_FIELD)
DEPARTMENT_BOARD_SYNC_QUEUES = os.environ.get("DEPARTMENT_BOARD_SYNC_QUEUES", "TESTG")
DEPARTMENT_BOARD_FIELD = os.environ.get("DEPARTMENT_BOARD_FIELD", "boards")
DEPARTMENT_BOARD_MAP_JSON = os.environ.get("DEPARTMENT_BOARD_MAP_JSON", "")
PROJECT_BOARD_MAP_JSON = os.environ.get("PROJECT_BOARD_MAP_JSON", "")
OPERATIONS_DIRECTOR_BOARD_ID = os.environ.get("OPERATIONS_DIRECTOR_BOARD_ID", "54")
OPERATIONS_DIRECTOR_APPLICATION_TYPES = os.environ.get(
    "OPERATIONS_DIRECTOR_APPLICATION_TYPES",
    "Закупка материалов (Снабжение),Закупка АХО (Администрация),Контроль поставки (Снабжение),Контроль поставки (Администрация)",
)
CONTROLLED_DEPARTMENT_BOARD_IDS = os.environ.get(
    "CONTROLLED_DEPARTMENT_BOARD_IDS",
    "13,14,15,22,24,25,26,27,28,32,33,40,41,50,51,52,53,54,55,57,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74",
)

SUPPLY_BLOCK = os.environ.get("SUPPLY_BLOCK", "Снабжение")
ADMINISTRATION_BLOCK = os.environ.get("ADMINISTRATION_BLOCK", "Административный")
FINANCE_BLOCK = os.environ.get("FINANCE_BLOCK", "Финансы")
TRACKER_ORG_HEADER = os.environ.get("TRACKER_ORG_HEADER", "X-Org-ID")

HTTP_TIMEOUT = 30
DOWNLOAD_TIMEOUT = 120
MESSENGER_TIMEOUT = 60
PROJECT_THREAD_STATE_PATH = os.environ.get("PROJECT_THREAD_STATE_PATH", "/root/project_thread_state.json")
THREAD_STATE_PATH = os.environ.get("THREAD_STATE_PATH", "/root/thread_state.json")
STAGE_LOCK_DIR = os.environ.get("STAGE_LOCK_DIR", "/root/stage_locks")
STAGE_EVENT_STATE_PATH = os.environ.get("STAGE_EVENT_STATE_PATH", "/root/stage_event_state.json")


# ================= WIKI MAP =================
# Добавляй сюда новые объекты и их wiki-ссылки
OBJECT_WIKI_MAP = {
    'ЖК "Сансара"': 'https://wiki.yandex.ru/homepage/fdafd95b3a5c/portfeli-proektov/portfel-proektov-1/proekt-sansara/',
    'ЖК “Сансара”': 'https://wiki.yandex.ru/homepage/fdafd95b3a5c/portfeli-proektov/portfel-proektov-1/proekt-sansara/',
    'Сансара': 'https://wiki.yandex.ru/homepage/fdafd95b3a5c/portfeli-proektov/portfel-proektov-1/proekt-sansara/',
    'ЖК союз': 'https://wiki.yandex.ru/homepage/fdafd95b3a5c/portfeli-proektov/portfel-proektov-1/proekt-zhk-sojuz/',
    'ЖК Союз': 'https://wiki.yandex.ru/homepage/fdafd95b3a5c/portfeli-proektov/portfel-proektov-1/proekt-zhk-sojuz/',
    'ЖК "Союз"': 'https://wiki.yandex.ru/homepage/fdafd95b3a5c/portfeli-proektov/portfel-proektov-1/proekt-zhk-sojuz/',
    'ЖК “Союз”': 'https://wiki.yandex.ru/homepage/fdafd95b3a5c/portfeli-proektov/portfel-proektov-1/proekt-zhk-sojuz/',
    'ЖК «Союз»': 'https://wiki.yandex.ru/homepage/fdafd95b3a5c/portfeli-proektov/portfel-proektov-1/proekt-zhk-sojuz/',
    'Проект - "ЖК Союз"': 'https://wiki.yandex.ru/homepage/fdafd95b3a5c/portfeli-proektov/portfel-proektov-1/proekt-zhk-sojuz/',
    'Союз': 'https://wiki.yandex.ru/homepage/fdafd95b3a5c/portfeli-proektov/portfel-proektov-1/proekt-zhk-sojuz/',
    'Янис': 'https://wiki.yandex.ru/homepage/fdafd95b3a5c/portfeli-proektov/portfel-proektov-1/proekt-janis/',
    'Калязин': 'https://wiki.yandex.ru/homepage/fdafd95b3a5c/portfeli-proektov/portfel-proektov-1/proekt-kaljazin/',
    'Комильфо': 'https://wiki.yandex.ru/homepage/fdafd95b3a5c/portfeli-proektov/portfel-proektov-1/proekt-komilfo/',
    'Гольф клуб Шишкино': 'https://wiki.yandex.ru/homepage/fdafd95b3a5c/portfeli-proektov/portfel-proektov-1/golf-klub/',
    'Парковые кварталы': 'https://wiki.yandex.ru/homepage/fdafd95b3a5c/portfeli-proektov/portfel-proektov-1/proekt---parkovye-kvartaly/',
}

OBJECT_PROJECT_CHAT_MAP = {
    "Аристово": ARISTOVO_PROJECT_CHAT_ID.strip(),
    'ЖК "Аристово"': ARISTOVO_PROJECT_CHAT_ID.strip(),
    "ЖК Аристово": ARISTOVO_PROJECT_CHAT_ID.strip(),
    'Проект - "Аристово"': ARISTOVO_PROJECT_CHAT_ID.strip(),
    "Проект - «Аристово»": ARISTOVO_PROJECT_CHAT_ID.strip(),
    "Парковые кварталы": "0/0/7dd7a8ae-4afe-4d38-9382-7c0cd69c636d",
    'Проект - "Парковые кварталы"': "0/0/7dd7a8ae-4afe-4d38-9382-7c0cd69c636d",
    "Петровский парк": "0/0/e70c0d14-aaca-4a91-9f8a-8d526d940692",
    'Проект - "Петровский парк"': "0/0/e70c0d14-aaca-4a91-9f8a-8d526d940692",
    "Гольф клуб Шишкино": "0/0/30402df1-75ff-4134-9c0a-b32c3488417f",
    'Проект - "Гольф клуб Шишкино"': "0/0/30402df1-75ff-4134-9c0a-b32c3488417f",
    "Шишкино": "0/0/30402df1-75ff-4134-9c0a-b32c3488417f",
    "Калязин": "0/0/d30ae803-dfe5-418e-bd28-c9d3834cb388",
    'Проект - "Калязин"': "0/0/d30ae803-dfe5-418e-bd28-c9d3834cb388",
    "Комильфо": "0/0/0ac46b36-7516-47c6-9b9f-670ef19cb9ad",
    'Проект - "Комильфо"': "0/0/0ac46b36-7516-47c6-9b9f-670ef19cb9ad",
    "Дом для Яниса": "0/0/7ec483a5-ad12-4c7c-8ac3-0cd88faa429c",
    'Проект - "Дом для Яниса"': "0/0/7ec483a5-ad12-4c7c-8ac3-0cd88faa429c",
}

# Пилотный mapping: пока все известные варианты Союза идут в текущий общий
# проектный чат, но структура уже готова для разведения chat_id по объектам.
BASE_FUNCTIONAL_BLOCK_CHAT_MAP = {
    "сдо": "0/0/f383f3e5-d86f-43cc-8ba6-25c188ec6ffb",
    "пто": "0/0/974a9738-5022-4910-8d49-b847f417d3ee",
    "проектный офис": "0/0/e4d007c8-4595-4aeb-99cf-35f9c8f97338",
    "производство": "0/0/ca5bc44a-c417-450b-9e26-90ffa626980e",
    "проектирование": "0/0/b381b877-5756-495c-b359-d810cd622158",
    "отдел кадров": "0/0/4739adb6-5cae-4683-8cd2-6373a0d88165",
    "юридический": "0/0/42c61fce-31e3-489f-a349-156f9c20678a",
    "hr": "0/0/1af55931-860d-47b6-a60e-2db1e7d475bf",
    "it": "0/0/e338230d-37c9-4804-92e2-f80429f3f432",
    "маркетинг": "0/0/a495e9b0-1383-428f-a282-4f9470a0f250",
    "продажи": "0/0/f05bf227-69f3-4eba-a895-480fa1321246",
    "административный": ADMINISTRATION_CHAT_ID.strip(),
    "администрация": ADMINISTRATION_CHAT_ID.strip(),
}

DEPARTMENT_WIKI_MAP: Dict[str, str] = {}
TEST_INITIATOR_CHAT_MAP = {
    "it": TEST_IT_INITIATOR_CHAT_ID.strip(),
}

TEST_DEPARTMENT_CHAT_MAP = {
    "административный": TEST_ADMINISTRATION_CHAT_ID.strip(),
    "администрация": TEST_ADMINISTRATION_CHAT_ID.strip(),
}

DEFAULT_DEPARTMENT_BOARD_MAP = {
    "снабжение": 50,
    "отдел - снабжения": 50,
    "финансы": 51,
    "финансовый": 51,
    "финансового": 51,
    "финансовый - отдел": 51,
    "бухгалтерия": 52,
    "бухгалтерии": 52,
    "отдел - бухгалтерии": 52,
    "административный": 69,
    "административный - отдел": 69,
    "администрация": 69,
    "офис менеджер": 69,
    "офис-менеджер": 69,
    "it": 67,
    "отдел - it": 67,
    "hr": 66,
    "отдел - hr": 66,
    "сдо": 55,
    "отдел - сдо": 55,
    "пто": 61,
    "отдел - пто": 61,
    "проектирование": 63,
    "отдел - проектирования": 63,
    "производство": 62,
    "производственный": 62,
    "производственного": 62,
    "производственный - отдел": 62,
    "отдел кадров": 64,
    "кадры": 64,
    "кадров": 64,
    "отдел - кадров": 64,
    "юридический": 65,
    "юридического": 65,
    "юридический - отдел": 65,
    "маркетинг": 68,
    "маркетинга": 68,
    "отдел - маркетинга": 68,
    "продажи": 57,
    "продаж": 57,
    "отдел - продаж": 57,
}

DEFAULT_PROJECT_BOARD_MAP = {
    "калязин": 53,
    "проект - калязин": 53,
    "жк союз": 59,
    "союз": 59,
    "проект - жк союз": 59,
    "жк - союз": 59,
    "парковые кварталы": 60,
    "проект - парковые кварталы": 60,
    "гольф клуб шишкино": 70,
    "гк гольф клуб - шишкино": 70,
    "проект - гольф клуб шишкино": 70,
    "проект гольф клуб шишкино": 70,
    "шишкино": 70,
    "комильфо": 71,
    "проект - комильфо": 71,
    "проект комильфо": 71,
    "дом для яниса": 72,
    "дом для янис": 72,
    "янис": 72,
    "проект - дом для яниса": 72,
    "проект дом для яниса": 72,
    "петровский парк": 73,
    "проект - петровский парк": 73,
    "проект петровский парк": 73,
    "аристово": 74,
    "жк аристово": 74,
    "проект - аристово": 74,
    "проект - жк аристово": 74,
}

# ================= LOGGING =================

def log(message: str) -> None:
    print(message, flush=True)


def log_exception(prefix: str, exc: Exception) -> None:
    log(f"{prefix}: {type(exc).__name__}: {exc}")
    log(traceback.format_exc())


# ================= HEADERS =================

def tracker_headers() -> Dict[str, str]:
    return {
        "Authorization": f"OAuth {TRACKER_TOKEN}",
        TRACKER_ORG_HEADER: ORG_ID,
        "Content-Type": "application/json",
    }


def tracker_file_headers() -> Dict[str, str]:
    return {
        "Authorization": f"OAuth {TRACKER_TOKEN}",
        TRACKER_ORG_HEADER: ORG_ID,
    }


def messenger_json_headers() -> Dict[str, str]:
    return {
        "Authorization": f"OAuth {BOT_TOKEN}",
        "Content-Type": "application/json",
    }


def messenger_auth_headers() -> Dict[str, str]:
    return {
        "Authorization": f"OAuth {BOT_TOKEN}",
    }


# ================= TRACKER API =================

def get_issue(issue_key: str) -> Dict[str, Any]:
    r = requests.get(
        f"{TRACKER_BASE}/issues/{issue_key}",
        headers=tracker_headers(),
        params={"expand": "attachments"},
        timeout=HTTP_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def get_links(issue_key: str) -> List[Dict[str, Any]]:
    r = requests.get(
        f"{TRACKER_BASE}/issues/{issue_key}/links",
        headers=tracker_headers(),
        timeout=HTTP_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def get_comments(issue_key: str) -> List[Dict[str, Any]]:
    r = requests.get(
        f"{TRACKER_BASE}/issues/{issue_key}/comments",
        headers=tracker_headers(),
        params={"expand": "attachments"},
        timeout=HTTP_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def add_comment(issue_key: str, text: str, attachment_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"text": text}
    if attachment_ids:
        payload["attachmentIds"] = attachment_ids

    r = requests.post(
        f"{TRACKER_BASE}/issues/{issue_key}/comments",
        headers=tracker_headers(),
        json=payload,
        timeout=HTTP_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def update_issue(issue_key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    log(f"[update_issue] PATCH {issue_key}")
    log(f"[update_issue] payload = {payload}")

    r = requests.patch(
        f"{TRACKER_BASE}/issues/{issue_key}",
        headers=tracker_headers(),
        json=payload,
        timeout=HTTP_TIMEOUT,
    )

    if not r.ok:
        log(f"[update_issue] ERROR {r.status_code}: {r.text}")

    r.raise_for_status()
    if not r.text.strip():
        return {}
    return r.json()


def create_issue(payload: Dict[str, Any]) -> Dict[str, Any]:
    log(f"[create_issue] payload = {payload}")
    r = requests.post(
        f"{TRACKER_BASE}/issues/",
        headers=tracker_headers(),
        json=payload,
        timeout=HTTP_TIMEOUT,
    )
    if not r.ok:
        log(f"[create_issue] ERROR {r.status_code}: {r.text}")
    r.raise_for_status()
    if not r.text.strip():
        return {}
    return r.json()


def create_issue_link(issue_key: str, related_issue_key: str, relationship: str = "relates") -> Dict[str, Any]:
    payload = {
        "relationship": relationship,
        "issue": related_issue_key,
    }
    log(f"[create_issue_link] issue={issue_key}, related={related_issue_key}, relationship={relationship}")
    r = requests.post(
        f"{TRACKER_BASE}/issues/{issue_key}/links",
        headers=tracker_headers(),
        json=payload,
        timeout=HTTP_TIMEOUT,
    )
    if not r.ok:
        log(f"[create_issue_link] ERROR {r.status_code}: {r.text}")
        if r.status_code == 422 and "уже связаны" in (r.text or "").lower():
            return {"ok": True, "mode": "already_linked"}
    r.raise_for_status()
    if not r.text.strip():
        return {}
    return r.json()


def get_transitions(issue_key: str) -> List[Dict[str, Any]]:
    r = requests.get(
        f"{TRACKER_BASE}/issues/{issue_key}/transitions",
        headers=tracker_headers(),
        timeout=HTTP_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def get_queue_local_fields(queue_key: str) -> List[Dict[str, Any]]:
    r = requests.get(
        f"{TRACKER_BASE}/queues/{queue_key}/localFields",
        headers=tracker_headers(),
        timeout=HTTP_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def execute_transition(issue_key: str, transition_id: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    r = requests.post(
        f"{TRACKER_BASE}/issues/{issue_key}/transitions/{transition_id}/_execute",
        headers=tracker_headers(),
        json=payload or {},
        timeout=HTTP_TIMEOUT,
    )
    if not r.ok:
        log(f"[execute_transition] ERROR {r.status_code}: {r.text}")
    r.raise_for_status()
    if not r.text.strip():
        return {}
    return r.json()


def transition_issue_to_status(issue_key: str, target_status_display: str) -> bool:
    try:
        transitions = get_transitions(issue_key)
    except Exception as exc:
        log(f"[transition_issue_to_status] ERROR loading transitions for {issue_key}: {exc}")
        return False

    normalized_target = target_status_display.strip().lower()

    for transition in transitions:
        to_status = transition.get("to") or {}
        to_display = str(to_status.get("display") or "").strip().lower()
        transition_display = str(transition.get("display") or "").strip().lower()

        if to_display == normalized_target or transition_display == normalized_target:
            transition_id = transition.get("id")
            if not transition_id:
                continue
            execute_transition(issue_key, str(transition_id))
            log(f"[transition_issue_to_status] {issue_key} -> {target_status_display} via {transition_id}")
            return True

    log(f"[transition_issue_to_status] transition to '{target_status_display}' not found for {issue_key}")
    return False


# ================= MESSENGER API =================

def send_text(chat_id: str, text: str, thread_id: Optional[int] = None, payload_id: Optional[str] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }

    if thread_id is not None:
        payload["thread_id"] = int(thread_id)

    if payload_id:
        payload["payload_id"] = payload_id

    r = requests.post(
        MESSENGER_SEND_TEXT_URL,
        headers=messenger_json_headers(),
        json=payload,
        timeout=MESSENGER_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def send_file(chat_id: str, file_bytes: bytes, filename: str, content_type: Optional[str] = None, thread_id: Optional[int] = None) -> Dict[str, Any]:
    if not content_type:
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    data: Dict[str, Any] = {"chat_id": chat_id}
    if thread_id is not None:
        data["thread_id"] = str(int(thread_id))

    r = requests.post(
        MESSENGER_SEND_FILE_URL,
        headers=messenger_auth_headers(),
        data=data,
        files={"document": (filename, file_bytes, content_type)},
        timeout=DOWNLOAD_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


# ================= HELPERS =================

def tracker_ui_url(issue_key: str) -> str:
    return f"{TRACKER_UI}/{issue_key}"


def tracker_display_url(issue_key: str) -> str:
    return tracker_ui_url(issue_key)


def get_queue_key(issue: Optional[Dict[str, Any]]) -> str:
    return str(((issue or {}).get("queue") or {}).get("key") or "").strip().upper()


def chat_config_for_queue(queue_key: str) -> Dict[str, str]:
    if str(queue_key or "").strip().upper() == "TESTG":
        return {
            "supply": TEST_SUPPLY_CHAT_ID.strip(),
            "finance": TEST_FINANCE_CHAT_ID.strip(),
            "accounting": TEST_ACCOUNTING_CHAT_ID.strip(),
            "project": TEST_PROJECT_NOTIFICATIONS_CHAT_ID.strip(),
            "approved_invoices": TEST_APPROVED_INVOICES_CHAT_ID.strip(),
        }

    return {
        "supply": SUPPLY_CHAT_ID.strip(),
        "finance": FINANCE_CHAT_ID.strip(),
        "accounting": ACCOUNTING_CHAT_ID.strip(),
        "project": PROJECT_NOTIFICATIONS_CHAT_ID.strip(),
        "approved_invoices": APPROVED_INVOICES_CHAT_ID.strip(),
    }


def resolve_issue_chat_id(issue: Optional[Dict[str, Any]], channel: str) -> str:
    return chat_config_for_queue(get_queue_key(issue)).get(channel, "").strip()


def get_custom_field(issue: Dict[str, Any], suffix: str) -> Tuple[Optional[str], Any]:
    for key, value in issue.items():
        if key.endswith(f"--{suffix}"):
            return key, value
    return None, None


def resolve_issue_field_key(issue: Optional[Dict[str, Any]], field_key: str) -> str:
    if not field_key:
        return field_key

    if issue and field_key in issue:
        return field_key

    suffix = field_key
    if "--" in suffix:
        suffix = suffix.split("--", 1)[1]

    if issue:
        resolved_key, _ = get_custom_field(issue, suffix)
        if resolved_key:
            return resolved_key

        queue_key = ((issue.get("queue") or {}).get("key") or "").strip()
        if queue_key:
            cache_key = f"{queue_key}:{suffix}"
            cached_value = QUEUE_LOCAL_FIELD_CACHE.get(cache_key)
            if cached_value:
                return cached_value["id"]

            try:
                local_fields = get_queue_local_fields(queue_key)
                for item in local_fields:
                    local_key = str(item.get("key") or "").strip()
                    local_id = str(item.get("id") or "").strip()
                    if local_key == suffix and local_id:
                        QUEUE_LOCAL_FIELD_CACHE[cache_key] = {"id": local_id}
                        return local_id
            except Exception as exc:
                log(f"[resolve_issue_field_key] local field lookup error for queue={queue_key}, suffix={suffix}: {exc}")

    return field_key


def get_custom_field_multi(issue: Dict[str, Any], suffixes: List[str]) -> Tuple[Optional[str], Any]:
    for suffix in suffixes:
        key, value = get_custom_field(issue, suffix)
        if key:
            return key, value
    return None, None


def normalize_thread_id(value: Any) -> Optional[int]:
    if value is None:
        return None

    if isinstance(value, int):
        return value

    text_value = str(value).strip()
    if not text_value or not text_value.isdigit():
        return None

    return int(text_value)


def normalize_text_value(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_marker_text(value: Any) -> str:
    text = normalize_text_value(value)
    if not text:
        return ""

    replacements = {
        "C": "С",
        "c": "с",
        "A": "А",
        "a": "а",
        "E": "Е",
        "e": "е",
        "K": "К",
        "k": "к",
        "M": "М",
        "m": "м",
        "H": "Н",
        "h": "н",
        "O": "О",
        "o": "о",
        "P": "Р",
        "p": "р",
        "T": "Т",
        "t": "т",
        "X": "Х",
        "x": "х",
        "Y": "У",
        "y": "у",
        "Ё": "Е",
        "ё": "е",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)

    return " ".join(text.split()).strip().lower()


def marker_in_text(text: str, marker: str) -> bool:
    normalized_text = normalize_marker_text(text)
    normalized_marker = normalize_marker_text(marker)
    return bool(normalized_text and normalized_marker and normalized_marker in normalized_text)


def build_messenger_chat_link(chat_id: str) -> str:
    normalized_chat_id = normalize_text_value(chat_id)
    if not normalized_chat_id:
        return ""
    return f"https://yandex.ru/chat/#/chats/{quote(normalized_chat_id, safe='')}"


def normalize_object_name(value: Any) -> str:
    text = normalize_text_value(value)
    if not text:
        return ""

    replacements = {
        "«": '"',
        "»": '"',
        "“": '"',
        "”": '"',
        "ё": "е",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)

    return " ".join(text.lower().replace('"', "").split())


def normalize_display_token(value: Any) -> str:
    return normalize_object_name(value)


def resolve_object_project_chat_id(object_name: Any) -> str:
    mapped_chat_id = OBJECT_PROJECT_CHAT_MAP.get(normalize_text_value(object_name), "").strip()
    if mapped_chat_id:
        return mapped_chat_id

    normalized_object = normalize_object_name(object_name)
    for mapped_object_name, chat_id in OBJECT_PROJECT_CHAT_MAP.items():
        if normalize_object_name(mapped_object_name) == normalized_object:
            return str(chat_id or "").strip()
    return ""


def get_issue_route_display(issue: Optional[Dict[str, Any]]) -> str:
    if not issue:
        return ""
    return get_display(get_custom_field(issue, "route")[1]).strip()


def is_administration_block_value(value: Any) -> bool:
    normalized = normalize_display_token(value)
    return normalized in {
        normalize_display_token(ADMINISTRATION_BLOCK),
        "администрация",
        "офис менеджер",
        "офис-менеджер",
    }


def is_source_block_value(value: Any) -> bool:
    normalized = normalize_display_token(value)
    return normalized in {
        normalize_display_token(SUPPLY_BLOCK),
        normalize_display_token(ADMINISTRATION_BLOCK),
        "администрация",
        "офис менеджер",
        "офис-менеджер",
    }


def get_source_block_display(issue: Optional[Dict[str, Any]]) -> str:
    functional_block = get_functional_block_display(issue).strip()
    if functional_block:
        return functional_block

    route_display = get_issue_route_display(issue)
    if route_display == "Офис-менеджер → Финансы → Бухгалтерия":
        return ADMINISTRATION_BLOCK
    if route_display == "Снабжение → Финансы → Бухгалтерия":
        return SUPPLY_BLOCK
    return functional_block


def build_source_comment_label(issue: Optional[Dict[str, Any]]) -> str:
    if is_initiator_finance_source_issue(issue or {}):
        return "Комментарий инициатора"
    if is_administration_block_value(get_source_block_display(issue)):
        return "Комментарий административного блока"
    return "Комментарий снабжения"


def build_source_arrival_comment(issue: Optional[Dict[str, Any]]) -> str:
    if is_initiator_finance_source_issue(issue or {}):
        return "📦 Заявка поступила к инициатору"
    if is_administration_block_value(get_source_block_display(issue)):
        return "📦 Заявка поступила в администрацию"
    return "📦 Заявка поступила в снабжение"


def get_issue_field_value(issue: Dict[str, Any], field_key: str) -> Any:
    resolved_key = resolve_issue_field_key(issue, field_key)
    return issue.get(resolved_key)


def save_issue_field_value(issue_key: str, issue: Dict[str, Any], field_key: str, value: Any) -> None:
    resolved_key = resolve_issue_field_key(issue, field_key)
    update_issue(issue_key, {resolved_key: value})
    issue[resolved_key] = value


def get_issue_string_field(issue: Dict[str, Any], field_key: str) -> str:
    return normalize_text_value(get_issue_field_value(issue, field_key))


def load_thread_state_map() -> Dict[str, Dict[str, Dict[str, str]]]:
    try:
        if not os.path.exists(THREAD_STATE_PATH):
            return {}
        with open(THREAD_STATE_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            return data
    except Exception as exc:
        log(f"[load_thread_state_map] ERROR: {exc}")
    return {}


def save_thread_state_map(state: Dict[str, Dict[str, Dict[str, str]]]) -> None:
    os.makedirs(os.path.dirname(THREAD_STATE_PATH), exist_ok=True)
    temp_path = f"{THREAD_STATE_PATH}.tmp"
    with open(temp_path, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2, sort_keys=True)
    os.replace(temp_path, THREAD_STATE_PATH)


def get_thread_state(issue_key: str, field_key: str) -> Dict[str, str]:
    state = load_thread_state_map()
    issue_state = state.get(issue_key)
    if not isinstance(issue_state, dict):
        return {}
    field_state = issue_state.get(field_key)
    if not isinstance(field_state, dict):
        return {}
    return field_state


def save_thread_state(issue_key: str, field_key: str, chat_id: str, thread_id: int) -> None:
    state = load_thread_state_map()
    issue_state = state.setdefault(issue_key, {})
    issue_state[field_key] = {
        "chat_id": normalize_text_value(chat_id),
        "thread_id": str(int(thread_id)),
    }
    save_thread_state_map(state)


def load_stage_event_state_map() -> Dict[str, Dict[str, Dict[str, Any]]]:
    try:
        if not os.path.exists(STAGE_EVENT_STATE_PATH):
            return {}
        with open(STAGE_EVENT_STATE_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            return data
    except Exception as exc:
        log(f"[load_stage_event_state_map] ERROR: {exc}")
    return {}


def save_stage_event_state_map(state: Dict[str, Dict[str, Dict[str, Any]]]) -> None:
    os.makedirs(os.path.dirname(STAGE_EVENT_STATE_PATH), exist_ok=True)
    temp_path = f"{STAGE_EVENT_STATE_PATH}.tmp"
    with open(temp_path, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2, sort_keys=True)
    os.replace(temp_path, STAGE_EVENT_STATE_PATH)


def stage_event_already_processed(issue_key: str, stage_code: str) -> bool:
    state = load_stage_event_state_map()
    issue_state = state.get(issue_key)
    if not isinstance(issue_state, dict):
        return False
    event_state = issue_state.get(stage_code)
    return isinstance(event_state, dict) and bool(event_state.get("processed"))


def mark_stage_event_processed(issue_key: str, stage_code: str, payload: Optional[Dict[str, Any]] = None) -> None:
    state = load_stage_event_state_map()
    issue_state = state.setdefault(issue_key, {})
    issue_state[stage_code] = {
        "processed": True,
        "payload": payload or {},
    }
    save_stage_event_state_map(state)


def finance_message_stage_code(marker_comment_id: Optional[Any]) -> str:
    return f"finance_message::{marker_comment_id or 'latest'}"


def finance_message_already_processed(finance_issue_key: str, marker_comment_id: Optional[Any]) -> bool:
    return stage_event_already_processed(finance_issue_key, finance_message_stage_code(marker_comment_id))


def mark_finance_message_processed(
    finance_issue_key: str,
    marker_comment_id: Optional[Any],
    payload: Optional[Dict[str, Any]] = None,
) -> None:
    mark_stage_event_processed(
        finance_issue_key,
        finance_message_stage_code(marker_comment_id),
        payload=payload,
    )


@contextmanager
def issue_stage_lock(issue_key: str):
    os.makedirs(STAGE_LOCK_DIR, exist_ok=True)
    safe_key = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in issue_key)
    lock_path = os.path.join(STAGE_LOCK_DIR, f"{safe_key}.lock")
    with open(lock_path, "w", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def get_issue_thread_id(issue: Dict[str, Any], field_key: str) -> Optional[int]:
    thread_id = normalize_thread_id(get_issue_field_value(issue, field_key))
    if thread_id is not None:
        return thread_id

    issue_key = normalize_text_value(issue.get("key"))
    if not issue_key:
        return None

    fallback_state = get_thread_state(issue_key, field_key)
    return normalize_thread_id(fallback_state.get("thread_id"))


def set_issue_field_if_present(issue: Dict[str, Any], payload: Dict[str, Any], field_key: str, value: Any) -> bool:
    resolved_key = resolve_issue_field_key(issue, field_key)
    if not resolved_key:
        return False

    normalized_current = normalize_text_value(issue.get(resolved_key))
    normalized_target = normalize_text_value(value)
    if normalized_current == normalized_target:
        return False

    payload[resolved_key] = value
    issue[resolved_key] = value
    return True


def save_issue_thread_id(
    issue_key: str,
    field_key: str,
    thread_id: int,
    issue: Optional[Dict[str, Any]] = None,
    chat_id: str = "",
) -> None:
    save_issue_field_value(issue_key, issue or {}, field_key, str(int(thread_id)))
    save_thread_state(issue_key, field_key, chat_id, thread_id)


def load_project_thread_state_map() -> Dict[str, Dict[str, str]]:
    try:
        if not os.path.exists(PROJECT_THREAD_STATE_PATH):
            return {}
        with open(PROJECT_THREAD_STATE_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            return data
    except Exception as exc:
        log(f"[load_project_thread_state_map] ERROR: {exc}")
    return {}


def save_project_thread_state_map(state: Dict[str, Dict[str, str]]) -> None:
    directory = os.path.dirname(PROJECT_THREAD_STATE_PATH) or "."
    os.makedirs(directory, exist_ok=True)
    temp_path = f"{PROJECT_THREAD_STATE_PATH}.tmp"
    with open(temp_path, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2)
    os.replace(temp_path, PROJECT_THREAD_STATE_PATH)


def get_project_thread_state(issue_key: str) -> Dict[str, str]:
    state = load_project_thread_state_map()
    item = state.get(issue_key)
    if isinstance(item, dict):
        return {
            "chat_id": str(item.get("chat_id") or "").strip(),
            "thread_id": str(item.get("thread_id") or "").strip(),
        }
    return {"chat_id": "", "thread_id": ""}


def save_project_thread_state(issue_key: str, chat_id: str, thread_id: int) -> None:
    state = load_project_thread_state_map()
    state[issue_key] = {
        "chat_id": str(chat_id or "").strip(),
        "thread_id": str(int(thread_id)),
    }
    save_project_thread_state_map(state)


def get_or_create_issue_thread_id(
    issue_key: str,
    issue: Dict[str, Any],
    chat_id: str,
    field_key: str,
    root_message_factory,
) -> int:
    existing = get_issue_thread_id(issue, field_key)
    if existing:
        return existing

    response = root_message_factory()
    message_id = response.get("message_id")
    normalized_message_id = normalize_thread_id(message_id)
    if normalized_message_id is None:
        raise ValueError(f"root message_id is missing for {issue_key} in {chat_id}: {response}")

    save_issue_field_value(issue_key, issue, field_key, str(normalized_message_id))
    save_thread_state(issue_key, field_key, chat_id, normalized_message_id)
    return normalized_message_id


def save_project_notification_thread_state(issue_key: str, issue: Dict[str, Any], chat_id: str, thread_id: int) -> None:
    save_project_thread_state(issue_key, chat_id, thread_id)
    save_chat_thread_state(
        issue_key,
        issue,
        chat_field=PROJECT_NOTIFICATIONS_CHAT_FIELD,
        thread_field=PROJECT_NOTIFICATIONS_THREAD_FIELD,
        chat_id=chat_id,
        thread_id=thread_id,
    )


def save_chat_thread_state(
    issue_key: str,
    issue: Dict[str, Any],
    chat_field: str,
    thread_field: str,
    chat_id: str,
    thread_id: int,
) -> None:
    payload: Dict[str, Any] = {}

    resolved_thread_field = resolve_issue_field_key(issue, thread_field)
    if resolved_thread_field:
        payload[resolved_thread_field] = str(int(thread_id))

    resolved_chat_field = resolve_issue_field_key(issue, chat_field)
    if resolved_chat_field:
        payload[resolved_chat_field] = chat_id

    if not payload:
        raise ValueError("chat/thread state fields are not configured")

    update_issue(issue_key, payload)
    for key, value in payload.items():
        issue[key] = value
    save_thread_state(issue_key, thread_field, chat_id, thread_id)


def comment_exists(issue_key: str, text: str) -> bool:
    try:
        comments = get_comments(issue_key)
        normalized = text.strip()
        return any((comment.get("text") or "").strip() == normalized for comment in comments)
    except Exception as exc:
        log(f"[comment_exists] ERROR for {issue_key}: {exc}")
        return False


def add_comment_once(issue_key: str, text: str) -> None:
    if comment_exists(issue_key, text):
        log(f"[add_comment_once] comment already exists in {issue_key}: {text}")
        return
    add_comment(issue_key, text)


def get_last_nonempty_comment_text(issue_key: str) -> str:
    comments = get_comments(issue_key)

    for comment in reversed(comments):
        text = (comment.get("text") or "").strip()
        if text:
            return text

    return ""


def sanitize_tracker_comment_tail(text: str) -> str:
    normalized = html.unescape(text or "").replace("\xa0", " ")
    lines = normalized.replace("\r\n", "\n").split("\n")
    cleaned_lines: List[str] = []
    previous_blank = False

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            if not previous_blank and cleaned_lines:
                cleaned_lines.append("")
            previous_blank = True
            continue

        if re.fullmatch(r"[*_~`#>\-]{3,}", line):
            continue

        if line.startswith("**") and line.endswith("**") and len(line) > 4:
            line = line[2:-2].strip()

        if not line:
            continue

        cleaned_lines.append(line)
        previous_blank = False

    while cleaned_lines and cleaned_lines[-1] == "":
        cleaned_lines.pop()

    return "\n".join(cleaned_lines).strip()


def extract_marker_comment_tail(text: str, marker: str) -> str:
    normalized_text = (text or "").replace("\r\n", "\n").strip()
    if not normalized_text or not marker_in_text(normalized_text, marker):
        return ""

    lines = [line.rstrip() for line in normalized_text.split("\n")]
    tail_lines: List[str] = []
    marker_consumed = False
    normalized_marker = normalize_marker_text(marker)

    for line in lines:
        stripped = line.strip()
        normalized_line = normalize_marker_text(stripped)
        if not marker_consumed and normalized_line == normalized_marker:
            marker_consumed = True
            continue
        if not marker_consumed and normalized_marker and normalized_marker in normalized_line:
            marker_consumed = True
            if normalized_line != normalized_marker:
                remainder = stripped
                for candidate in [marker, "Счет на согласование", "Cчет на согласование", "Счёт на согласование"]:
                    if candidate in remainder:
                        remainder = remainder.replace(candidate, "", 1)
                        break
                remainder = remainder.strip(" :-")
                if remainder:
                    tail_lines.append(remainder)
            continue
        if marker_consumed:
            tail_lines.append(line)

    return sanitize_tracker_comment_tail("\n".join(tail_lines))


def get_latest_marker_comment_context(issue_key: str, marker: str) -> Dict[str, Any]:
    comments = get_comments(issue_key)

    for comment in reversed(comments):
        text = (comment.get("text") or "").strip()
        if not marker_in_text(text, marker):
            continue
        return {
            "text": text,
            "tail_text": extract_marker_comment_tail(text, marker),
            "attachments": dedupe_attachments(comment.get("attachments") or []),
            "id": comment.get("id"),
        }

    return {
        "text": "",
        "tail_text": "",
        "attachments": [],
        "id": None,
    }


def finance_rejection_marker(finance_issue_key: str) -> str:
    return f"[finance_rejected:{finance_issue_key}]"


def finance_rejection_already_processed(supply_issue_key: str, finance_issue_key: str) -> bool:
    marker = finance_rejection_marker(finance_issue_key)
    try:
        comments = get_comments(supply_issue_key)
        return any(marker in (comment.get("text") or "") for comment in comments)
    except Exception as exc:
        log(f"[finance_rejection_already_processed] ERROR for {supply_issue_key}: {exc}")
        return False




def paid_invoice_marker(accounting_issue_key: str, comment_id: Optional[Any] = None) -> str:
    normalized_comment_id = normalize_text_value(comment_id)
    if normalized_comment_id:
        return f"[paid_invoice:{accounting_issue_key}:{normalized_comment_id}]"
    return f"[paid_invoice:{accounting_issue_key}]"


def paid_invoice_already_processed(
    supply_issue_key: str,
    accounting_issue_key: str,
    comment_id: Optional[Any] = None,
) -> bool:
    marker = paid_invoice_marker(accounting_issue_key, comment_id)
    try:
        comments = get_comments(supply_issue_key)
        return any(marker in (comment.get("text") or "") for comment in comments)
    except Exception as exc:
        log(f"[paid_invoice_already_processed] ERROR for {supply_issue_key}: {exc}")
        return False

def reset_finance_issue_created_flag(supply_issue_key: str, supply_issue: Dict[str, Any]) -> bool:
    field_key = resolve_issue_field_key(supply_issue, "aFinancialIssueHasBeenCreated")
    if not field_key:
        log(f"[reset_finance_issue_created_flag] field not found in {supply_issue_key}")
        return False

    field_value = supply_issue.get(field_key)

    normalized = str(field_value).strip().lower() if field_value is not None else ""
    # Hidden Tracker fields may be omitted from issue payloads even when they still
    # contain "Да". In that case we must still force-reset the flag, otherwise a
    # repeated finance task cannot be created after rejection.
    if normalized in {"нет", "false", "no", "0"}:
        log(f"[reset_finance_issue_created_flag] already reset in {supply_issue_key}")
        return False

    update_issue(supply_issue_key, {field_key: "Нет"})
    supply_issue[field_key] = "Нет"
    log(f"[reset_finance_issue_created_flag] reset in {supply_issue_key}")
    return True


def get_display(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return value.get("display") or value.get("name") or value.get("key") or value.get("id") or ""
    if isinstance(value, list):
        parts = [get_display(item) for item in value]
        parts = [part for part in parts if part]
        return ", ".join(parts)
    return str(value)


def normalize_ref_value(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, dict):
        if value.get("id") is not None:
            return {"id": value["id"]}
        if value.get("key") is not None:
            return {"key": value["key"]}
        return None

    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else None

    return value


def get_date_pair(issue: Dict[str, Any]) -> Tuple[Optional[str], Any]:
    return get_custom_field(issue, DATE_SUFFIX)


def get_object_pair(issue: Dict[str, Any]) -> Tuple[Optional[str], Any]:
    if issue.get("object") is not None:
        return "object", issue.get("object")
    return get_custom_field(issue, OBJECT_SUFFIX)


def get_initiator_pair(issue: Dict[str, Any]) -> Tuple[Optional[str], Any]:
    if issue.get("initiator") is not None:
        return "initiator", issue.get("initiator")
    return get_custom_field(issue, INITIATOR_SUFFIX)


def get_application_type_pair(issue: Dict[str, Any]) -> Tuple[Optional[str], Any]:
    if issue.get("applicationType") is not None:
        return "applicationType", issue.get("applicationType")
    return get_custom_field(issue, APPLICATION_TYPE_SUFFIX)


def get_application_outline_pair(issue: Dict[str, Any]) -> Tuple[Optional[str], Any]:
    if issue.get("applicationOutline") is not None:
        return "applicationOutline", issue.get("applicationOutline")
    return get_custom_field(issue, APPLICATION_OUTLINE_SUFFIX)


def get_functional_block_pair(issue: Dict[str, Any]) -> Tuple[Optional[str], Any]:
    return get_custom_field_multi(issue, FUNCTIONAL_BLOCK_SUFFIXES)


def resolve_functional_block_field_key(issue: Optional[Dict[str, Any]]) -> str:
    if issue:
        existing_key, _ = get_functional_block_pair(issue)
        if existing_key:
            return existing_key

    for suffix in FUNCTIONAL_BLOCK_SUFFIXES:
        resolved_key = resolve_issue_field_key(issue, suffix)
        if resolved_key:
            return resolved_key

    return "functionalBlock"


def get_date_display(issue: Optional[Dict[str, Any]]) -> str:
    if not issue:
        return ""
    return get_display(get_date_pair(issue)[1])


def get_object_display(issue: Optional[Dict[str, Any]]) -> str:
    if not issue:
        return ""
    return get_display(get_object_pair(issue)[1])


def get_initiator_display(issue: Optional[Dict[str, Any]]) -> str:
    if not issue:
        return ""
    return get_display(get_initiator_pair(issue)[1])


def get_application_type_display(issue: Optional[Dict[str, Any]]) -> str:
    if not issue:
        return ""
    return get_display(get_application_type_pair(issue)[1])


def get_application_outline_display(issue: Optional[Dict[str, Any]]) -> str:
    if not issue:
        return ""
    return get_display(get_application_outline_pair(issue)[1])


def get_functional_block_display(issue: Optional[Dict[str, Any]]) -> str:
    if not issue:
        return ""
    return get_display(get_functional_block_pair(issue)[1])


def get_context_mode(issue: Optional[Dict[str, Any]]) -> str:
    if not issue:
        return "object"

    outline = normalize_text_value(get_application_outline_display(issue)).lower()
    if outline == "внутренняя":
        return "internal"
    if outline == "проектная":
        return "project"
    initiator_display = get_initiator_display(issue).strip()
    object_display = get_object_display(issue).strip()
    if get_queue_key(issue) == "TESTG" and initiator_display:
        return "project"
    if get_queue_key(issue) == "OPS" and initiator_display and not object_display:
        return "project"
    return "object"


def get_context_pair(issue: Dict[str, Any]) -> Tuple[Optional[str], Any]:
    mode = get_context_mode(issue)
    if mode in {"project", "internal"}:
        initiator_key, initiator_value = get_initiator_pair(issue)
        if initiator_key and get_display(initiator_value).strip():
            return initiator_key, initiator_value
    return get_object_pair(issue)


def get_context_display(issue: Optional[Dict[str, Any]]) -> str:
    if not issue:
        return ""
    return get_display(get_context_pair(issue)[1])


def get_context_label(issue: Optional[Dict[str, Any]]) -> str:
    mode = get_context_mode(issue)
    if mode in {"project", "internal"}:
        return "🏢 Инициатор"
    return "🏗 Объект"


def get_context_wiki_link(issue: Optional[Dict[str, Any]]) -> Optional[str]:
    context_name = get_context_display(issue).strip()
    if not context_name:
        return None

    if get_context_mode(issue) == "internal":
        return DEPARTMENT_WIKI_MAP.get(context_name)
    return OBJECT_WIKI_MAP.get(context_name)


def get_context_wiki_label(issue: Optional[Dict[str, Any]]) -> str:
    return "📚 Wiki отдела" if get_context_mode(issue) == "internal" else "📚 Wiki по объекту"


def issue_has_context(issue: Optional[Dict[str, Any]]) -> bool:
    return bool(get_context_display(issue).strip())


def resolve_project_notifications_chat(issue: Optional[Dict[str, Any]]) -> Dict[str, str]:
    object_name = get_context_display(issue)
    normalized_object = normalize_object_name(object_name)
    context_mode = get_context_mode(issue)
    project_chat_id = resolve_issue_chat_id(issue, "project")

    if context_mode == "internal" and normalized_object:
        initiator_chat_id = ""
        if get_queue_key(issue) == "TESTG":
            initiator_chat_id = TEST_INITIATOR_CHAT_MAP.get(normalized_object, "").strip()
        if not initiator_chat_id:
            initiator_chat_id = BASE_FUNCTIONAL_BLOCK_CHAT_MAP.get(normalized_object, "").strip()
        if initiator_chat_id:
            return {
                "object_name": object_name,
                "normalized_object": normalized_object,
                "chat_id": initiator_chat_id,
                "source": "test_initiator_chat_map" if get_queue_key(issue) == "TESTG" and TEST_INITIATOR_CHAT_MAP.get(normalized_object) else "department_initiator_chat_map",
            }

    if normalized_object:
        mapped_project_chat_id = resolve_object_project_chat_id(object_name)
        if mapped_project_chat_id:
            return {
                "object_name": object_name,
                "normalized_object": normalized_object,
                "chat_id": mapped_project_chat_id,
                "source": "object_project_chat_map",
            }
        if project_chat_id:
            return {
                "object_name": object_name,
                "normalized_object": normalized_object,
                "chat_id": project_chat_id,
                "source": "queue_project_chat",
            }

    return {
        "object_name": object_name,
        "normalized_object": normalized_object,
        "chat_id": "",
        "source": "missing_object_mapping",
    }


def resolve_department_chat(issue: Optional[Dict[str, Any]]) -> Dict[str, str]:
    functional_block = get_functional_block_display(issue)
    normalized_block = normalize_object_name(functional_block)
    queue_chat_config = chat_config_for_queue(get_queue_key(issue))
    queue_key = get_queue_key(issue)

    if normalized_block == "снабжение":
        mapped_chat_id = queue_chat_config.get("supply") or ""
        if mapped_chat_id:
            return {
                "functional_block": functional_block,
                "normalized_functional_block": normalized_block,
                "chat_id": mapped_chat_id,
                "source": "queue_supply_chat",
            }

    if normalized_block == "финансы":
        mapped_chat_id = queue_chat_config.get("finance") or ""
        if mapped_chat_id:
            return {
                "functional_block": functional_block,
                "normalized_functional_block": normalized_block,
                "chat_id": mapped_chat_id,
                "source": "queue_finance_chat",
            }

    if normalized_block == "бухгалтерия":
        mapped_chat_id = queue_chat_config.get("accounting") or ""
        if mapped_chat_id:
            return {
                "functional_block": functional_block,
                "normalized_functional_block": normalized_block,
                "chat_id": mapped_chat_id,
                "source": "queue_accounting_chat",
            }

    if is_administration_block_value(functional_block):
        mapped_chat_id = ""
        if queue_key == "TESTG":
            mapped_chat_id = TEST_DEPARTMENT_CHAT_MAP.get(normalized_block, "").strip()
        if not mapped_chat_id:
            mapped_chat_id = BASE_FUNCTIONAL_BLOCK_CHAT_MAP.get(normalized_block) or queue_chat_config.get("supply") or ""
        if mapped_chat_id:
            return {
                "functional_block": functional_block,
                "normalized_functional_block": normalized_block,
                "chat_id": mapped_chat_id,
                "source": "test_administration_chat_map" if queue_key == "TESTG" and TEST_DEPARTMENT_CHAT_MAP.get(normalized_block) else "administration_chat_fallback",
            }

    if normalized_block:
        mapped_chat_id = BASE_FUNCTIONAL_BLOCK_CHAT_MAP.get(normalized_block)
        if mapped_chat_id:
            return {
                "functional_block": functional_block,
                "normalized_functional_block": normalized_block,
                "chat_id": mapped_chat_id,
                "source": "functional_block_map",
            }

    return {
        "functional_block": functional_block,
        "normalized_functional_block": normalized_block,
        "chat_id": "",
        "source": "missing_functional_block_mapping",
    }


def resolve_source_chat_id(issue: Optional[Dict[str, Any]]) -> str:
    if issue and is_initiator_finance_source_issue(issue):
        routing = resolve_project_notifications_chat(issue)
        if routing.get("chat_id"):
            return routing["chat_id"]

    routing = resolve_department_chat(issue)
    if routing.get("chat_id"):
        return routing["chat_id"]
    return resolve_issue_chat_id(issue, "supply")


def sync_issue_chat_link_fields(issue_key: str, issue: Dict[str, Any]) -> Dict[str, str]:
    project_routing = resolve_project_notifications_chat(issue)
    department_routing = resolve_department_chat(issue)
    context_mode = get_context_mode(issue)

    payload: Dict[str, Any] = {}
    project_chat_link = ""
    if context_mode != "internal":
        project_chat_link = build_messenger_chat_link(project_routing.get("chat_id") or "")
    department_chat_link = build_messenger_chat_link(department_routing.get("chat_id") or "")

    project_field_updated = set_issue_field_if_present(issue, payload, PROJECT_CHAT_LINK_FIELD, project_chat_link)
    department_field_updated = set_issue_field_if_present(issue, payload, DEPARTMENT_CHAT_LINK_FIELD, department_chat_link)

    if payload:
        update_issue(issue_key, payload)

    return {
        "project_chat_id": project_routing.get("chat_id") or "",
        "project_chat_link": project_chat_link,
        "project_source": project_routing.get("source") or "",
        "department_chat_id": department_routing.get("chat_id") or "",
        "department_chat_link": department_chat_link,
        "department_source": department_routing.get("source") or "",
        "project_field_updated": "yes" if project_field_updated else "no",
        "department_field_updated": "yes" if department_field_updated else "no",
    }


def parse_csv_set(value: str, normalize_upper: bool = False) -> set[str]:
    result: set[str] = set()
    for item in str(value or "").split(","):
        text = item.strip()
        if not text:
            continue
        result.add(text.upper() if normalize_upper else text)
    return result


def parse_normalized_csv_set(value: str) -> set[str]:
    return {
        normalized
        for normalized in (normalize_display_token(item) for item in str(value or "").split(","))
        if normalized
    }


def normalize_board_id(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, dict):
        return normalize_board_id(value.get("id"))
    if isinstance(value, int):
        return value
    text_value = str(value).strip()
    if not text_value:
        return None
    try:
        return int(text_value)
    except ValueError:
        return None


def load_department_board_map() -> Dict[str, int]:
    mapping = {
        normalize_display_token(name): int(board_id)
        for name, board_id in DEFAULT_DEPARTMENT_BOARD_MAP.items()
        if normalize_display_token(name)
    }

    if not DEPARTMENT_BOARD_MAP_JSON.strip():
        return mapping

    try:
        custom_mapping = json.loads(DEPARTMENT_BOARD_MAP_JSON)
    except Exception as exc:
        log(f"[load_department_board_map] invalid JSON: {exc}")
        return mapping

    if not isinstance(custom_mapping, dict):
        log("[load_department_board_map] DEPARTMENT_BOARD_MAP_JSON must be an object")
        return mapping

    for name, raw_board_id in custom_mapping.items():
        normalized_name = normalize_display_token(name)
        board_id = normalize_board_id(raw_board_id)
        if normalized_name and board_id is not None:
            mapping[normalized_name] = board_id

    return mapping


def load_project_board_map() -> Dict[str, int]:
    mapping = {
        normalize_display_token(name): int(board_id)
        for name, board_id in DEFAULT_PROJECT_BOARD_MAP.items()
        if normalize_display_token(name)
    }

    if not PROJECT_BOARD_MAP_JSON.strip():
        return mapping

    try:
        custom_mapping = json.loads(PROJECT_BOARD_MAP_JSON)
    except Exception as exc:
        log(f"[load_project_board_map] invalid JSON: {exc}")
        return mapping

    if not isinstance(custom_mapping, dict):
        log("[load_project_board_map] PROJECT_BOARD_MAP_JSON must be an object")
        return mapping

    for name, raw_board_id in custom_mapping.items():
        normalized_name = normalize_display_token(name)
        board_id = normalize_board_id(raw_board_id)
        if normalized_name and board_id is not None:
            mapping[normalized_name] = board_id

    return mapping


def load_controlled_department_board_ids(
    department_board_map: Optional[Dict[str, int]] = None,
    project_board_map: Optional[Dict[str, int]] = None,
) -> set[int]:
    ids: set[int] = set((department_board_map or load_department_board_map()).values())
    ids.update((project_board_map or load_project_board_map()).values())
    operations_director_board_id = normalize_board_id(OPERATIONS_DIRECTOR_BOARD_ID)
    if operations_director_board_id is not None:
        ids.add(operations_director_board_id)
    for item in parse_csv_set(CONTROLLED_DEPARTMENT_BOARD_IDS):
        board_id = normalize_board_id(item)
        if board_id is not None:
            ids.add(board_id)
    return ids


def get_issue_board_ids(issue: Dict[str, Any]) -> List[int]:
    board_ids: List[int] = []
    boards_value = get_issue_field_value(issue, DEPARTMENT_BOARD_FIELD)
    if not isinstance(boards_value, list):
        return board_ids

    for item in boards_value:
        board_id = normalize_board_id(item)
        if board_id is not None and board_id not in board_ids:
            board_ids.append(board_id)
    return board_ids


def resolve_department_board_targets(issue: Dict[str, Any]) -> Dict[str, Any]:
    department_board_map = load_department_board_map()
    project_board_map = load_project_board_map()
    sources = [
        ("initiator", get_initiator_display(issue)),
        ("functional_block", get_functional_block_display(issue)),
    ]

    targets: List[Dict[str, Any]] = []
    unmapped: List[Dict[str, str]] = []
    seen_ids: set[int] = set()

    for source, display_value in sources:
        display_text = normalize_text_value(display_value)
        normalized_value = normalize_display_token(display_text)
        if not normalized_value:
            continue

        board_id = department_board_map.get(normalized_value)
        if board_id is None:
            unmapped.append({
                "source": source,
                "display": display_text,
                "normalized": normalized_value,
            })
            continue

        if board_id in seen_ids:
            continue
        seen_ids.add(board_id)
        targets.append({
            "source": source,
            "display": display_text,
            "normalized": normalized_value,
            "board_id": board_id,
        })

    context_display = get_context_display(issue)
    normalized_context = normalize_display_token(context_display)
    context_mode = get_context_mode(issue)

    if context_mode == "internal":
        operations_director_board_id = normalize_board_id(OPERATIONS_DIRECTOR_BOARD_ID)
        if operations_director_board_id is not None and operations_director_board_id not in seen_ids:
            seen_ids.add(operations_director_board_id)
            targets.append({
                "source": "application_outline",
                "display": get_application_outline_display(issue),
                "normalized": normalize_display_token(get_application_outline_display(issue)),
                "board_id": operations_director_board_id,
            })
    elif normalized_context:
        project_board_id = project_board_map.get(normalized_context)
        if project_board_id is None:
            unmapped.append({
                "source": "project_context",
                "display": context_display,
                "normalized": normalized_context,
            })
        elif project_board_id not in seen_ids:
            seen_ids.add(project_board_id)
            targets.append({
                "source": "project_context",
                "display": context_display,
                "normalized": normalized_context,
                "board_id": project_board_id,
            })

    application_type_display = get_application_type_display(issue)
    normalized_application_type = normalize_display_token(application_type_display)
    operations_director_application_types = parse_normalized_csv_set(OPERATIONS_DIRECTOR_APPLICATION_TYPES)
    operations_director_board_id = normalize_board_id(OPERATIONS_DIRECTOR_BOARD_ID)
    if (
        normalized_application_type
        and normalized_application_type in operations_director_application_types
        and operations_director_board_id is not None
        and operations_director_board_id not in seen_ids
    ):
        seen_ids.add(operations_director_board_id)
        targets.append({
            "source": "application_type",
            "display": application_type_display,
            "normalized": normalized_application_type,
            "board_id": operations_director_board_id,
        })

    return {
        "targets": targets,
        "unmapped": unmapped,
        "department_board_map": department_board_map,
        "project_board_map": project_board_map,
    }


def sync_department_boards(issue_key: str, issue: Dict[str, Any]) -> Dict[str, Any]:
    queue_key = get_queue_key(issue)
    allowed_queues = parse_csv_set(DEPARTMENT_BOARD_SYNC_QUEUES, normalize_upper=True)
    if "*" not in allowed_queues and queue_key not in allowed_queues:
        return {
            "updated": False,
            "skipped": True,
            "reason": "queue_not_enabled",
            "queue_key": queue_key,
            "enabled_queues": sorted(allowed_queues),
        }

    target_result = resolve_department_board_targets(issue)
    desired_department_board_ids = [
        item["board_id"] for item in target_result["targets"]
    ]
    controlled_board_ids = load_controlled_department_board_ids(
        target_result["department_board_map"],
        target_result["project_board_map"],
    )
    current_board_ids = get_issue_board_ids(issue)

    final_board_ids: List[int] = []
    for board_id in current_board_ids:
        if board_id not in controlled_board_ids and board_id not in final_board_ids:
            final_board_ids.append(board_id)

    for board_id in desired_department_board_ids:
        if board_id not in final_board_ids:
            final_board_ids.append(board_id)

    added_ids = [board_id for board_id in final_board_ids if board_id not in current_board_ids]
    removed_ids = [
        board_id
        for board_id in current_board_ids
        if board_id in controlled_board_ids and board_id not in final_board_ids
    ]
    if not added_ids and not removed_ids:
        final_board_ids = current_board_ids[:]

    result: Dict[str, Any] = {
        "updated": False,
        "skipped": False,
        "reason": "no_change",
        "queue_key": queue_key,
        "current_board_ids": current_board_ids,
        "final_board_ids": final_board_ids,
        "desired_department_board_ids": desired_department_board_ids,
        "controlled_department_board_ids": sorted(controlled_board_ids),
        "added_ids": added_ids,
        "removed_ids": removed_ids,
        "targets": target_result["targets"],
        "unmapped": target_result["unmapped"],
    }

    if final_board_ids == current_board_ids:
        return result

    payload = {
        resolve_issue_field_key(issue, DEPARTMENT_BOARD_FIELD): [
            {"id": board_id} for board_id in final_board_ids
        ]
    }
    update_issue(issue_key, payload)
    result["updated"] = True
    result["reason"] = "updated"
    return result


def build_wiki_block(issue: Optional[Dict[str, Any]]) -> str:
    wiki_link = get_context_wiki_link(issue)
    if not wiki_link:
        return ""
    return f"\n\n{get_context_wiki_label(issue)}:\n{wiki_link}"


def ensure_wiki_comment(issue_key: str, issue: Optional[Dict[str, Any]]) -> None:
    wiki_link = get_context_wiki_link(issue)
    if not wiki_link:
        return

    try:
        comments = get_comments(issue_key)
        normalized_link = wiki_link.strip()
        for comment in comments:
            text = comment.get("text") or ""
            if normalized_link in text:
                log(f"[ensure_wiki_comment] wiki already exists in {issue_key}")
                return

        add_comment(issue_key, f"{get_context_wiki_label(issue)}:\n{wiki_link}")
        log(f"[ensure_wiki_comment] wiki comment added to {issue_key}")
    except Exception as exc:
        log(f"[ensure_wiki_comment] ERROR for {issue_key}: {exc}")


def get_attachments(issue: Dict[str, Any]) -> List[Dict[str, Any]]:
    return issue.get("attachments") or []


def resolve_attachment_name(att: Dict[str, Any]) -> str:
    return (
        att.get("name")
        or att.get("display")
        or att.get("filename")
        or f"attachment_{att.get('id', 'file')}"
    )


def download_attachment(issue_key: str, att: Dict[str, Any]) -> Tuple[bytes, str, str]:
    att_id = att.get("id")
    if not att_id:
        raise ValueError("attachment id is missing")

    filename = resolve_attachment_name(att)
    encoded_filename = quote(filename)

    r = requests.get(
        f"{TRACKER_BASE}/issues/{issue_key}/attachments/{att_id}/{encoded_filename}",
        headers=tracker_file_headers(),
        timeout=DOWNLOAD_TIMEOUT,
        allow_redirects=True,
    )
    r.raise_for_status()

    content_type = (r.headers.get("Content-Type") or "").split(";")[0].strip()
    if not content_type or content_type == "application/json":
        content_type = att.get("mimetype") or mimetypes.guess_type(filename)[0] or "application/octet-stream"

    return r.content, filename, content_type


def issue_attachment_names(issue_key: str) -> set[str]:
    try:
        issue = get_issue(issue_key)
    except Exception as exc:
        log(f"[issue_attachment_names] ERROR for {issue_key}: {exc}")
        return set()

    return {
        resolve_attachment_name(att).strip().lower()
        for att in dedupe_attachments(get_attachments(issue))
    }


def upload_temporary_attachment(file_bytes: bytes, filename: str, content_type: Optional[str] = None) -> Dict[str, Any]:
    if not content_type:
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    r = requests.post(
        f"{TRACKER_BASE}/attachments/",
        headers=tracker_file_headers(),
        files={"file": (filename, file_bytes, content_type)},
        timeout=DOWNLOAD_TIMEOUT,
    )
    r.raise_for_status()
    if not r.text.strip():
        return {}
    return r.json()


def ensure_file_commented_to_issue(
    issue_key: str,
    file_bytes: bytes,
    filename: str,
    comment_text: str,
    content_type: Optional[str] = None,
    skip_if_issue_has_filename: bool = True,
) -> bool:
    if skip_if_issue_has_filename:
        existing_names = issue_attachment_names(issue_key)
        normalized_name = filename.strip().lower()
        if normalized_name in existing_names:
            log(f"[ensure_file_commented_to_issue] already present in {issue_key}: {filename}")
            return False

    uploaded = upload_temporary_attachment(file_bytes, filename, content_type)
    attachment_id = uploaded.get("id")
    if attachment_id is None:
        raise ValueError(f"temporary attachment upload failed for {filename}: {uploaded}")

    add_comment(issue_key, comment_text, attachment_ids=[str(attachment_id)])
    log(f"[ensure_file_commented_to_issue] added comment with attachment to {issue_key}: {filename}")
    return True


def dedupe_attachments(attachments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    unique: List[Dict[str, Any]] = []
    seen = set()

    for att in attachments:
        att_id = att.get("id")
        name = resolve_attachment_name(att).strip().lower()

        key = ("id", str(att_id)) if att_id is not None else ("name", name)
        if key in seen:
            continue

        seen.add(key)
        unique.append(att)

    return unique


def send_issue_files(chat_id: str, issue_key: str, issue: Dict[str, Any], thread_id: Optional[int] = None, intro_text: Optional[str] = None) -> Tuple[List[str], List[str]]:
    sent: List[str] = []
    errors: List[str] = []
    intro_sent = False

    for att in dedupe_attachments(get_attachments(issue)):
        filename = resolve_attachment_name(att)
        try:
            file_bytes, final_name, content_type = download_attachment(issue_key, att)
            if intro_text and not intro_sent:
                send_text(chat_id, intro_text, thread_id=thread_id)
                intro_sent = True
            send_file(chat_id, file_bytes, final_name, content_type, thread_id=thread_id)
            sent.append(final_name)
            log(f"[send_issue_files] sent: {final_name}")
        except Exception as exc:
            error_text = f"{filename}: {exc}"
            errors.append(error_text)
            log(f"[send_issue_files] ERROR: {error_text}")

    return sent, errors


def get_issue_description_text(issue: Optional[Dict[str, Any]]) -> str:
    description = html.unescape(str((issue or {}).get("description") or "")).replace("\xa0", " ")
    if not description.strip():
        return ""

    normalized = description.replace("\r\n", "\n")
    normalized = re.sub(r"(?i)<br\\s*/?>", "\n", normalized)
    normalized = re.sub(r"(?i)</p>", "\n", normalized)
    normalized = re.sub(r"(?i)<p[^>]*>", "", normalized)
    normalized = re.sub(r"<[^>]+>", "", normalized)

    lines = normalized.split("\n")
    cleaned_lines: List[str] = []
    previous_blank = False

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            if not previous_blank and cleaned_lines:
                cleaned_lines.append("")
            previous_blank = True
            continue

        cleaned_lines.append(line)
        previous_blank = False

    while cleaned_lines and cleaned_lines[-1] == "":
        cleaned_lines.pop()

    return "\n".join(cleaned_lines).strip()


def send_issue_description_text(chat_id: str, issue: Dict[str, Any], thread_id: Optional[int] = None) -> bool:
    description_text = get_issue_description_text(issue)
    if not description_text:
        return False

    send_text(
        chat_id,
        f"📝 Описание задачи:\n{description_text}",
        thread_id=thread_id,
    )
    return True


def send_comment_files(chat_id: str, issue_key: str, already_sent_names: Optional[List[str]] = None, thread_id: Optional[int] = None, intro_text: Optional[str] = None, copy_to_issue_key: Optional[str] = None) -> Tuple[List[str], List[str]]:
    sent: List[str] = []
    errors: List[str] = []
    intro_sent = False
    already_sent = {name.strip().lower() for name in (already_sent_names or []) if name}

    comments = get_comments(issue_key)

    for comment in reversed(comments):
        text = comment.get("text") or ""
        if not marker_in_text(text, INVOICE_MARKER):
            continue

        for att in dedupe_attachments(comment.get("attachments") or []):
            filename = resolve_attachment_name(att)
            normalized_name = filename.strip().lower()

            if normalized_name in already_sent:
                log(f"[send_comment_files] skip duplicate: {filename}")
                continue

            try:
                file_bytes, final_name, content_type = download_attachment(issue_key, att)
                if copy_to_issue_key:
                    try:
                        ensure_file_commented_to_issue(copy_to_issue_key, file_bytes, final_name, "💰 Счет на согласование", content_type)
                    except Exception as attach_exc:
                        log(f"[send_comment_files] ERROR attaching to issue {copy_to_issue_key}: {attach_exc}")

                if intro_text and not intro_sent:
                    send_text(chat_id, intro_text, thread_id=thread_id)
                    intro_sent = True
                send_file(chat_id, file_bytes, final_name, content_type, thread_id=thread_id)
                sent.append(final_name)
                already_sent.add(final_name.strip().lower())
                log(f"[send_comment_files] sent: {final_name}")
            except Exception as exc:
                error_text = f"{filename}: {exc}"
                errors.append(error_text)
                log(f"[send_comment_files] ERROR: {error_text}")
        break

    return sent, errors


def send_marker_comment_files(
    source_issue_key: str,
    marker: str,
    chat_id: Optional[str] = None,
    thread_id: Optional[int] = None,
    intro_text: Optional[str] = None,
    copy_to_issue_key: Optional[str] = None,
    copy_comment_text: Optional[str] = None,
    copy_skip_if_issue_has_filename: bool = True,
    already_sent_names: Optional[List[str]] = None,
) -> Tuple[List[str], List[str]]:
    sent: List[str] = []
    errors: List[str] = []
    intro_sent = False
    already_sent = {name.strip().lower() for name in (already_sent_names or []) if name}

    comments = get_comments(source_issue_key)

    for comment in reversed(comments):
        text = comment.get("text") or ""
        if not marker_in_text(text, marker):
            continue

        for att in dedupe_attachments(comment.get("attachments") or []):
            filename = resolve_attachment_name(att)
            normalized_name = filename.strip().lower()

            if normalized_name in already_sent:
                log(f"[send_marker_comment_files] skip duplicate: {filename}")
                continue

            try:
                file_bytes, final_name, content_type = download_attachment(source_issue_key, att)

                if copy_to_issue_key and copy_comment_text:
                    try:
                        ensure_file_commented_to_issue(
                            copy_to_issue_key,
                            file_bytes,
                            final_name,
                            copy_comment_text,
                            content_type,
                            skip_if_issue_has_filename=copy_skip_if_issue_has_filename,
                        )
                    except Exception as attach_exc:
                        log(f"[send_marker_comment_files] ERROR attaching to issue {copy_to_issue_key}: {attach_exc}")

                if chat_id:
                    if intro_text and not intro_sent:
                        send_text(chat_id, intro_text, thread_id=thread_id)
                        intro_sent = True
                    send_file(chat_id, file_bytes, final_name, content_type, thread_id=thread_id)

                sent.append(final_name)
                already_sent.add(normalized_name)
                log(f"[send_marker_comment_files] sent: {final_name}")
            except Exception as exc:
                error_text = f"{filename}: {exc}"
                errors.append(error_text)
                log(f"[send_marker_comment_files] ERROR: {error_text}")
        break

    return sent, errors


def is_supply_issue(issue: Dict[str, Any]) -> bool:
    functional_block = get_source_block_display(issue)
    return is_source_block_value(functional_block)


def is_primary_supply_issue(issue: Dict[str, Any]) -> bool:
    if is_initiator_finance_source_issue(issue):
        return True
    if not is_supply_issue(issue):
        return False
    app_type = get_application_type_display(issue).strip().lower()
    return not is_supply_control_application_type_value(app_type)


def normalize_process_value(value: Any) -> str:
    return normalize_display_token(get_display(value))


def is_auto_created_finance_flow_issue(issue: Dict[str, Any]) -> bool:
    functional_block = normalize_process_value(get_functional_block_display(issue))
    summary = normalize_process_value(issue.get("summary") or "")
    return (
        functional_block in {normalize_process_value(FINANCE_BLOCK), "бухгалтерия"}
        and summary.startswith(normalize_process_value("Согласование оплаты счета"))
    )


def is_initiator_finance_source_issue(issue: Dict[str, Any]) -> bool:
    if is_auto_created_finance_flow_issue(issue):
        return False

    app_type = normalize_process_value(get_application_type_display(issue))
    route_display = normalize_process_value(get_issue_route_display(issue))
    allowed_app_types = parse_normalized_csv_set(INITIATOR_FINANCE_APP_TYPES)
    allowed_app_types.add(normalize_process_value(INITIATOR_FINANCE_APP_TYPE))
    if app_type in allowed_app_types:
        return True
    if route_display == normalize_process_value(INITIATOR_FINANCE_ROUTE):
        return True
    return False


def is_supply_control_application_type_value(value: Any) -> bool:
    normalized = str(value or "").strip().lower()
    return normalized in {
        SUPPLY_CONTROL_APP_TYPE.strip().lower(),
        ADMIN_SUPPLY_CONTROL_APP_TYPE.strip().lower(),
        INITIATOR_SUPPLY_CONTROL_APP_TYPE.strip().lower(),
    }


def is_initiator_supply_control_issue(issue: Dict[str, Any]) -> bool:
    app_type = normalize_process_value(get_application_type_display(issue))
    route_display = normalize_process_value(get_issue_route_display(issue))
    return (
        app_type == normalize_process_value(INITIATOR_SUPPLY_CONTROL_APP_TYPE)
        or route_display == normalize_process_value(INITIATOR_SUPPLY_CONTROL_ROUTE)
    )


def should_suppress_initiator_supply_control_start_notification(issue: Dict[str, Any], status_value: Any) -> bool:
    return (
        is_initiator_supply_control_issue(issue)
        and notification_class_for_status(status_value) == "created"
    )


def initiator_functional_block_display(issue: Dict[str, Any]) -> str:
    current_block = get_functional_block_display(issue).strip()
    if current_block and normalize_display_token(current_block) not in {
        normalize_display_token(FINANCE_BLOCK),
        "бухгалтерия",
    }:
        return current_block

    initiator_display = get_initiator_display(issue)
    normalized_initiator = normalize_display_token(initiator_display)
    initiator_to_block = {
        "отдел - снабжения": SUPPLY_BLOCK,
        "отдел - пто": "ПТО",
        "отдел - сдо": "СДО",
        "отдел - проектирования": "Проектирование",
        "производственный - отдел": "Производство",
        "отдел - кадров": "Кадры",
        "юридический - отдел": "Юридический",
        "финансовый - отдел": FINANCE_BLOCK,
        "отдел - бухгалтерии": "Бухгалтерия",
        "отдел - hr": "HR",
        "отдел - it": "IT",
        "отдел - продаж": "Продажи",
        "отдел - маркетинга": "Маркетинг",
        "административный - отдел": ADMINISTRATION_BLOCK,
    }
    if normalized_initiator in initiator_to_block:
        return initiator_to_block[normalized_initiator]

    if get_context_mode(issue) == "project":
        return "Проектный офис"

    return current_block or get_display(initiator_display).strip() or "Проектный офис"


def get_supply_control_profile(source_issue: Dict[str, Any]) -> Dict[str, str]:
    if is_initiator_finance_source_issue(source_issue):
        return {
            "application_type": INITIATOR_SUPPLY_CONTROL_APP_TYPE,
            "route": INITIATOR_SUPPLY_CONTROL_ROUTE,
            "functional_block": initiator_functional_block_display(source_issue),
        }

    source_block = get_source_block_display(source_issue)
    if is_administration_block_value(source_block):
        return {
            "application_type": ADMIN_SUPPLY_CONTROL_APP_TYPE,
            "route": ADMIN_SUPPLY_CONTROL_ROUTE,
            "functional_block": ADMINISTRATION_BLOCK,
        }

    return {
        "application_type": SUPPLY_CONTROL_APP_TYPE,
        "route": SUPPLY_CONTROL_ROUTE,
        "functional_block": SUPPLY_BLOCK,
    }


def init_initiator_finance_issue(issue_key: str, status_display: Any = None) -> Dict[str, Any]:
    issue = get_issue(issue_key)
    if not is_initiator_finance_source_issue(issue):
        raise ValueError("issue is not an initiator finance source issue")

    route_key = resolve_issue_field_key(issue, "route")
    functional_block_key = resolve_functional_block_field_key(issue)
    target_functional_block = initiator_functional_block_display(issue)

    payload: Dict[str, Any] = {}
    if route_key and get_issue_route_display(issue) != INITIATOR_FINANCE_ROUTE:
        payload[route_key] = INITIATOR_FINANCE_ROUTE

    if functional_block_key and get_functional_block_display(issue).strip() != target_functional_block:
        payload[functional_block_key] = target_functional_block

    updated = False
    if payload:
        update_issue(issue_key, payload)
        updated = True
        issue = get_issue(issue_key)

    chat_link_sync = {
        "skipped": True,
        "reason": "initiator_finance_init_is_silent",
    }
    notification_result = {
        "sent": False,
        "reason": "initiator_finance_init_is_silent",
    }

    return {
        "ok": True,
        "issue_key": issue_key,
        "updated": updated,
        "payload_keys": sorted(str(key) for key in payload.keys()),
        "route": INITIATOR_FINANCE_ROUTE,
        "functional_block": target_functional_block,
        "chat_link_sync": chat_link_sync,
        "project_notification": notification_result,
    }


def should_send_initiator_notification(issue_key: str, issue: Dict[str, Any]) -> Tuple[bool, str]:
    app_type = get_application_type_display(issue).strip().lower()
    if is_supply_control_application_type_value(app_type):
        return True, "supply_control_issue"

    supply_issue_key = find_supply_issue(issue_key)
    if supply_issue_key and supply_issue_key != issue_key:
        return False, "linked_finance_accounting_issue"

    return True, "source_or_standalone_issue"


def extract_linked_issue_infos(issue_key: str) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    seen = set()

    for link in get_links(issue_key):
        obj = link.get("object") or {}
        linked_key = obj.get("key")
        if linked_key and linked_key not in seen:
            seen.add(linked_key)
            result.append({
                "key": linked_key,
                "direction": link.get("direction"),
                "type": link.get("type") or {},
            })

    return result


def find_supply_issue(issue_key: str) -> Optional[str]:
    current_issue = get_issue(issue_key)
    if is_primary_supply_issue(current_issue):
        return issue_key

    linked_infos = extract_linked_issue_infos(issue_key)

    for preferred_direction in ["inward", None]:
        for item in linked_infos:
            if preferred_direction and item.get("direction") != preferred_direction:
                continue

            linked_key = item["key"]
            try:
                linked_issue = get_issue(linked_key)
                if is_primary_supply_issue(linked_issue):
                    return linked_key
            except Exception as exc:
                log(f"[find_supply_issue] linked lookup error for {linked_key}: {exc}")

    for preferred_direction in ["inward", None]:
        for item in linked_infos:
            if preferred_direction and item.get("direction") != preferred_direction:
                continue

            linked_key = item["key"]
            try:
                linked_issue = get_issue(linked_key)
                if is_supply_issue(linked_issue) or is_initiator_finance_source_issue(linked_issue):
                    return linked_key
            except Exception as exc:
                log(f"[find_supply_issue] linked fallback lookup error for {linked_key}: {exc}")

    if len(linked_infos) == 1:
        return linked_infos[0]["key"]

    return None


def find_linked_issue_by_application_type(issue_key: str, application_type_display: str) -> Optional[str]:
    target = application_type_display.strip().lower()
    if not target:
        return None

    for item in extract_linked_issue_infos(issue_key):
        linked_key = item["key"]
        try:
            linked_issue = get_issue(linked_key)
        except Exception as exc:
            log(f"[find_linked_issue_by_application_type] linked lookup error for {linked_key}: {exc}")
            continue

        if get_application_type_display(linked_issue).strip().lower() == target:
            return linked_key

    return None


def find_linked_issue_by_route_and_block(issue_key: str, route_display: str, functional_block_display: str) -> Optional[str]:
    target_route = route_display.strip().lower()
    target_block = functional_block_display.strip().lower()
    if not target_route or not target_block:
        return None

    for item in extract_linked_issue_infos(issue_key):
        linked_key = item["key"]
        try:
            linked_issue = get_issue(linked_key)
        except Exception as exc:
            log(f"[find_linked_issue_by_route_and_block] linked lookup error for {linked_key}: {exc}")
            continue

        linked_route = get_display(get_custom_field(linked_issue, "route")[1]).strip().lower()
        linked_block = get_functional_block_display(linked_issue).strip().lower()
        linked_status = get_display(linked_issue.get("status")).strip().lower()
        if linked_status == "отменено":
            continue
        if linked_route == target_route and linked_block == target_block:
            return linked_key

    return None


def find_linked_finance_flow_issue(issue_key: str, route_display: str) -> Optional[str]:
    target_route = route_display.strip().lower()
    if not target_route:
        return None

    for item in extract_linked_issue_infos(issue_key):
        linked_key = item["key"]
        try:
            linked_issue = get_issue(linked_key)
        except Exception as exc:
            log(f"[find_linked_finance_flow_issue] linked lookup error for {linked_key}: {exc}")
            continue

        linked_route = get_display(get_custom_field(linked_issue, "route")[1]).strip().lower()
        linked_status = get_display(linked_issue.get("status")).strip().lower()
        linked_block = get_functional_block_display(linked_issue).strip().lower()
        linked_summary = str(linked_issue.get("summary") or "").strip().lower()
        linked_app_type = get_application_type_display(linked_issue).strip().lower()

        if linked_status == "отменено":
            continue
        if linked_route != target_route:
            continue
        if linked_key == issue_key or is_primary_supply_issue(linked_issue):
            continue
        if is_supply_control_application_type_value(linked_app_type):
            continue
        if linked_summary.startswith("согласование оплаты счета") or linked_block in {
            FINANCE_BLOCK.strip().lower(),
            "бухгалтерия",
        }:
            return linked_key

    return None


# ================= MESSAGE BUILDERS =================

def build_context_text(issue: Optional[Dict[str, Any]]) -> str:
    return f"{get_context_label(issue)}:\n{get_context_display(issue) or 'Не заполнен'}"


def pick_context_issue(*issues: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for issue in issues:
        if issue_has_context(issue):
            return issue
    for issue in issues:
        if issue:
            return issue
    return None


def append_context_fields_to_payload(source_issue: Dict[str, Any], payload: Dict[str, Any]) -> None:
    source_object_key, source_object_value = get_object_pair(source_issue)
    object_value = normalize_ref_value(source_object_value)
    if source_object_key and object_value is not None:
        payload[source_object_key] = object_value

    source_initiator_key, source_initiator_value = get_initiator_pair(source_issue)
    initiator_value = normalize_ref_value(source_initiator_value)
    if source_initiator_key and initiator_value is not None:
        payload[source_initiator_key] = initiator_value

    source_outline_key, source_outline_value = get_application_outline_pair(source_issue)
    outline_value = normalize_ref_value(source_outline_value)
    if source_outline_key and outline_value is not None:
        payload[source_outline_key] = outline_value


def build_message_structured(title: str, issue_key: str, summary: str, date_text: str, context_issue: Optional[Dict[str, Any]], application_type_text: str, wiki_issue: Optional[Dict[str, Any]] = None) -> str:
    return (
        f"{title}\n\n"
        f"📌 Задача:\n{issue_key}\n{tracker_display_url(issue_key)}\n\n"
        f"💼 Наименование:\n{summary or '—'}\n\n"
        f"📅 Дата завершения:\n{date_text or '—'}\n\n"
        f"{build_context_text(context_issue)}\n\n"
        f"👉 Тип заявки:\n{application_type_text or 'Не заполнен'}"
        f"{build_wiki_block(wiki_issue)}"
    )


def build_supply_message(issue_key: str, issue: Dict[str, Any], title: str) -> str:
    return build_message_structured(
        title=title,
        issue_key=issue_key,
        summary=issue.get("summary") or "—",
        date_text=get_date_display(issue) or "—",
        context_issue=issue,
        application_type_text=get_application_type_display(issue) or "Не заполнен",
        wiki_issue=issue,
    )


def build_accounting_message(accounting_issue_key: str, accounting_issue: Dict[str, Any], supply_issue_key: Optional[str], supply_issue: Optional[Dict[str, Any]]) -> str:
    summary = accounting_issue.get("summary") or "—"
    date_text = get_date_display(accounting_issue) or get_date_display(supply_issue) or "—"
    context_issue = pick_context_issue(accounting_issue, supply_issue)
    application_type_text = get_application_type_display(accounting_issue) or get_application_type_display(supply_issue) or "Не заполнен"
    supply_comment_block = ""
    if supply_issue_key:
        marker_context = get_latest_marker_comment_context(supply_issue_key, INVOICE_MARKER)
        supply_comment_tail = (marker_context.get("tail_text") or "").strip()
        if supply_comment_tail:
            supply_comment_block = f"\n\n📝 {build_source_comment_label(supply_issue)}:\n{supply_comment_tail}"

    return (
        "📥 Новая задача для отдела бухгалтерии\n\n"
        f"📌 Задача:\n{accounting_issue_key}\n{tracker_display_url(accounting_issue_key)}\n\n"
        f"💼 Наименование:\n{summary}\n\n"
        f"📅 Дата завершения:\n{date_text}\n\n"
        f"{build_context_text(context_issue)}\n\n"
        f"👉 Тип заявки:\n{application_type_text}"
        f"{supply_comment_block}"
        f"{build_wiki_block(pick_context_issue(accounting_issue, supply_issue))}"
    )


def build_approved_invoice_message(
    finance_issue_key: str,
    finance_issue: Dict[str, Any],
    supply_issue_key: Optional[str],
    supply_issue: Optional[Dict[str, Any]],
) -> str:
    summary = finance_issue.get("summary") or "—"
    date_text = get_date_display(finance_issue) or get_date_display(supply_issue) or "—"
    context_issue = pick_context_issue(finance_issue, supply_issue)
    application_type_text = get_application_type_display(finance_issue) or get_application_type_display(supply_issue) or "Не заполнен"

    source_block = ""
    if supply_issue_key:
        source_block = f"\n\n📌 Исходная задача:\n{supply_issue_key}\n{tracker_display_url(supply_issue_key)}"
    supply_comment_block = ""
    if supply_issue_key:
        marker_context = get_latest_marker_comment_context(supply_issue_key, INVOICE_MARKER)
        supply_comment_tail = (marker_context.get("tail_text") or "").strip()
        if supply_comment_tail:
            supply_comment_block = f"\n\n📝 {build_source_comment_label(supply_issue)}:\n{supply_comment_tail}"

    return (
        "✅ Счет согласован\n\n"
        f"📌 Финансовая задача:\n{finance_issue_key}\n{tracker_display_url(finance_issue_key)}\n\n"
        f"💼 Название:\n{summary}\n\n"
        f"📅 Дата завершения:\n{date_text}\n\n"
        f"{build_context_text(context_issue)}\n\n"
        f"👉 Тип заявки:\n{application_type_text}"
        f"{source_block}"
        f"{supply_comment_block}"
        f"{build_wiki_block(pick_context_issue(finance_issue, supply_issue))}"
    )


def build_payment_done_message(supply_issue_key: str, supply_issue: Dict[str, Any]) -> str:
    return build_message_structured(
        title="💸 Оплата проведена",
        issue_key=supply_issue_key,
        summary=supply_issue.get("summary") or "—",
        date_text=get_date_display(supply_issue) or "—",
        context_issue=supply_issue,
        application_type_text=get_application_type_display(supply_issue) or "Не заполнен",
        wiki_issue=supply_issue,
    )


def process_paid_invoice_distribution(
    accounting_issue_key: str,
    accounting_issue: Dict[str, Any],
    supply_issue_key: str,
    supply_issue: Dict[str, Any],
    marker: str,
    *,
    include_payment_status: bool,
    intro_text: Optional[str],
    copy_comment_text: str,
) -> Dict[str, Any]:
    supply_chat_id = resolve_source_chat_id(supply_issue)
    finance_chat_id = resolve_issue_chat_id(accounting_issue, "finance")
    accounting_chat_id = resolve_issue_chat_id(accounting_issue, "accounting")

    marker_context = get_latest_marker_comment_context(accounting_issue_key, marker)
    marker_comment_id = marker_context.get("id")
    marker_attachments = marker_context.get("attachments") or []
    resolved_copy_comment_text = copy_comment_text.replace(
        "{paid_invoice_marker}",
        paid_invoice_marker(accounting_issue_key, marker_comment_id),
    )

    if not marker_comment_id or not marker_attachments:
        return {
            "actions": ["skip_missing_paid_invoice_marker"],
            "paid_invoice_comment_id": marker_comment_id,
            "paid_files_sent": [],
            "paid_file_errors": [],
            "finance_files_sent": [],
            "finance_file_errors": [],
            "accounting_files_sent": [],
            "accounting_file_errors": [],
        }

    if paid_invoice_already_processed(supply_issue_key, accounting_issue_key, marker_comment_id):
        return {
            "actions": ["skip_already_processed_paid_invoice"],
            "already_processed": True,
            "paid_invoice_comment_id": marker_comment_id,
            "paid_files_sent": [],
            "paid_file_errors": [],
            "finance_files_sent": [],
            "finance_file_errors": [],
            "accounting_files_sent": [],
            "accounting_file_errors": [],
        }

    supply_thread_id = get_or_create_issue_thread_id(
        supply_issue_key,
        supply_issue,
        supply_chat_id,
        SUPPLY_THREAD_FIELD,
        lambda: send_text(
            supply_chat_id,
            build_supply_message(supply_issue_key, supply_issue, "📦 Новая заявка"),
            payload_id=f"supply-root::{supply_issue_key}",
        ),
    )

    finance_thread_id = get_or_create_issue_thread_id(
        accounting_issue_key,
        accounting_issue,
        finance_chat_id,
        FINANCE_THREAD_FIELD,
        lambda: send_text(
            finance_chat_id,
            build_finance_message(accounting_issue_key, accounting_issue, supply_issue_key, supply_issue),
            payload_id=f"finance-root::{accounting_issue_key}",
        ),
    )

    accounting_thread_id = get_or_create_issue_thread_id(
        accounting_issue_key,
        accounting_issue,
        accounting_chat_id,
        ACCOUNTING_THREAD_FIELD,
        lambda: send_text(
            accounting_chat_id,
            build_accounting_message(accounting_issue_key, accounting_issue, supply_issue_key, supply_issue),
            payload_id=f"accounting-root::{accounting_issue_key}",
        ),
    )

    if include_payment_status:
        add_comment_once(supply_issue_key, "💸 Оплата произведена")
        ensure_wiki_comment(supply_issue_key, supply_issue)

        send_text(
            supply_chat_id,
            build_minimal_stage_message("💸 Оплата произведена"),
            thread_id=supply_thread_id,
            payload_id=f"stage::{accounting_issue_key}::payment_done::supply",
        )
        send_text(
            finance_chat_id,
            build_minimal_stage_message("💸 Оплата произведена"),
            thread_id=finance_thread_id,
            payload_id=f"stage::{accounting_issue_key}::payment_done::finance",
        )
        send_text(
            accounting_chat_id,
            build_minimal_stage_message("💸 Оплата произведена"),
            thread_id=accounting_thread_id,
            payload_id=f"stage::{accounting_issue_key}::payment_done::accounting",
        )

    paid_files_sent, paid_file_errors = send_marker_comment_files(
        accounting_issue_key,
        marker,
        chat_id=supply_chat_id,
        thread_id=supply_thread_id,
        intro_text=intro_text,
        copy_to_issue_key=supply_issue_key,
        copy_comment_text=resolved_copy_comment_text,
        copy_skip_if_issue_has_filename=False,
    )

    finance_files_sent, finance_file_errors = send_marker_comment_files(
        accounting_issue_key,
        marker,
        chat_id=finance_chat_id,
        thread_id=finance_thread_id,
        intro_text=intro_text,
        already_sent_names=[],
    )

    accounting_files_sent, accounting_file_errors = send_marker_comment_files(
        accounting_issue_key,
        marker,
        chat_id=accounting_chat_id,
        thread_id=accounting_thread_id,
        intro_text=intro_text,
        already_sent_names=[],
    )

    return {
        "actions": [
            "messenger_to_supply",
            "messenger_to_finance",
            "messenger_to_accounting",
            "copy_paid_invoice_to_supply",
        ],
        "paid_invoice_comment_id": marker_comment_id,
        "paid_files_sent": paid_files_sent,
        "paid_file_errors": paid_file_errors,
        "finance_files_sent": finance_files_sent,
        "finance_file_errors": finance_file_errors,
        "accounting_files_sent": accounting_files_sent,
        "accounting_file_errors": accounting_file_errors,
    }


def build_minimal_stage_message(title: str) -> str:
    return title


def build_finance_message(finance_issue_key: str, finance_issue: Dict[str, Any], supply_issue_key: str, supply_issue: Dict[str, Any]) -> str:
    context_issue = pick_context_issue(finance_issue, supply_issue)
    application_type_display = get_application_type_display(finance_issue) or get_application_type_display(supply_issue) or "Не заполнен"
    date_display = get_date_display(finance_issue) or get_date_display(supply_issue) or "— не указана —"
    source_summary = supply_issue.get("summary") or "—"
    marker_context = get_latest_marker_comment_context(supply_issue_key, INVOICE_MARKER)
    supply_comment_tail = (marker_context.get("tail_text") or "").strip()
    supply_comment_block = ""
    if supply_comment_tail:
        supply_comment_block = f"\n\n📝 {build_source_comment_label(supply_issue)}:\n{supply_comment_tail}"

    return (
        "💰 Согласование оплаты счета\n\n"
        f"📌 Финансовая задача:\n{finance_issue_key}\n{tracker_display_url(finance_issue_key)}\n\n"
        f"📌 Исходная задача:\n{supply_issue_key}\n{tracker_display_url(supply_issue_key)}\n\n"
        f"💼 Название:\n{finance_issue.get('summary') or '—'}\n\n"
        f"📦 Наименование исходной задачи:\n{source_summary}\n\n"
        f"📅 Дата завершения:\n{date_display}\n\n"
        f"{build_context_text(context_issue)}\n\n"
        f"👉 Тип заявки:\n{application_type_display}"
        f"{supply_comment_block}"
        f"{build_wiki_block(supply_issue)}"
    )


def normalize_status_text(value: Any) -> str:
    return get_display(value).strip().lower()


def notification_class_for_status(status_value: Any) -> Optional[str]:
    normalized = normalize_status_text(status_value)
    if not normalized:
        return None

    if normalized == "беклог":
        return "created"
    if normalized in {"в работе", "ревью", "требуется информация"}:
        return "in_progress"
    if normalized == "готово":
        return "done"
    if normalized == "отменено":
        return "cancelled"
    return None


def notification_title_for_class(notification_class: Optional[str]) -> Optional[str]:
    titles = {
        "created": "✅ Задача создана успешно",
        "in_progress": "🛠 Задача в работе",
        "done": "✅ Задача закрыта успешно",
        "cancelled": "❌ Задача отменена",
    }
    return titles.get(notification_class)


def build_project_notification_message(issue_key: str, issue: Dict[str, Any], title: str) -> str:
    return (
        f"{title}\n\n"
        f"📌 Задача:\n{issue_key}\n{tracker_display_url(issue_key)}\n\n"
        f"💼 Наименование:\n{issue.get('summary') or '—'}\n\n"
        f"{build_context_text(issue)}\n\n"
        f"👉 Тип заявки:\n{get_application_type_display(issue) or 'Не заполнен'}"
        f"{build_wiki_block(issue)}"
    )


def build_project_stage_message(status_value: Any) -> str:
    notification_class = notification_class_for_status(status_value)
    mapping = {
        "created": "✅ Задача создана успешно",
        "in_progress": "🛠️ Задача в работе",
        "done": "✅ Задача закрыта успешно",
        "cancelled": "❌ Задача отменена",
    }
    if notification_class in mapping:
        return mapping[notification_class]
    return get_display(status_value) or "Обновление статуса"


def supply_control_notification_meta_for_status(status_value: Any) -> Optional[Dict[str, str]]:
    normalized = normalize_status_text(status_value)
    if not normalized:
        return None

    mapping = {
        "беклог": {
            "notification_class": "created",
            "title": "🚚 Контроль поставки создан",
        },
        "в работе": {
            "notification_class": "in_progress",
            "title": "🛠 Контроль поставки в работе",
        },
        "ревью": {
            "notification_class": "review",
            "title": "🔎 Контроль поставки на ревью",
        },
        "требуется информация": {
            "notification_class": "needs_info",
            "title": "❓ По задаче требуется информация",
        },
        "готово": {
            "notification_class": "done",
            "title": "✅ Контроль поставки завершен",
        },
        "отменено": {
            "notification_class": "cancelled",
            "title": "❌ Контроль поставки отменен",
        },
    }
    return mapping.get(normalized)


def build_supply_control_message(
    issue_key: str,
    issue: Dict[str, Any],
    title: str,
    current_status: Any = None,
    source_issue_key: Optional[str] = None,
) -> str:
    source_block = ""
    if source_issue_key:
        source_block = (
            f"📌 Исходная задача:\n{source_issue_key}\n"
            f"{tracker_display_url(source_issue_key)}"
        )

    parts = [
        title,
        f"📌 Задача:\n{issue_key}\n{tracker_display_url(issue_key)}",
        f"💼 Наименование:\n{issue.get('summary') or '—'}",
    ]
    if source_block:
        parts.append(source_block)
    parts.append(build_context_text(issue))
    parts.append(f"👉 Тип заявки:\n{get_application_type_display(issue) or 'Не заполнен'}{build_wiki_block(issue)}")
    return "\n\n".join(parts)


def build_supply_control_stage_message(status_value: Any) -> str:
    normalized = normalize_status_text(status_value)
    mapping = {
        "в работе": "🛠️ В работе",
        "требуется информация": "❓ Требуется информация",
        "ревью": "🔎 Ревью",
        "готово": "✅ Готово",
        "отменено": "❌ Отменено",
        "беклог": "📦 Создана задача",
    }
    return mapping.get(normalized, get_display(status_value) or "Обновление статуса")


def build_supply_control_accounting_message(
    issue_key: str,
    issue: Dict[str, Any],
    source_issue_key: Optional[str] = None,
) -> str:
    source_block = ""
    if source_issue_key:
        source_block = (
            f"\n\n📌 Исходная задача:\n{source_issue_key}\n"
            f"{tracker_display_url(source_issue_key)}"
        )

    return (
        "📥 Контроль поставки передан в бухгалтерию\n\n"
        f"📌 Задача:\n{issue_key}\n{tracker_display_url(issue_key)}\n\n"
        f"💼 Наименование:\n{issue.get('summary') or '—'}"
        f"{source_block}\n\n"
        f"{build_context_text(issue)}\n\n"
        f"👉 Тип заявки:\n{get_application_type_display(issue) or 'Не заполнен'}"
        f"{build_wiki_block(issue)}"
    )


def find_related_issue_by_route(issue_key: str, route_display: str) -> Optional[str]:
    normalized_target = route_display.strip().lower()
    if not normalized_target:
        return None

    for item in extract_linked_issue_infos(issue_key):
        linked_key = item["key"]
        try:
            linked_issue = get_issue(linked_key)
        except Exception as exc:
            log(f"[find_related_issue_by_route] linked lookup error for {linked_key}: {exc}")
            continue

        linked_route = get_display(get_custom_field(linked_issue, "route")[1]).strip().lower()
        if linked_route == normalized_target:
            return linked_key

    return None


def send_supply_control_notification(issue_key: str, issue: Dict[str, Any], status_display: Any, previous_status: Any = None) -> Dict[str, Any]:
    accounting_chat_id = resolve_issue_chat_id(issue, "accounting")

    source_issue_key = find_supply_issue(issue_key)
    if not source_issue_key:
        source_issue_key = find_related_issue_by_route(issue_key, "Снабжение -> Финансы -> Бухгалтерия")
    if not source_issue_key:
        source_issue_key = issue_key
    source_issue = get_issue(source_issue_key) if source_issue_key != issue_key else issue
    supply_chat_id = resolve_source_chat_id(source_issue) or resolve_source_chat_id(issue)

    if not supply_chat_id:
        raise ValueError("source department chat is not configured")

    current_meta = supply_control_notification_meta_for_status(status_display)
    if not current_meta:
        return {
            "sent": False,
            "reason": "status_not_mapped",
            "status_display": get_display(status_display),
            "previous_status": get_display(previous_status),
            "source_issue_key": source_issue_key,
        }

    if should_suppress_initiator_supply_control_start_notification(issue, status_display):
        return {
            "sent": False,
            "reason": "initiator_supply_control_start_is_silent",
            "status_display": get_display(status_display),
            "previous_status": get_display(previous_status),
            "source_issue_key": source_issue_key,
        }

    message_text = build_supply_control_message(
        issue_key,
        issue,
        current_meta["title"],
        current_status=status_display,
        source_issue_key=source_issue_key,
    )
    routing = resolve_project_notifications_chat(issue)
    deliveries: List[Dict[str, Any]] = []
    object_chat_id = (routing.get("chat_id") or "").strip()
    object_saved_chat_id = get_issue_string_field(issue, SUPPLY_CONTROL_OBJECT_CHAT_FIELD)
    object_existing_thread_id = get_issue_thread_id(issue, SUPPLY_CONTROL_OBJECT_THREAD_FIELD)
    object_thread_reusable = bool(
        object_chat_id and object_existing_thread_id and object_saved_chat_id == object_chat_id
    )
    object_chat_same_as_supply = bool(object_chat_id and object_chat_id == supply_chat_id)
    payload_suffix = current_meta["notification_class"]
    object_notification_class = notification_class_for_status(status_display)
    object_notification_title = notification_title_for_class(object_notification_class)
    object_delivery_mode = "root" if object_notification_class == "created" else "reply"
    object_message_text = ""
    if object_notification_class and object_notification_title:
        object_message_text = build_project_notification_message(issue_key, issue, object_notification_title)

    normalized_status = normalize_status_text(status_display)
    supply_thread_id: Optional[int] = None
    if normalized_status == "беклог":
        root_payload_id = f"supply-control::{issue_key}::{payload_suffix}::supply_root_v2"
        log(
            "[supply-control-root] "
            f"issue={issue_key}, payload_id={root_payload_id}, "
            f"title={current_meta['title']}, preview={message_text[:240]!r}"
        )
        supply_response = send_text(
            supply_chat_id,
            message_text,
            payload_id=root_payload_id,
        )
        supply_thread_id = normalize_thread_id(supply_response.get("message_id"))
        if supply_thread_id is None:
            raise ValueError(f"supply root message_id is missing for {issue_key}")
        save_issue_thread_id(issue_key, SUPPLY_THREAD_FIELD, supply_thread_id, issue, chat_id=supply_chat_id)
        deliveries.append({
            "target": "supply_department",
            "chat_id": supply_chat_id,
            "routing_source": "static_supply_chat",
            "message_id": supply_thread_id,
            "mode": "root",
            "thread_reused": False,
        })
        issue_files_sent, issue_file_errors = send_issue_files(
            supply_chat_id,
            issue_key,
            issue,
            thread_id=supply_thread_id,
            intro_text="📎 Файл из описания задачи",
        )
        deliveries.append({
            "target": "supply_department_files",
            "chat_id": supply_chat_id,
            "routing_source": "static_supply_chat",
            "message_id": supply_thread_id,
            "mode": "thread_files",
            "thread_reused": True,
            "issue_files_sent": issue_files_sent,
            "issue_file_errors": issue_file_errors,
        })
    else:
        supply_thread_id = get_or_create_issue_thread_id(
            issue_key,
            issue,
            supply_chat_id,
            SUPPLY_THREAD_FIELD,
            lambda: send_text(
                supply_chat_id,
                build_supply_control_message(
                    issue_key,
                    issue,
                    "🚚 Контроль поставки создан",
                    current_status={"display": "Беклог"},
                    source_issue_key=source_issue_key,
                ),
                payload_id=f"supply-control::{issue_key}::created::supply_root_recovery",
            ),
        )
        send_text(
            supply_chat_id,
            build_supply_control_stage_message(status_display),
            thread_id=supply_thread_id,
            payload_id=f"supply-control::{issue_key}::{payload_suffix}::supply_reply",
        )
        deliveries.append({
            "target": "supply_department",
            "chat_id": supply_chat_id,
            "routing_source": "static_supply_chat",
            "message_id": supply_thread_id,
            "mode": "reply",
            "thread_reused": True,
        })
        if normalized_status == "ревью":
            closing_docs_sent, closing_docs_errors = send_marker_comment_files(
                issue_key,
                CLOSING_DOCS_MARKER,
                chat_id=supply_chat_id,
                thread_id=supply_thread_id,
                intro_text="📎 Закрывающие документы",
            )
            deliveries.append({
                "target": "supply_department_files",
                "chat_id": supply_chat_id,
                "routing_source": "static_supply_chat",
                "message_id": supply_thread_id,
                "mode": "thread_files",
                "thread_reused": True,
                "closing_docs_marker": CLOSING_DOCS_MARKER,
                "closing_docs_sent": closing_docs_sent,
                "closing_docs_errors": closing_docs_errors,
            })

    if object_chat_same_as_supply:
        thread_id = supply_thread_id
        if not object_notification_class or not object_notification_title:
            deliveries.append({
                "target": "project_object_chat",
                "chat_id": supply_chat_id,
                "routing_source": "shared_chat",
                "mode": "skipped",
                "reason": "status_not_mapped_for_project_chat",
            })
        elif object_notification_class == "created":
            save_chat_thread_state(
                issue_key,
                issue,
                chat_field=SUPPLY_CONTROL_OBJECT_CHAT_FIELD,
                thread_field=SUPPLY_CONTROL_OBJECT_THREAD_FIELD,
                chat_id=supply_chat_id,
                thread_id=thread_id,
            )
            deliveries.append({
                "target": "supply_department+project_object_chat",
                "chat_id": supply_chat_id,
                "routing_source": "shared_chat",
                "message_id": thread_id,
                "mode": "root",
                "thread_reused": False,
            })
        elif object_thread_reusable:
            send_text(
                supply_chat_id,
                object_message_text,
                thread_id=object_existing_thread_id,
                payload_id=f"supply-control::{issue_key}::{object_notification_class}::shared_reply",
            )
            deliveries.append({
                "target": "supply_department+project_object_chat",
                "chat_id": supply_chat_id,
                "routing_source": "shared_chat",
                "message_id": object_existing_thread_id,
                "mode": "reply",
                "thread_reused": True,
            })
        else:
            supply_response = send_text(
                supply_chat_id,
                message_text,
                payload_id=f"supply-control::{issue_key}::{payload_suffix}::supply_department_fallback",
            )
            deliveries.append({
                "target": "supply_department",
                "chat_id": supply_chat_id,
                "routing_source": "shared_chat_supply_fallback",
                "message_id": normalize_thread_id(supply_response.get("message_id")),
                "mode": "standalone",
                "thread_reused": False,
            })
            deliveries.append({
                "target": "project_object_chat",
                "chat_id": supply_chat_id,
                "routing_source": "shared_chat",
                "mode": "skipped",
                "reason": "missing_object_thread",
            })
    else:
        if not object_chat_id:
            deliveries.append({
                "target": "project_object_chat",
                "chat_id": "",
                "routing_source": routing.get("source") or "unknown",
                "mode": "skipped",
                "reason": "missing_object_chat",
            })
        elif not object_notification_class or not object_notification_title:
            deliveries.append({
                "target": "project_object_chat",
                "chat_id": object_chat_id,
                "routing_source": routing.get("source") or "unknown",
                "mode": "skipped",
                "reason": "status_not_mapped_for_project_chat",
            })
        elif object_notification_class == "created":
            response = send_text(
                object_chat_id,
                object_message_text,
                payload_id=f"supply-control::{issue_key}::{object_notification_class}::project_object_chat_root",
            )
            object_thread_id = normalize_thread_id(response.get("message_id"))
            if object_thread_id is None:
                raise ValueError(f"root message_id is missing for object chat in {issue_key}")
            save_chat_thread_state(
                issue_key,
                issue,
                chat_field=SUPPLY_CONTROL_OBJECT_CHAT_FIELD,
                thread_field=SUPPLY_CONTROL_OBJECT_THREAD_FIELD,
                chat_id=object_chat_id,
                thread_id=object_thread_id,
            )
            deliveries.append({
                "target": "project_object_chat",
                "chat_id": object_chat_id,
                "routing_source": routing.get("source") or "unknown",
                "message_id": object_thread_id,
                "mode": "root",
                "thread_reused": False,
            })
        elif object_thread_reusable:
            deliveries.append({
                "target": "project_object_chat",
                "chat_id": object_chat_id,
                "routing_source": routing.get("source") or "unknown",
                "message_id": object_existing_thread_id,
                "mode": "skipped",
                "thread_reused": True,
                "reason": "project_status_endpoint_owns_replies",
            })
        else:
            skip_reason = "missing_object_thread"
            if object_existing_thread_id and not object_saved_chat_id:
                skip_reason = "missing_saved_object_chat_id"
            elif object_existing_thread_id and object_saved_chat_id and object_saved_chat_id != object_chat_id:
                skip_reason = "object_chat_changed"

            deliveries.append({
                "target": "project_object_chat",
                "chat_id": object_chat_id,
                "routing_source": routing.get("source") or "unknown",
                "mode": "skipped",
                "reason": skip_reason,
            })

    accounting_delivery: Optional[Dict[str, Any]] = None
    if normalized_status in {"ревью", "готово", "отменено"} and accounting_chat_id:
        accounting_thread_id = get_or_create_issue_thread_id(
            issue_key,
            issue,
            accounting_chat_id,
            ACCOUNTING_THREAD_FIELD,
            lambda: send_text(
                accounting_chat_id,
                build_supply_control_accounting_message(issue_key, issue, source_issue_key=source_issue_key),
                payload_id=f"supply-control::{issue_key}::accounting_root",
            ),
        )

        stage_title_map = {
            "готово": "✅ Готово",
            "отменено": "❌ Отменено",
        }
        if normalized_status in stage_title_map:
            send_text(
                accounting_chat_id,
                stage_title_map[normalized_status],
                thread_id=accounting_thread_id,
                payload_id=f"supply-control::{issue_key}::{payload_suffix}::accounting_reply",
            )

        closing_docs_sent: List[str] = []
        closing_docs_errors: List[str] = []
        if normalized_status == "ревью":
            closing_docs_sent, closing_docs_errors = send_marker_comment_files(
                issue_key,
                CLOSING_DOCS_MARKER,
                accounting_chat_id,
                thread_id=accounting_thread_id,
                intro_text="📎 Закрывающие документы по поставке",
            )

        accounting_delivery = {
            "target": "accounting_department",
            "chat_id": accounting_chat_id,
            "routing_source": "static_accounting_chat",
            "message_id": accounting_thread_id,
            "mode": "reply",
            "thread_reused": normalized_status != "ревью",
            "closing_docs_marker": CLOSING_DOCS_MARKER if normalized_status == "ревью" else "",
            "closing_docs_sent": closing_docs_sent,
            "closing_docs_errors": closing_docs_errors,
        }
        deliveries.append(accounting_delivery)

    return {
        "sent": any(item.get("mode") != "skipped" for item in deliveries),
        "mode": "fanout",
        "status_display": get_display(status_display),
        "previous_status": get_display(previous_status),
        "source_issue_key": source_issue_key,
        "notification_class": current_meta["notification_class"],
        "thread_persistence": True,
        "delivery_count": len(deliveries),
        "deliveries": deliveries,
        "resolved_object": routing.get("object_name") or "",
        "object_chat_id": object_chat_id,
        "object_saved_chat_id": object_saved_chat_id,
        "object_thread_id": object_existing_thread_id,
        "object_delivery_mode": object_delivery_mode,
    }


def ensure_supply_control_supply_root(issue_key: str, issue: Dict[str, Any], source_issue_key: Optional[str] = None) -> Dict[str, Any]:
    source_issue = get_issue(source_issue_key) if source_issue_key and source_issue_key != issue_key else issue
    supply_chat_id = resolve_source_chat_id(source_issue) or resolve_source_chat_id(issue)
    existing_thread_id = get_issue_thread_id(issue, SUPPLY_THREAD_FIELD)
    if existing_thread_id:
        return {
            "sent": False,
            "mode": "already_exists",
            "issue_key": issue_key,
            "thread_id": existing_thread_id,
        }

    ensure_wiki_comment(issue_key, issue)
    message_text = build_supply_control_message(
        issue_key,
        issue,
        "🚚 Контроль поставки создан",
        current_status={"display": "Беклог"},
        source_issue_key=source_issue_key or issue_key,
    )
    response = send_text(
        supply_chat_id,
        message_text,
        payload_id=f"supply-control::{issue_key}::created::bridge_supply_root",
    )
    thread_id = normalize_thread_id(response.get("message_id"))
    if thread_id is None:
        raise ValueError(f"supply root message_id is missing for {issue_key}")

    save_issue_thread_id(issue_key, SUPPLY_THREAD_FIELD, thread_id, issue, chat_id=supply_chat_id)
    issue_files_sent, issue_file_errors = send_issue_files(
        supply_chat_id,
        issue_key,
        issue,
        thread_id=thread_id,
        intro_text="📎 Файл из описания задачи",
    )
    return {
        "sent": True,
        "mode": "created",
        "issue_key": issue_key,
        "thread_id": thread_id,
        "issue_files_sent": issue_files_sent,
        "issue_file_errors": issue_file_errors,
    }


def send_project_status_notification(issue_key: str, issue: Dict[str, Any], previous_status: Any = None, current_status: Any = None) -> Dict[str, Any]:
    routing = resolve_project_notifications_chat(issue)
    resolved_chat_id = routing.get("chat_id") or ""
    if not resolved_chat_id:
        raise ValueError("PROJECT_NOTIFICATIONS_CHAT_ID is not configured")
    if not PROJECT_NOTIFICATIONS_THREAD_FIELD:
        raise ValueError("PROJECT_NOTIFICATIONS_THREAD_FIELD is not configured")
    if not PROJECT_NOTIFICATIONS_CHAT_FIELD:
        raise ValueError("PROJECT_NOTIFICATIONS_CHAT_FIELD is not configured")

    current_status_value = current_status if current_status is not None else issue.get("status")
    current_class = notification_class_for_status(current_status_value)
    current_title = notification_title_for_class(current_class)
    saved_chat_id = get_issue_string_field(issue, PROJECT_NOTIFICATIONS_CHAT_FIELD)
    existing_thread_id = get_issue_thread_id(issue, PROJECT_NOTIFICATIONS_THREAD_FIELD)
    state_source = "tracker_fields"
    if not saved_chat_id or not existing_thread_id:
        fallback_state = get_project_thread_state(issue_key)
        fallback_chat_id = fallback_state.get("chat_id") or ""
        fallback_thread_id = normalize_thread_id(fallback_state.get("thread_id"))
        if not saved_chat_id and fallback_chat_id:
            saved_chat_id = fallback_chat_id
            state_source = "server_state"
        if not existing_thread_id and fallback_thread_id:
            existing_thread_id = fallback_thread_id
            state_source = "server_state"
    thread_can_be_reused = bool(existing_thread_id and saved_chat_id and saved_chat_id == resolved_chat_id)

    if not current_class or not current_title:
        return {
            "sent": False,
            "reason": "status_not_mapped",
            "current_status": get_display(current_status_value),
            "previous_status": get_display(previous_status),
            "previous_notification_class": notification_class_for_status(previous_status),
            "current_notification_class": current_class,
            "resolved_object": routing.get("object_name") or "",
            "resolved_chat_id": resolved_chat_id,
            "saved_chat_id": saved_chat_id,
            "routing_source": routing.get("source") or "unknown",
            "thread_reused": False,
            "state_source": state_source,
        }

    previous_class = notification_class_for_status(previous_status)
    if previous_status is not None and previous_class == current_class:
        return {
            "sent": False,
            "reason": "same_notification_class",
            "previous_status": get_display(previous_status),
            "current_status": get_display(current_status_value),
            "previous_notification_class": previous_class,
            "current_notification_class": current_class,
            "resolved_object": routing.get("object_name") or "",
            "resolved_chat_id": resolved_chat_id,
            "saved_chat_id": saved_chat_id,
            "routing_source": routing.get("source") or "unknown",
            "thread_reused": False,
            "state_source": state_source,
        }

    payload_suffix = current_class

    if not thread_can_be_reused:
        thread_id = normalize_thread_id(
            send_text(
                resolved_chat_id,
                build_project_notification_message(issue_key, issue, current_title),
                payload_id=f"project-root::{issue_key}::{payload_suffix}",
            ).get("message_id")
        )
        if thread_id is None:
            raise ValueError(f"root message_id is missing for {issue_key} in {resolved_chat_id}")
        save_project_notification_thread_state(issue_key, issue, resolved_chat_id, thread_id)

        thread_mode_reason = "missing_thread"
        if existing_thread_id and not saved_chat_id:
            thread_mode_reason = "missing_saved_chat_id"
        elif existing_thread_id and saved_chat_id and saved_chat_id != resolved_chat_id:
            thread_mode_reason = "chat_changed"

        return {
            "sent": True,
            "mode": "root",
            "thread_id": thread_id,
            "previous_status": get_display(previous_status),
            "current_status": get_display(current_status_value),
            "previous_notification_class": previous_class,
            "current_notification_class": current_class,
            "resolved_object": routing.get("object_name") or "",
            "resolved_chat_id": resolved_chat_id,
            "saved_chat_id": saved_chat_id,
            "routing_source": routing.get("source") or "unknown",
            "thread_reused": False,
            "thread_mode_reason": thread_mode_reason,
            "state_source": state_source,
        }

    if current_class == "created":
        return {
            "sent": False,
            "reason": "skip_created_reply",
            "mode": "reply_skipped",
            "thread_id": existing_thread_id,
            "previous_status": get_display(previous_status),
            "current_status": get_display(current_status_value),
            "previous_notification_class": previous_class,
            "current_notification_class": current_class,
            "resolved_object": routing.get("object_name") or "",
            "resolved_chat_id": resolved_chat_id,
            "saved_chat_id": saved_chat_id,
            "routing_source": routing.get("source") or "unknown",
            "thread_reused": True,
            "thread_mode_reason": "created_reply_disabled",
            "state_source": state_source,
        }

    send_text(
        resolved_chat_id,
        build_project_stage_message(current_status_value),
        thread_id=existing_thread_id,
        payload_id=f"project-event::{issue_key}::{payload_suffix}",
    )
    return {
        "sent": True,
        "mode": "reply",
        "thread_id": existing_thread_id,
        "previous_status": get_display(previous_status),
        "current_status": get_display(current_status_value),
        "previous_notification_class": previous_class,
        "current_notification_class": current_class,
        "resolved_object": routing.get("object_name") or "",
        "resolved_chat_id": resolved_chat_id,
        "saved_chat_id": saved_chat_id,
        "routing_source": routing.get("source") or "unknown",
        "thread_reused": True,
        "thread_mode_reason": "reuse_existing_thread",
        "state_source": state_source,
    }


# ================= SYNC =================

def sync_fields_from_supply_to_issue(target_issue_key: str) -> Dict[str, Any]:
    supply_key = find_supply_issue(target_issue_key)
    if not supply_key:
        raise ValueError("linked supply issue not found")

    supply_issue = get_issue(supply_key)
    payload: Dict[str, Any] = {}

    source_date_key, source_date_value = get_date_pair(supply_issue)
    if source_date_key and source_date_value:
        payload[source_date_key] = source_date_value

    append_context_fields_to_payload(supply_issue, payload)

    if not payload:
        raise ValueError("no fields to sync from supply issue")

    update_issue(target_issue_key, payload)

    return {
        "target_issue": target_issue_key,
        "source_issue": supply_key,
        "payload_keys": list(payload.keys()),
    }


def create_delivery_control_task_from_issue(trigger_issue_key: str) -> Dict[str, Any]:
    trigger_issue = get_issue(trigger_issue_key)
    if is_supply_issue(trigger_issue):
        source_issue_key = trigger_issue_key
        source_issue = trigger_issue
    else:
        source_issue_key = find_supply_issue(trigger_issue_key)
        if not source_issue_key:
            raise ValueError("linked supply issue not found")
        source_issue = get_issue(source_issue_key)

    supply_control_profile = get_supply_control_profile(source_issue)
    target_control_app_type = supply_control_profile["application_type"]
    target_control_route = supply_control_profile["route"]
    target_control_block = supply_control_profile["functional_block"]

    existing_control_key = find_linked_issue_by_application_type(source_issue_key, target_control_app_type)
    if existing_control_key:
        existing_control_issue = get_issue(existing_control_key)
        bridge_supply_root = ensure_supply_control_supply_root(
            existing_control_key,
            existing_control_issue,
            source_issue_key=source_issue_key,
        )
        flag_payload: Dict[str, Any] = {}
        set_issue_field_if_present(source_issue, flag_payload, DELIVERY_CONTROL_CREATED_FIELD, "Да")
        if flag_payload:
            update_issue(source_issue_key, flag_payload)
        return {
            "ok": True,
            "mode": "already_exists",
            "trigger_issue_key": trigger_issue_key,
            "source_issue_key": source_issue_key,
            "delivery_control_issue_key": existing_control_key,
            "flag_payload_keys": list(flag_payload.keys()),
            "bridge_supply_root": bridge_supply_root,
        }

    created_flag = get_issue_string_field(source_issue, DELIVERY_CONTROL_CREATED_FIELD).strip().lower()
    if created_flag == "да":
        return {
            "ok": True,
            "mode": "already_flagged",
            "trigger_issue_key": trigger_issue_key,
            "source_issue_key": source_issue_key,
            "delivery_control_issue_key": "",
        }

    queue_key = ((source_issue.get("queue") or {}).get("key") or "").strip()
    if not queue_key:
        raise ValueError("queue key is missing on source issue")

    summary = source_issue.get("summary") or trigger_issue.get("summary") or ""
    new_summary = f"Контроль поставки - {summary}".strip(" -")

    payload: Dict[str, Any] = {
        "queue": queue_key,
        "summary": new_summary,
        "type": "task",
        "priority": "normal",
        "description": (
            f"Задача создана автоматически из процесса «{get_application_type_display(source_issue) or 'Закупка материалов'}».\n\n"
            f"Исходная задача:\n{source_issue_key}\n\n"
            "Проверьте связанную задачу и продолжите работу по процессу контроля поставки."
        ),
    }

    application_type_key = resolve_issue_field_key(source_issue, APPLICATION_TYPE_SUFFIX)
    if application_type_key:
        payload[application_type_key] = target_control_app_type

    route_key = resolve_issue_field_key(source_issue, "route")
    if route_key:
        payload[route_key] = target_control_route

    functional_block_key, functional_block_value = get_functional_block_pair(source_issue)
    if functional_block_key:
        payload[functional_block_key] = target_control_block

    append_context_fields_to_payload(source_issue, payload)

    source_date_key, source_date_value = get_date_pair(source_issue)
    if source_date_key and source_date_value:
        payload[source_date_key] = source_date_value

    created_issue = create_issue(payload)
    created_issue_key = created_issue.get("key")
    if not created_issue_key:
        raise ValueError("created delivery control issue key is missing")

    create_issue_link(source_issue_key, created_issue_key)
    route_value = get_display(get_custom_field(source_issue, "route")[1]).strip() or "Снабжение → Финансы → Бухгалтерия"
    finance_issue_key = find_linked_finance_flow_issue(source_issue_key, route_value)
    if finance_issue_key and finance_issue_key != created_issue_key:
        create_issue_link(finance_issue_key, created_issue_key)
    created_issue = get_issue(created_issue_key)
    bridge_supply_root = ensure_supply_control_supply_root(
        created_issue_key,
        created_issue,
        source_issue_key=source_issue_key,
    )

    flag_payload: Dict[str, Any] = {}
    set_issue_field_if_present(source_issue, flag_payload, DELIVERY_CONTROL_CREATED_FIELD, "Да")
    if flag_payload:
        update_issue(source_issue_key, flag_payload)

    return {
        "ok": True,
        "mode": "created",
        "trigger_issue_key": trigger_issue_key,
        "source_issue_key": source_issue_key,
        "finance_issue_key": finance_issue_key or "",
        "delivery_control_issue_key": created_issue_key,
        "created_payload_keys": list(payload.keys()),
        "flag_payload_keys": list(flag_payload.keys()),
        "bridge_supply_root": bridge_supply_root,
    }


def create_finance_task_from_supply_issue(trigger_issue_key: str) -> Dict[str, Any]:
    trigger_issue = get_issue(trigger_issue_key)
    if is_supply_issue(trigger_issue):
        source_issue_key = trigger_issue_key
        source_issue = trigger_issue
    else:
        source_issue_key = find_supply_issue(trigger_issue_key)
        if not source_issue_key:
            raise ValueError("linked supply issue not found")
        source_issue = get_issue(source_issue_key)

    route_value = get_display(get_custom_field(source_issue, "route")[1]).strip() or "Снабжение → Финансы → Бухгалтерия"
    existing_finance_key = find_linked_issue_by_route_and_block(source_issue_key, route_value, FINANCE_BLOCK)
    if existing_finance_key:
        flag_payload: Dict[str, Any] = {}
        set_issue_field_if_present(source_issue, flag_payload, "aFinancialIssueHasBeenCreated", "Да")
        if flag_payload:
            update_issue(source_issue_key, flag_payload)
        return {
            "ok": True,
            "mode": "already_exists",
            "trigger_issue_key": trigger_issue_key,
            "source_issue_key": source_issue_key,
            "finance_issue_key": existing_finance_key,
            "flag_payload_keys": list(flag_payload.keys()),
        }

    created_flag = get_issue_string_field(source_issue, "aFinancialIssueHasBeenCreated").strip().lower()
    if created_flag == "да":
        return {
            "ok": True,
            "mode": "already_flagged",
            "trigger_issue_key": trigger_issue_key,
            "source_issue_key": source_issue_key,
            "finance_issue_key": "",
        }

    queue_key = ((source_issue.get("queue") or {}).get("key") or "").strip()
    if not queue_key:
        raise ValueError("queue key is missing on source issue")

    summary = source_issue.get("summary") or trigger_issue.get("summary") or ""
    marker_context = get_latest_marker_comment_context(source_issue_key, INVOICE_MARKER)
    supply_comment_tail = (marker_context.get("tail_text") or "").strip()
    new_summary = f"Согласование оплаты счета - {summary}".strip(" -")
    source_process_name = get_application_type_display(source_issue) or "Закупка материалов"
    source_comment_label = build_source_comment_label(source_issue)
    description_suffix = ""
    if supply_comment_tail:
        description_suffix = f"\n\n{source_comment_label}:\n{supply_comment_tail}"

    payload: Dict[str, Any] = {
        "queue": queue_key,
        "summary": new_summary,
        "type": "task",
        "priority": "normal",
        "description": (
            f"Задача создана автоматически из процесса «{source_process_name}».\n\n"
            f"Исходная задача:\n{source_issue_key}\n\n"
            "Проверьте связанную задачу и продолжите работу по процессу согласования оплаты счета."
            f"{description_suffix}"
        ),
    }

    application_type_key, application_type_value = get_application_type_pair(source_issue)
    application_type_display = get_display(application_type_value)
    if application_type_key and application_type_display:
        payload[application_type_key] = application_type_display

    route_key = resolve_issue_field_key(source_issue, "route")
    if route_key and route_value:
        payload[route_key] = route_value

    functional_block_key, _ = get_functional_block_pair(source_issue)
    if functional_block_key:
        payload[functional_block_key] = FINANCE_BLOCK

    append_context_fields_to_payload(source_issue, payload)

    source_date_key, source_date_value = get_date_pair(source_issue)
    if source_date_key and source_date_value:
        payload[source_date_key] = source_date_value

    created_issue = create_issue(payload)
    created_issue_key = created_issue.get("key")
    if not created_issue_key:
        raise ValueError("created finance issue key is missing")

    create_issue_link(source_issue_key, created_issue_key)
    created_issue = get_issue(created_issue_key)
    chat_link_sync = sync_issue_chat_link_fields(created_issue_key, created_issue)

    flag_payload: Dict[str, Any] = {}
    set_issue_field_if_present(source_issue, flag_payload, "aFinancialIssueHasBeenCreated", "Да")
    if flag_payload:
        update_issue(source_issue_key, flag_payload)

    return {
        "ok": True,
        "mode": "created",
        "trigger_issue_key": trigger_issue_key,
        "source_issue_key": source_issue_key,
        "finance_issue_key": created_issue_key,
        "created_payload_keys": list(payload.keys()),
        "flag_payload_keys": list(flag_payload.keys()),
        "chat_link_sync": chat_link_sync,
    }


# ================= ROUTES =================

@app.route("/", methods=["GET"])
def root():
    return jsonify({"ok": True, "service": "tracker-webhooks"})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True})


@app.route("/webhook-sync-linked-fields", methods=["POST"])
@app.route("/webhook-sync-object", methods=["POST"])
def webhook_sync_linked_fields():
    try:
        data = request.get_json(force=True, silent=True) or {}
        issue_key = data.get("issue_key")

        if not issue_key:
            return jsonify({"ok": False, "error": "issue_key is required"}), 400

        log(f"[webhook-sync-linked-fields] issue={issue_key}")
        issue = get_issue(issue_key)
        chat_link_sync = sync_issue_chat_link_fields(issue_key, issue)
        result = sync_fields_from_supply_to_issue(issue_key)
        return jsonify({"ok": True, "chat_link_sync": chat_link_sync, **result})

    except Exception as exc:
        log_exception("[webhook-sync-linked-fields] ERROR", exc)
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/webhook-finance-message", methods=["POST"])
def webhook_finance_message():
    try:
        data = request.get_json(force=True, silent=True) or {}
        issue_key = data.get("issue_key")

        if not issue_key:
            return jsonify({"ok": False, "error": "issue_key is required"}), 400

        log(f"[webhook-finance-message] issue={issue_key}")

        finance_issue = get_issue(issue_key)
        supply_key = find_supply_issue(issue_key)
        if not supply_key:
            return jsonify({"ok": False, "error": "linked supply issue not found"}), 404

        supply_issue = get_issue(supply_key)
        marker_context = get_latest_marker_comment_context(supply_key, INVOICE_MARKER)
        marker_comment_id = marker_context.get("id")
        finance_chat_id = resolve_issue_chat_id(finance_issue, "finance")

        with issue_stage_lock(issue_key):
            if finance_message_already_processed(issue_key, marker_comment_id):
                log(f"[webhook-finance-message] already processed for issue={issue_key}, marker_comment_id={marker_comment_id}")
                return jsonify({
                    "ok": True,
                    "issue_key": issue_key,
                    "supply_issue_key": supply_key,
                    "already_processed": True,
                    "marker_comment_id": marker_comment_id,
                    "actions": ["skip_already_processed_finance_message"],
                })

            finance_thread_id = get_or_create_issue_thread_id(
                issue_key,
                finance_issue,
                finance_chat_id,
                FINANCE_THREAD_FIELD,
                lambda: send_text(
                    finance_chat_id,
                    build_finance_message(issue_key, finance_issue, supply_key, supply_issue),
                    payload_id=f"finance-root::{issue_key}",
                ),
            )
            ensure_wiki_comment(issue_key, supply_issue)

            comment_files_sent, comment_file_errors = send_comment_files(
                finance_chat_id,
                supply_key,
                thread_id=finance_thread_id,
                intro_text="💰 Счет на согласование",
                copy_to_issue_key=issue_key,
            )

            issue_files_sent: List[str] = []
            issue_file_errors: List[str] = []
            if not comment_files_sent:
                issue_files_sent, issue_file_errors = send_issue_files(
                    finance_chat_id,
                    issue_key,
                    finance_issue,
                    thread_id=finance_thread_id,
                    intro_text="💰 Счет на согласование",
                )

            mark_finance_message_processed(
                issue_key,
                marker_comment_id,
                payload={
                    "supply_issue_key": supply_key,
                    "marker_comment_id": marker_comment_id,
                    "comment_files_sent": comment_files_sent,
                    "issue_files_sent": issue_files_sent,
                },
            )

        return jsonify({
            "ok": True,
            "issue_key": issue_key,
            "supply_issue_key": supply_key,
            "marker_comment_id": marker_comment_id,
            "issue_files_sent": issue_files_sent,
            "comment_files_sent": comment_files_sent,
            "issue_file_errors": issue_file_errors,
            "comment_file_errors": comment_file_errors,
        })

    except Exception as exc:
        log_exception("[webhook-finance-message] ERROR", exc)
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/webhook-create-delivery-control-task", methods=["POST"])
def webhook_create_delivery_control_task():
    try:
        data = request.get_json(force=True, silent=True) or {}
        issue_key = data.get("issue_key")

        if not issue_key:
            return jsonify({"ok": False, "error": "issue_key is required"}), 400

        log(f"[webhook-create-delivery-control-task] issue={issue_key}")
        result = create_delivery_control_task_from_issue(issue_key)
        return jsonify(result)

    except Exception as exc:
        log_exception("[webhook-create-delivery-control-task] ERROR", exc)
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/webhook-create-finance-task", methods=["POST"])
def webhook_create_finance_task():
    try:
        data = request.get_json(force=True, silent=True) or {}
        issue_key = data.get("issue_key")

        if not issue_key:
            return jsonify({"ok": False, "error": "issue_key is required"}), 400

        log(f"[webhook-create-finance-task] issue={issue_key}")
        result = create_finance_task_from_supply_issue(issue_key)
        return jsonify(result)

    except Exception as exc:
        log_exception("[webhook-create-finance-task] ERROR", exc)
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/webhook-init-initiator-finance-task", methods=["POST"])
def webhook_init_initiator_finance_task():
    try:
        data = request.get_json(force=True, silent=True) or {}
        issue_key = data.get("issue_key")

        if not issue_key:
            return jsonify({"ok": False, "error": "issue_key is required"}), 400

        status_display = data.get("status_display")
        if status_display is None:
            status_display = data.get("status")

        log(f"[webhook-init-initiator-finance-task] issue={issue_key}")
        result = init_initiator_finance_issue(issue_key, status_display=status_display)
        return jsonify(result)

    except Exception as exc:
        log_exception("[webhook-init-initiator-finance-task] ERROR", exc)
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/webhook-stage-update", methods=["POST"])
def webhook_stage_update():
    try:
        data = request.get_json(force=True, silent=True) or {}
        issue_key = data.get("issue_key")
        stage_code = data.get("stage_code")

        if not issue_key:
            return jsonify({"ok": False, "error": "issue_key is required"}), 400
        if not stage_code:
            return jsonify({"ok": False, "error": "stage_code is required"}), 400

        log(f"[webhook-stage-update] issue={issue_key}, stage_code={stage_code}")

        issue = get_issue(issue_key)
        chat_link_sync = sync_issue_chat_link_fields(issue_key, issue)
        supply_control_stage_codes = {
            "to_supply_control_supply",
            "supply_control_in_progress",
            "supply_control_need_info",
            "to_supply_control_accounting",
            "supply_control_done",
            "supply_control_cancelled",
        }
        supply_key = find_supply_issue(issue_key)

        if not supply_key and stage_code != "to_supply" and stage_code not in supply_control_stage_codes:
            return jsonify({"ok": False, "error": "linked supply issue not found"}), 404

        supply_issue = get_issue(supply_key) if supply_key else None
        source_issue_for_stage = issue if stage_code == "to_supply" else supply_issue
        supply_chat_id = resolve_source_chat_id(source_issue_for_stage)
        finance_chat_id = resolve_issue_chat_id(issue, "finance")
        accounting_chat_id = resolve_issue_chat_id(issue, "accounting")
        approved_invoices_chat_id = resolve_issue_chat_id(issue, "approved_invoices")

        result: Dict[str, Any] = {
            "ok": True,
            "issue_key": issue_key,
            "supply_issue_key": supply_key,
            "stage_code": stage_code,
            "actions": [],
            "chat_link_sync": chat_link_sync,
        }

        if stage_code == "to_supply":
            add_comment_once(issue_key, build_source_arrival_comment(issue))
            ensure_wiki_comment(issue_key, issue)
            supply_thread_id = get_or_create_issue_thread_id(
                issue_key,
                issue,
                supply_chat_id,
                SUPPLY_THREAD_FIELD,
                lambda: send_text(
                    supply_chat_id,
                    build_supply_message(issue_key, issue, "📦 Новая заявка"),
                    payload_id=f"supply-root::{issue_key}",
                ),
            )
            description_sent = send_issue_description_text(
                supply_chat_id,
                issue,
                thread_id=supply_thread_id,
            )

            sent_files, file_errors = send_issue_files(
                supply_chat_id,
                issue_key,
                issue,
                thread_id=supply_thread_id,
                intro_text="📎 Файл из описания задачи",
            )

            result["actions"] = ["comment_to_issue", "messenger_to_supply"]
            if description_sent:
                result["actions"].append("supply_issue_description")
            result["description_sent"] = description_sent
            result["issue_files_sent"] = sent_files
            result["issue_file_errors"] = file_errors

        elif stage_code == "supply_in_progress":
            ensure_wiki_comment(supply_key, supply_issue)
            supply_thread_id = get_or_create_issue_thread_id(
                supply_key,
                supply_issue,
                supply_chat_id,
                SUPPLY_THREAD_FIELD,
                lambda: send_text(
                    supply_chat_id,
                    build_supply_message(supply_key, supply_issue, "📦 Новая заявка"),
                    payload_id=f"supply-root::{supply_key}",
                ),
            )
            send_text(
                supply_chat_id,
                build_minimal_stage_message("🛠 В работе"),
                thread_id=supply_thread_id,
                payload_id=f"stage::{supply_key}::supply_in_progress",
            )
            result["actions"] = ["messenger_to_supply"]

        elif stage_code == "to_finance_review":
            marker_context = get_latest_marker_comment_context(supply_key, INVOICE_MARKER)
            marker_comment_id = marker_context.get("id") or "latest"

            add_comment(supply_key, "⏳ Передано на согласование оплаты")
            ensure_wiki_comment(supply_key, supply_issue)
            supply_thread_id = get_or_create_issue_thread_id(
                supply_key,
                supply_issue,
                supply_chat_id,
                SUPPLY_THREAD_FIELD,
                lambda: send_text(
                    supply_chat_id,
                    build_supply_message(supply_key, supply_issue, "📦 Новая заявка"),
                    payload_id=f"supply-root::{supply_key}",
                ),
            )
            send_text(
                supply_chat_id,
                build_minimal_stage_message("⏳ Передано на согласование оплаты"),
                thread_id=supply_thread_id,
                payload_id=f"stage::{supply_key}::to_finance_review::{marker_comment_id}",
            )
            comment_files_sent, comment_file_errors = send_comment_files(
                supply_chat_id,
                supply_key,
                thread_id=supply_thread_id,
            )
            result["actions"] = ["comment_to_supply_issue", "messenger_to_supply", "supply_invoice_files"]
            result["comment_files_sent"] = comment_files_sent
            result["comment_file_errors"] = comment_file_errors

        elif stage_code == "to_accounting":
            with issue_stage_lock(issue_key):
                if stage_event_already_processed(issue_key, stage_code):
                    log(f"[to_accounting] already processed for {issue_key}")
                    result["actions"] = ["skip_already_processed_to_accounting"]
                    result["already_processed"] = True
                    return jsonify(result)

                approval_comment = get_last_nonempty_comment_text(issue_key).strip()

                add_comment_once(supply_key, "✅ Оплата согласована")
                add_comment_once(supply_key, "🐝 Передано в бухгалтерию")
                ensure_wiki_comment(issue_key, issue)
                ensure_wiki_comment(supply_key, supply_issue)

                supply_thread_id = get_or_create_issue_thread_id(
                    supply_key,
                    supply_issue,
                    supply_chat_id,
                    SUPPLY_THREAD_FIELD,
                    lambda: send_text(
                        supply_chat_id,
                        build_supply_message(supply_key, supply_issue, "📦 Новая заявка"),
                        payload_id=f"supply-root::{supply_key}",
                    ),
                )
                send_text(
                    supply_chat_id,
                    build_minimal_stage_message("✅ Оплата согласована"),
                    thread_id=supply_thread_id,
                    payload_id=f"stage::{supply_key}::to_accounting::supply",
                )

                finance_thread_id = get_or_create_issue_thread_id(
                    issue_key,
                    issue,
                    finance_chat_id,
                    FINANCE_THREAD_FIELD,
                    lambda: send_text(
                        finance_chat_id,
                        build_finance_message(issue_key, issue, supply_key, supply_issue),
                        payload_id=f"finance-root::{issue_key}",
                    ),
                )
                send_text(
                    finance_chat_id,
                    build_minimal_stage_message("✅ Оплата согласована"),
                    thread_id=finance_thread_id,
                    payload_id=f"stage::{issue_key}::to_accounting::finance",
                )
                if approval_comment:
                    send_text(
                        finance_chat_id,
                        f"💬 Комментарий к согласованию оплаты:\n{approval_comment}",
                        thread_id=finance_thread_id,
                        payload_id=f"stage::{issue_key}::to_accounting::finance_comment",
                    )

                accounting_thread_id = get_or_create_issue_thread_id(
                    issue_key,
                    issue,
                    accounting_chat_id,
                    ACCOUNTING_THREAD_FIELD,
                    lambda: send_text(
                        accounting_chat_id,
                        build_accounting_message(issue_key, issue, supply_key, supply_issue),
                        payload_id=f"accounting-root::{issue_key}",
                    ),
                )

                send_text(
                    accounting_chat_id,
                    build_minimal_stage_message("✅ Оплата согласована"),
                    thread_id=accounting_thread_id,
                    payload_id=f"stage::{issue_key}::to_accounting::accounting",
                )
                if approval_comment:
                    send_text(
                        accounting_chat_id,
                        f"💬 Комментарий к согласованию оплаты:\n{approval_comment}",
                        thread_id=accounting_thread_id,
                        payload_id=f"stage::{issue_key}::to_accounting::accounting_comment",
                    )

                sent_issue_files, issue_file_errors = send_comment_files(
                    accounting_chat_id,
                    supply_key,
                    thread_id=accounting_thread_id,
                )

                approved_invoices_thread_id: Optional[int] = None
                approved_invoices_issue_files_sent: List[str] = []
                approved_invoices_issue_file_errors: List[str] = []
                approved_invoices_comment_sent = False
                if approved_invoices_chat_id:
                    approved_invoice_root = send_text(
                        approved_invoices_chat_id,
                        build_approved_invoice_message(issue_key, issue, supply_key, supply_issue),
                        payload_id=f"approved-invoice-root::{issue_key}",
                    )
                    approved_invoices_thread_id = normalize_thread_id(approved_invoice_root.get("message_id"))
                    if approved_invoices_thread_id is None:
                        raise ValueError(f"approved invoice root message_id is missing for {issue_key}")
                    if approval_comment:
                        send_text(
                            approved_invoices_chat_id,
                            f"💬 Комментарий к согласованию оплаты:\n{approval_comment}",
                            thread_id=approved_invoices_thread_id,
                            payload_id=f"stage::{issue_key}::to_accounting::approved_invoice_comment",
                        )
                        approved_invoices_comment_sent = True
                    approved_invoices_issue_files_sent, approved_invoices_issue_file_errors = send_comment_files(
                        approved_invoices_chat_id,
                        supply_key,
                        thread_id=approved_invoices_thread_id,
                    )

                mark_stage_event_processed(
                    issue_key,
                    stage_code,
                    payload={
                        "supply_issue_key": supply_key,
                        "approval_comment_present": bool(approval_comment),
                    },
                )

                result["actions"] = ["comments_to_supply_issue", "messenger_to_supply", "messenger_to_finance", "messenger_to_accounting"]
                if approved_invoices_chat_id:
                    result["actions"].append("messenger_to_approved_invoices")
                result["approval_comment_sent_to_finance"] = bool(approval_comment)
                result["approval_comment_sent_to_accounting"] = bool(approval_comment)
                result["issue_files_sent"] = sent_issue_files
                result["issue_file_errors"] = issue_file_errors
                result["approved_invoices_thread_id"] = approved_invoices_thread_id
                result["approved_invoices_issue_files_sent"] = approved_invoices_issue_files_sent
                result["approved_invoices_issue_file_errors"] = approved_invoices_issue_file_errors
                result["approval_comment_sent_to_approved_invoices"] = approved_invoices_comment_sent

        elif stage_code == "payment_done":
            with issue_stage_lock(issue_key):
                if stage_event_already_processed(issue_key, stage_code):
                    log(f"[payment_done] already processed for {issue_key}")
                    result["actions"] = ["skip_already_processed_payment_done"]
                    result["already_processed"] = True
                    return jsonify(result)

                add_comment_once(supply_key, "💸 Оплата произведена")
                ensure_wiki_comment(supply_key, supply_issue)

                supply_thread_id = get_or_create_issue_thread_id(
                    supply_key,
                    supply_issue,
                    supply_chat_id,
                    SUPPLY_THREAD_FIELD,
                    lambda: send_text(
                        supply_chat_id,
                        build_supply_message(supply_key, supply_issue, "📦 Новая заявка"),
                        payload_id=f"supply-root::{supply_key}",
                    ),
                )
                send_text(
                    supply_chat_id,
                    build_minimal_stage_message("💸 Оплата произведена"),
                    thread_id=supply_thread_id,
                    payload_id=f"stage::{issue_key}::payment_done::supply",
                )

                finance_thread_id = get_issue_thread_id(issue, FINANCE_THREAD_FIELD)
                if finance_thread_id:
                    send_text(
                        finance_chat_id,
                        build_minimal_stage_message("💸 Оплата произведена"),
                        thread_id=finance_thread_id,
                        payload_id=f"stage::{issue_key}::payment_done::finance",
                    )

                accounting_thread_id = get_issue_thread_id(issue, ACCOUNTING_THREAD_FIELD)
                if accounting_thread_id:
                    send_text(
                        accounting_chat_id,
                        build_minimal_stage_message("💸 Оплата произведена"),
                        thread_id=accounting_thread_id,
                        payload_id=f"stage::{issue_key}::payment_done::accounting",
                    )

                log(f"[payment_done] issue={issue_key} recorded; payment notification sent")
                result["actions"] = ["comment_to_supply_issue", "messenger_to_supply", "messenger_to_finance", "messenger_to_accounting", "payment_recorded"]

                paid_invoice_result = process_paid_invoice_distribution(
                    issue_key,
                    issue,
                    supply_key,
                    supply_issue,
                    PAID_INVOICE_MARKER,
                    include_payment_status=False,
                    intro_text=None,
                    copy_comment_text="💸 Платежка направлена\n{paid_invoice_marker}",
                )
                result["actions"].extend(
                    action
                    for action in paid_invoice_result.get("actions", [])
                    if action not in result["actions"]
                )
                result["paid_invoice_comment_id"] = paid_invoice_result.get("paid_invoice_comment_id")
                result["paid_files_sent"] = paid_invoice_result.get("paid_files_sent", [])
                result["paid_file_errors"] = paid_invoice_result.get("paid_file_errors", [])
                result["finance_files_sent"] = paid_invoice_result.get("finance_files_sent", [])
                result["finance_file_errors"] = paid_invoice_result.get("finance_file_errors", [])
                result["accounting_files_sent"] = paid_invoice_result.get("accounting_files_sent", [])
                result["accounting_file_errors"] = paid_invoice_result.get("accounting_file_errors", [])

                mark_stage_event_processed(
                    issue_key,
                    stage_code,
                    payload={
                        "supply_issue_key": supply_key,
                        "paid_invoice_comment_id": paid_invoice_result.get("paid_invoice_comment_id"),
                    },
                )

        elif stage_code in supply_control_stage_codes:
            supply_control_status_map = {
                "to_supply_control_supply": "Беклог",
                "supply_control_in_progress": "В работе",
                "supply_control_need_info": "Требуется информация",
                "to_supply_control_accounting": "Ревью",
                "supply_control_done": "Готово",
                "supply_control_cancelled": "Отменено",
            }
            status_display = supply_control_status_map[stage_code]
            previous_status = data.get("previous_status") or data.get("old_status_display") or data.get("old_status")

            ensure_wiki_comment(issue_key, issue)
            with issue_stage_lock(issue_key):
                supply_control_result = send_supply_control_notification(
                    issue_key,
                    issue,
                    status_display=status_display,
                    previous_status=previous_status,
                )

            result["actions"] = ["messenger_supply_control"]
            result["status_display"] = status_display
            result["supply_control"] = supply_control_result

        

        elif stage_code == "finance_rejected":
                    if finance_rejection_already_processed(supply_key, issue_key):
                        log(f"[finance_rejected] already processed for supply={supply_key}, finance={issue_key}")
                        result["actions"] = ["skip_already_processed"]
                        result["already_processed"] = True
                        return jsonify(result)
        
                    rejection_reason = get_last_nonempty_comment_text(issue_key).strip()
                    marker = finance_rejection_marker(issue_key)
        
                    comment_text = "❌ Оплата не согласована"
                    if rejection_reason:
                        comment_text += f"\n\nПричина:\n{rejection_reason}"
                    comment_text += f"\n\n{marker}"
        
                    add_comment_once(supply_key, comment_text)
                    ensure_wiki_comment(supply_key, supply_issue)
        
                    status_changed = transition_issue_to_status(supply_key, "Требуется информация")
        
                    supply_thread_id = get_or_create_issue_thread_id(
                        supply_key,
                        supply_issue,
                        supply_chat_id,
                        SUPPLY_THREAD_FIELD,
                        lambda: send_text(
                            supply_chat_id,
                            build_supply_message(supply_key, supply_issue, "📦 Новая заявка"),
                            payload_id=f"supply-root::{supply_key}",
                        ),
                    )
        
                    messenger_text = "❌ Оплата не согласована"
                    if rejection_reason:
                        messenger_text += f"\n\nПричина:\n{rejection_reason}"
        
                    send_text(
                        supply_chat_id,
                        messenger_text,
                        thread_id=supply_thread_id,
                        payload_id=f"stage::{issue_key}::finance_rejected::supply",
                    )
        
                    finance_thread_id = get_issue_thread_id(issue, FINANCE_THREAD_FIELD)
                    if finance_thread_id:
                            send_text(
                                finance_chat_id,
                                messenger_text,
                                thread_id=finance_thread_id,
                                payload_id=f"stage::{issue_key}::finance_rejected::finance",
                        )
        
                    reset_done = False
                    try:
                        reset_done = reset_finance_issue_created_flag(supply_key, supply_issue)
                    except Exception as reset_exc:
                        log(f"[finance_rejected] reset flag error for {supply_key}: {reset_exc}")
        
                    result["actions"] = [
                        "comment_to_supply_issue",
                        "transition_supply_to_need_info",
                        "reset_finance_issue_created_flag",
                        "messenger_to_supply",
                        "messenger_to_finance",
                    ]
                    result["rejection_reason"] = rejection_reason
                    result["finance_issue_created_flag_reset"] = reset_done
                    result["supply_status_changed"] = status_changed
                    result["rejection_marker"] = marker

        elif stage_code in {"paid_invoice_ready", "paid_invoice_reload"}:
            marker = PAID_INVOICE_RELOAD_MARKER if stage_code == "paid_invoice_reload" else PAID_INVOICE_MARKER
            intro_text = "📎 Дозагруженные платежки" if stage_code == "paid_invoice_reload" else None
            copy_comment_text = (
                "📎 Дозагруженные платежки\n{paid_invoice_marker}"
                if stage_code == "paid_invoice_reload"
                else "💸 Платежка направлена\n{paid_invoice_marker}"
            )

            paid_invoice_result = process_paid_invoice_distribution(
                issue_key,
                issue,
                supply_key,
                supply_issue,
                marker,
                include_payment_status=(stage_code == "paid_invoice_ready"),
                intro_text=intro_text,
                copy_comment_text=copy_comment_text,
            )
            result["actions"] = paid_invoice_result.get("actions", [])
            result["paid_files_sent"] = paid_invoice_result.get("paid_files_sent", [])
            result["paid_file_errors"] = paid_invoice_result.get("paid_file_errors", [])
            result["finance_files_sent"] = paid_invoice_result.get("finance_files_sent", [])
            result["finance_file_errors"] = paid_invoice_result.get("finance_file_errors", [])
            result["accounting_files_sent"] = paid_invoice_result.get("accounting_files_sent", [])
            result["accounting_file_errors"] = paid_invoice_result.get("accounting_file_errors", [])
            result["paid_invoice_comment_id"] = paid_invoice_result.get("paid_invoice_comment_id")
            if paid_invoice_result.get("already_processed"):
                result["already_processed"] = True



        else:
            return jsonify({"ok": False, "error": f"unknown stage_code: {stage_code}"}), 400

        return jsonify(result)

    except Exception as exc:
        log_exception("[webhook-stage-update] ERROR", exc)
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/webhook-supply-control-status", methods=["POST"])
@app.route("/webhook-delivery-control-status", methods=["POST"])
def webhook_supply_control_status():
    payload = request.get_json(force=True, silent=False) or {}
    issue_key = payload.get("issue_key")
    if not issue_key:
        return jsonify({"ok": False, "error": "issue_key is required"}), 400

    try:
        issue = get_issue(issue_key)
        chat_link_sync = sync_issue_chat_link_fields(issue_key, issue)
        previous_status = payload.get("old_status")
        if previous_status is None:
            previous_status = payload.get("previous_status")
        if previous_status is None:
            previous_status = payload.get("old_status_display")

        current_status = payload.get("status")
        if current_status is None:
            current_status = payload.get("status_display")
        if current_status is None:
            current_status = payload.get("new_status")
        if current_status is None:
            current_status = payload.get("current_status")
        if current_status is None:
            current_status = issue.get("status")

        payload_keys = sorted(str(key) for key in payload.keys())
        log(
            "[webhook-supply-control-status] "
            f"issue={issue_key}, previous_status={get_display(previous_status)}, "
            f"current_status={get_display(current_status)}, payload_keys={payload_keys}"
        )

        supply_control_result = send_supply_control_notification(
            issue_key,
            issue,
            status_display=current_status,
            previous_status=previous_status,
        )
        return jsonify({
            "ok": True,
            "issue_key": issue_key,
            "payload_keys": payload_keys,
            "chat_link_sync": chat_link_sync,
            "supply_control": supply_control_result,
        })
    except Exception as exc:
        log_exception("[webhook-supply-control-status] ERROR", exc)
        return jsonify({
            "ok": True,
            "issue_key": issue_key,
            "payload_keys": sorted(str(key) for key in payload.keys()),
            "supply_control": {
                "sent": False,
                "reason": "exception",
                "error": str(exc),
            },
        })


@app.route("/webhook-project-status-notification", methods=["POST"])
@app.route("/webhook-task-status-notification", methods=["POST"])
def webhook_project_status_notification():
    payload = request.get_json(force=True, silent=False) or {}
    issue_key = payload.get("issue_key")
    if not issue_key:
        return jsonify({"ok": False, "error": "issue_key is required"}), 400

    try:
        issue = get_issue(issue_key)
        previous_status = payload.get("old_status")
        if previous_status is None:
            previous_status = payload.get("previous_status")
        if previous_status is None:
            previous_status = payload.get("old_status_display")

        current_status = payload.get("status")
        if current_status is None:
            current_status = payload.get("status_display")
        if current_status is None:
            current_status = payload.get("new_status")
        if current_status is None:
            current_status = payload.get("current_status")
        if current_status is None:
            current_status = issue.get("status")

        should_notify, should_notify_reason = should_send_initiator_notification(issue_key, issue)
        if not should_notify:
            log(
                "[webhook-project-status-notification] "
                f"skip issue={issue_key}, reason={should_notify_reason}"
            )
            return jsonify({
                "ok": True,
                "issue_key": issue_key,
                "payload_keys": sorted(str(key) for key in payload.keys()),
                "chat_link_sync": {
                    "skipped": True,
                    "reason": should_notify_reason,
                },
                "project_notification": {
                    "sent": False,
                    "reason": should_notify_reason,
                },
            })

        if should_suppress_initiator_supply_control_start_notification(issue, current_status):
            log(
                "[webhook-project-status-notification] "
                f"skip issue={issue_key}, reason=initiator_supply_control_start_is_silent"
            )
            return jsonify({
                "ok": True,
                "issue_key": issue_key,
                "payload_keys": sorted(str(key) for key in payload.keys()),
                "chat_link_sync": {
                    "skipped": True,
                    "reason": "initiator_supply_control_start_is_silent",
                },
                "project_notification": {
                    "sent": False,
                    "reason": "initiator_supply_control_start_is_silent",
                },
            })

        chat_link_sync = sync_issue_chat_link_fields(issue_key, issue)
        payload_keys = sorted(str(key) for key in payload.keys())
        log(
            "[webhook-project-status-notification] "
            f"issue={issue_key}, previous_status={get_display(previous_status)}, "
            f"current_status={get_display(current_status)}, payload_keys={payload_keys}"
        )

        notification_result = send_project_status_notification(
            issue_key,
            issue,
            previous_status=previous_status,
            current_status=current_status,
        )
        log(
            "[webhook-project-status-notification] "
            f"resolved_object={notification_result.get('resolved_object', '')}, "
            f"resolved_chat_id={notification_result.get('resolved_chat_id', '')}, "
            f"routing_source={notification_result.get('routing_source', '')}, "
            f"thread_mode_reason={notification_result.get('thread_mode_reason', '')}"
        )
        return jsonify({
            "ok": True,
            "issue_key": issue_key,
            "payload_keys": payload_keys,
            "chat_link_sync": chat_link_sync,
            "project_notification": notification_result,
        })
    except Exception as exc:
        log_exception("[webhook-project-status-notification] ERROR", exc)
        return jsonify({
            "ok": True,
            "issue_key": issue_key,
            "payload_keys": sorted(str(key) for key in payload.keys()),
            "project_notification": {
                "sent": False,
                "reason": "exception",
                "error": str(exc),
            },
        })


@app.route("/webhook-sync-department-boards", methods=["POST"])
def webhook_sync_department_boards():
    payload = request.get_json(force=True, silent=False) or {}
    issue_key = payload.get("issue_key")
    if not issue_key:
        return jsonify({"ok": False, "error": "issue_key is required"}), 400

    try:
        issue = get_issue(issue_key)
        result = sync_department_boards(issue_key, issue)
        log(
            "[webhook-sync-department-boards] "
            f"issue={issue_key}, queue={result.get('queue_key')}, "
            f"updated={result.get('updated')}, reason={result.get('reason')}, "
            f"added={result.get('added_ids')}, removed={result.get('removed_ids')}"
        )
        return jsonify({
            "ok": True,
            "issue_key": issue_key,
            "payload_keys": sorted(str(key) for key in payload.keys()),
            "department_boards": result,
        })
    except Exception as exc:
        log_exception("[webhook-sync-department-boards] ERROR", exc)
        return jsonify({
            "ok": True,
            "issue_key": issue_key,
            "payload_keys": sorted(str(key) for key in payload.keys()),
            "department_boards": {
                "updated": False,
                "reason": "exception",
                "error": str(exc),
            },
        })


if __name__ == "__main__":
    log("🚀 tracker-webhooks started on 0.0.0.0:8080")
    app.run(host="0.0.0.0", port=8080)
