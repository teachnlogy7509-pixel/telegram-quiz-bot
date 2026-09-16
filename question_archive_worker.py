"""Build four-day Hindi Notes/Test PDFs from Telegram quiz events and keep them in Drive."""
from __future__ import annotations

import io
import json
import logging
import os
import re
import time
from datetime import datetime, timedelta, timezone
from html import escape
from urllib import error, parse, request

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
log = logging.getLogger("rathod-question-archive")

SUPA_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPA_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN", "").strip()
NOTES_FOLDER = os.getenv("DRIVE_FOLDER_QUESTION_NOTES", "").strip()
TESTS_FOLDER = os.getenv("DRIVE_FOLDER_QUESTION_TESTS", "").strip()
POLL_SECONDS = max(60, int(os.getenv("ARCHIVE_POLL_SECONDS", "120")))
FONT_NAME = "RathodDevanagari"
FONT_PATH = next(
    (
        path
        for path in (
            "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
            "/usr/share/fonts/opentype/noto/NotoSansDevanagari-Regular.ttf",
            "/tmp/NotoSansDevanagari-Regular.ttf",
        )
        if os.path.exists(path)
    ),
    "/tmp/NotoSansDevanagari-Regular.ttf",
)
LATIN_FONT_NAME = "RathodLatin"
LATIN_FONT_PATH = next(
    (
        path
        for path in (
            "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
            "/usr/share/fonts/opentype/noto/NotoSans-Regular.ttf",
            "/usr/share/fonts/google-noto/NotoSans-Regular.ttf",
            "/tmp/NotoSans-Regular.ttf",
        )
        if os.path.exists(path)
    ),
    "/tmp/NotoSans-Regular.ttf",
)


def valid_ttf(path: str) -> bool:
    if not os.path.exists(path) or os.path.getsize(path) < 10_000:
        return False
    with open(path, "rb") as handle:
        magic = handle.read(4)
    return magic in (b"\x00\x01\x00\x00", b"OTTO", b"true", b"typ1")


def download_ttf(path: str, urls: list[str]) -> None:
    last_error = None
    for url in urls:
        try:
            req = request.Request(url, headers={"User-Agent": "RATHOD-HUB-Archive/1.0"})
            with request.urlopen(req, timeout=60) as response:
                data = response.read()
            if len(data) < 10_000 or data[:4] not in (b"\x00\x01\x00\x00", b"OTTO", b"true", b"typ1"):
                raise RuntimeError("downloaded response is not a TTF")
            with open(path, "wb") as handle:
                handle.write(data)
            if valid_ttf(path):
                return
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"font download failed: {last_error}")


def ensure_hindi_font() -> str:
    """Load a real Devanagari font; never silently produce a broken Hindi PDF."""
    if FONT_NAME in pdfmetrics.getRegisteredFontNames():
        return FONT_NAME
    try:
        if os.path.exists(FONT_PATH) and not valid_ttf(FONT_PATH) and FONT_PATH.startswith("/tmp/"):
            os.remove(FONT_PATH)
        if not os.path.exists(FONT_PATH):
            download_ttf(
                FONT_PATH,
                [
                    "https://github.com/openmaptiles/fonts/raw/refs/heads/master/noto-sans/NotoSansDevanagari-Regular.ttf",
                    "https://raw.githubusercontent.com/openmaptiles/fonts/master/noto-sans/NotoSansDevanagari-Regular.ttf",
                    "https://cdn.jsdelivr.net/gh/openmaptiles/fonts@master/noto-sans/NotoSansDevanagari-Regular.ttf",
                ],
            )
        pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH, shapable=True))
        log.info("Hindi PDF font ready: %s", FONT_PATH)
        return FONT_NAME
    except Exception as exc:
        raise RuntimeError("Hindi Devanagari font unavailable; refusing to create an incorrectly rendered PDF") from exc


def ensure_latin_font() -> str:
    """Load a Latin fallback so English, numbers and scientific symbols are not boxes."""
    if LATIN_FONT_NAME in pdfmetrics.getRegisteredFontNames():
        return LATIN_FONT_NAME
    try:
        if os.path.exists(LATIN_FONT_PATH) and not valid_ttf(LATIN_FONT_PATH) and LATIN_FONT_PATH.startswith("/tmp/"):
            os.remove(LATIN_FONT_PATH)
        if not os.path.exists(LATIN_FONT_PATH):
            download_ttf(
                LATIN_FONT_PATH,
                [
                    "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSans/NotoSans-Regular.ttf",
                    "https://raw.githubusercontent.com/googlefonts/noto-fonts/main/hinted/ttf/NotoSans/NotoSans-Regular.ttf",
                    "https://cdn.jsdelivr.net/gh/notofonts/noto-fonts@main/hinted/ttf/NotoSans/NotoSans-Regular.ttf",
                ],
            )
        pdfmetrics.registerFont(TTFont(LATIN_FONT_NAME, LATIN_FONT_PATH, shapable=True))
        log.info("Latin fallback font ready: %s", LATIN_FONT_PATH)
        return LATIN_FONT_NAME
    except Exception as exc:
        raise RuntimeError("Latin fallback font unavailable; refusing to create a PDF with missing glyphs") from exc


def pdf_text(value: object) -> str:
    """Use Devanagari for Hindi and a full Latin font for English/numbers/symbols."""
    text = str(value or "")
    if not text:
        return ""
    chunks: list[str] = []
    current: list[str] = []
    current_latin: bool | None = None

    def flush() -> None:
        if not current:
            return
        escaped = escape("".join(current))
        if current_latin:
            chunks.append(f'<font name="{LATIN_FONT_NAME}">{escaped}</font>')
        else:
            chunks.append(escaped)
        current.clear()

    for char in text:
        code = ord(char)
        is_latin = not (0x0900 <= code <= 0x097F)
        if current_latin is not None and is_latin != current_latin:
            flush()
        current_latin = is_latin
        current.append(char)
    flush()
    return "".join(chunks)


def rest(method: str, table: str, params: dict | None = None, body: dict | None = None):
    if not SUPA_URL or not SUPA_KEY:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")
    url = f"{SUPA_URL}/rest/v1/{table}"
    if params:
        url += "?" + parse.urlencode(params, safe="(),.*")
    headers = {
        "apikey": SUPA_KEY,
        "Authorization": f"Bearer {SUPA_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    try:
        with request.urlopen(request.Request(url, data=data, headers=headers, method=method), timeout=30) as response:
            text = response.read().decode()
        return json.loads(text) if text else None
    except error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:800]
        raise RuntimeError(f"Supabase {method} {table} failed HTTP {exc.code}: {detail}") from exc


def token() -> str:
    if not all((CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN)):
        raise RuntimeError("Google Drive OAuth variables are missing")
    body = parse.urlencode(
        {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": REFRESH_TOKEN,
            "grant_type": "refresh_token",
        }
    ).encode()
    with request.urlopen(
        request.Request(
            "https://oauth2.googleapis.com/token",
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        ),
        timeout=25,
    ) as response:
        data = json.loads(response.read().decode())
    if not data.get("access_token"):
        raise RuntimeError("Google OAuth refresh failed")
    return str(data["access_token"])


def drive(method: str, url: str, access: str, body=None, content_type: str | None = None):
    headers = {"Authorization": f"Bearer {access}"}
    if content_type:
        headers["Content-Type"] = content_type
    with request.urlopen(request.Request(url, data=body, headers=headers, method=method), timeout=60) as response:
        text = response.read().decode()
    return json.loads(text) if text else {}


def find_file(access: str, folder: str, name: str):
    safe = name.replace("'", "\\'")
    query = f"'{folder}' in parents and name = '{safe}' and trashed = false"
    data = drive(
        "GET",
        "https://www.googleapis.com/drive/v3/files?" + parse.urlencode({"q": query, "fields": "files(id,name,webViewLink)", "pageSize": "10"}),
        access,
    )
    files = data.get("files") or []
    return files[0] if files else None


def ensure_group_access(access: str, file_id: str) -> None:
    """Allow Telegram group members with the link to open the PDF."""
    try:
        permissions_url = "https://www.googleapis.com/drive/v3/files/" + file_id + "/permissions?fields=permissions(id,type,role)"
        data = drive("GET", permissions_url, access)
        if not any(p.get("type") == "anyone" and p.get("role") == "reader" for p in data.get("permissions", [])):
            drive(
                "POST",
                "https://www.googleapis.com/drive/v3/files/" + file_id + "/permissions?fields=id",
                access,
                json.dumps({"type": "anyone", "role": "reader"}).encode(),
                "application/json",
            )
    except Exception as exc:
        log.warning("Could not enable group link access for %s: %s", file_id, str(exc)[:160])


def upload_or_update(access: str, folder: str, name: str, pdf: bytes) -> str:
    old = find_file(access, folder, name)
    if old:
        data = drive(
            "PATCH",
            "https://www.googleapis.com/upload/drive/v3/files/" + str(old["id"]) + "?uploadType=media&fields=id,name,webViewLink",
            access,
            pdf,
            "application/pdf",
        )
        file_id = str(data.get("id") or old["id"])
    else:
        boundary = "rathodarchiveboundary"
        metadata = json.dumps({"name": name, "parents": [folder]}).encode()
        body = (
            b"--" + boundary.encode() + b"\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n"
            + metadata
            + b"\r\n--"
            + boundary.encode()
            + b"\r\nContent-Type: application/pdf\r\n\r\n"
            + pdf
            + b"\r\n--"
            + boundary.encode()
            + b"--\r\n"
        )
        data = drive(
            "POST",
            "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,webViewLink",
            access,
            body,
            "multipart/related; boundary=" + boundary,
        )
        file_id = str(data.get("id") or "")
    if not file_id:
        raise RuntimeError("Drive did not return a file ID")
    ensure_group_access(access, file_id)
    return "https://drive.google.com/file/d/" + file_id + "/view?usp=sharing"


def publish_archive_links(label: str, notes_url: str, test_url: str) -> None:
    """Store one latest link record so Sakhi can answer /archivepdf."""
    payload = {
        "label": label,
        "notes_url": notes_url or "",
        "test_url": test_url or "",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    rows = rest(
        "GET",
        "rh_bridge_events",
        {"select": "id,payload", "event_type": "eq.archive_pdf_ready", "order": "created_at.desc", "limit": "1"},
    ) or []
    body = {
        "event_type": "archive_pdf_ready",
        "delivery_mode": "digest",
        "display_name": "RATHOD Question Archive",
        "payload": payload,
    }
    if rows and isinstance(rows[0].get("payload"), dict) and rows[0]["payload"].get("label") == label:
        rest("PATCH", "rh_bridge_events", {"id": f"eq.{rows[0]['id']}"}, {"payload": payload})
    else:
        rest("POST", "rh_bridge_events", body=body)


def window(now: datetime):
    start = now.replace(day=((now.day - 1) // 4) * 4 + 1, hour=0, minute=0, second=0, microsecond=0)
    return start, start + timedelta(days=4)


def allowed_source(row: dict) -> bool:
    payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
    text = " ".join(str(payload.get(key, "")) for key in ("source", "mode", "quiz_name", "event_type")).lower().replace("_", " ")
    if "telegram" in text:
        return True
    return bool(re.search(r"neet\s*720|daily\s*9\s*pm|9\s*pm\s*(battle|arena|quiz)|scheduled\s*(battle|quiz)", text, re.I))


def is_old_daily_event(row: dict) -> bool:
    payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
    source = str(payload.get("source", "")).lower()
    if "telegram" in source:
        return False
    text = " ".join(str(payload.get(key, "")) for key in ("source", "mode", "quiz_name", "event_type")).lower()
    return "daily event" in text or "dailyevent" in text


def extract(row: dict):
    payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
    question = str(payload.get("question") or "").strip()
    options = payload.get("options")
    if not question or not isinstance(options, list) or len(options) != 4:
        return None
    try:
        correct = int(payload.get("correct_index")) if payload.get("correct_index") is not None else None
    except (TypeError, ValueError):
        correct = None
    return {
        "question": question,
        "options": [str(option) for option in options],
        "correct_index": correct,
        "mode": str(payload.get("mode") or "Quiz"),
    }


def make_pdf(title: str, rows: list[dict], answers: bool) -> bytes:
    font = ensure_hindi_font()
    ensure_latin_font()
    output = io.BytesIO()
    document = SimpleDocTemplate(output, pagesize=A4, rightMargin=16 * mm, leftMargin=16 * mm, topMargin=15 * mm, bottomMargin=15 * mm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="RATitle", parent=styles["Title"], fontName=font, shaping=1))
    styles.add(ParagraphStyle(name="RA", parent=styles["BodyText"], fontName=font, fontSize=8.5, leading=12, shaping=1))
    styles.add(ParagraphStyle(name="RQ", parent=styles["Heading3"], fontName=font, fontSize=10.5, leading=14, spaceBefore=8, spaceAfter=4, shaping=1))
    story = [
        Paragraph(pdf_text(title), styles["RATitle"]),
        Spacer(1, 5 * mm),
        Paragraph(pdf_text(f"कुल प्रश्न: {len(rows)} | RATHOD HUB संग्रह"), styles["RA"]),
    ]
    option_letters = ("क", "ख", "ग", "घ")
    for number, question in enumerate(rows, 1):
        story.append(Paragraph(pdf_text(f"{number}. [{question['mode']}] {question['question']}"), styles["RQ"]))
        for index, option in enumerate(question["options"]):
            story.append(Paragraph(pdf_text(f"{option_letters[index]}. {option}"), styles["RA"]))
        if answers:
            answer = "उपलब्ध नहीं" if question["correct_index"] is None else option_letters[question["correct_index"]]
            story.append(Paragraph(pdf_text("सही उत्तर: " + answer), styles["RA"]))
    document.build(story)
    return output.getvalue()


def rows_for(start: datetime, end: datetime) -> list[dict]:
    raw = rest(
        "GET",
        "rh_bridge_events",
        {"select": "id,event_type,payload,created_at", "created_at": f"gte.{start.isoformat()}", "order": "created_at.asc", "limit": "2000"},
    ) or []
    unique = {}
    for row in raw:
        try:
            created = datetime.fromisoformat(str(row.get("created_at", "")).replace("Z", "+00:00"))
        except ValueError:
            continue
        if created >= end or is_old_daily_event(row) or not allowed_source(row) or row.get("event_type") not in {"quiz_question", "quiz_item", "question_solved"}:
            continue
        question = extract(row)
        if question:
            unique.setdefault((question["question"], question["mode"]), question)
    return list(unique.values())


def run_once() -> None:
    start, end = window(datetime.now(timezone.utc))
    rows = rows_for(start, end)
    if not rows:
        log.info("No allowed questions in %s-%s", start.date(), (end - timedelta(days=1)).date())
        return
    access = token()
    label = start.strftime("%d-%b") + "_to_" + (end - timedelta(days=1)).strftime("%d-%b-%Y")
    notes_url = ""
    test_url = ""
    if NOTES_FOLDER:
        notes_url = upload_or_update(access, NOTES_FOLDER, "Notes_" + label + ".pdf", make_pdf("RATHOD HUB नोट्स - " + label, rows, True))
        log.info("Notes PDF: %s", notes_url)
    if TESTS_FOLDER:
        test_url = upload_or_update(access, TESTS_FOLDER, "Test_" + label + ".pdf", make_pdf("RATHOD HUB टेस्ट प्रश्नपत्र - " + label, rows, False))
        log.info("Test PDF: %s", test_url)
    if notes_url or test_url:
        try:
            publish_archive_links(label, notes_url, test_url)
        except Exception as exc:
            log.warning("PDFs updated, but Sakhi archive link sync failed: %s", str(exc)[:800])


def main() -> None:
    if not all((SUPA_URL, SUPA_KEY, CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN)):
        raise SystemExit("Supabase and Google Drive OAuth variables are required")
    while True:
        try:
            run_once()
        except Exception:
            log.exception("Archive pass failed")
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
