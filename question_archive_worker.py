"""RATHOD HUB rolling question archive worker.

Consumes public.rh_bridge_events quiz_question events, skips Daily Event,
builds four-day Notes and Test PDFs, and upserts them into existing Google
Drive folders using the same OAuth credentials as the google-drive function.
Run as a small Railway service: python question_archive_worker.py
"""
from __future__ import annotations

import io
import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from html import escape
from urllib import parse, request

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

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


def rest(method: str, table: str, params: dict[str, str] | None = None, body: object | None = None):
    if not SUPA_URL or not SUPA_KEY:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")
    url = f"{SUPA_URL}/rest/v1/{table}"
    if params:
        url += "?" + parse.urlencode(params, safe="(),.*")
    headers = {"apikey": SUPA_KEY, "Authorization": f"Bearer {SUPA_KEY}", "Content-Type": "application/json", "Accept": "application/json"}
    data = None if body is None else json.dumps(body).encode()
    with request.urlopen(request.Request(url, data=data, headers=headers, method=method), timeout=30) as response:
        text = response.read().decode()
        return json.loads(text) if text else None


def access_token() -> str:
    if not all((CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN)):
        raise RuntimeError("Google Drive OAuth variables are missing")
    body = parse.urlencode({"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "refresh_token": REFRESH_TOKEN, "grant_type": "refresh_token"}).encode()
    with request.urlopen(request.Request("https://oauth2.googleapis.com/token", data=body, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST"), timeout=25) as response:
        data = json.loads(response.read().decode())
    if not data.get("access_token"):
        raise RuntimeError("Google OAuth refresh failed")
    return str(data["access_token"])


def drive_request(token: str, method: str, url: str, body: bytes | None = None, content_type: str | None = None):
    headers = {"Authorization": f"Bearer {token}"}
    if content_type:
        headers["Content-Type"] = content_type
    with request.urlopen(request.Request(url, data=body, headers=headers, method=method), timeout=60) as response:
        text = response.read().decode()
        return json.loads(text) if text else {}


def find_file(token: str, folder_id: str, name: str) -> dict | None:
    q = f"'{folder_id}' in parents and name = '{name.replace(chr(39), chr(92)+chr(39))}' and trashed = false"
    params = parse.urlencode({"q": q, "fields": "files(id,name,mimeType,webViewLink)", "pageSize": "10"})
    data = drive_request(token, "GET", f"https://www.googleapis.com/drive/v3/files?{params}")
    files = data.get("files") or []
    return files[0] if files else None


def upload_or_update(token: str, folder_id: str, name: str, content: bytes) -> dict:
    old = find_file(token, folder_id, name)
    if old:
        result = drive_request(token, "PATCH", f"https://www.googleapis.com/upload/drive/v3/files/{old['id']}?uploadType=media&fields=id,name,webViewLink", content, "application/pdf")
    else:
        metadata = json.dumps({"name": name, "parents": [folder_id]}).encode()
        boundary = "rathodarchiveboundary"
        body = b"--" + boundary.encode() + b"\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n" + metadata + b"\r\n--" + boundary.encode() + b"\r\nContent-Type: application/pdf\r\n\r\n" + content + b"\r\n--" + boundary.encode() + b"--\r\n"
        result = drive_request(token, "POST", "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,webViewLink", body, f"multipart/related; boundary={boundary}")
    file_id = str(result.get("id") or old.get("id") if old else result.get("id") or "")
    return {"id": file_id, "name": name, "url": f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"}


def batch_dates(day: datetime) -> tuple[datetime, datetime]:
    start_day = ((day.day - 1) // 4) * 4 + 1
    start = day.replace(day=start_day, hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=4)
    return start, end


def is_daily(row: dict) -> bool:
    p = row.get("payload") if isinstance(row.get("payload"), dict) else {}
    text = " ".join(str(p.get(k, "")) for k in ("source", "mode", "quiz_name", "event_type")).lower()
    return any(x in text for x in ("daily event", "daily 9 pm", "daily_9pm", "dailyevent"))


def question_from(row: dict) -> dict | None:
    p = row.get("payload") if isinstance(row.get("payload"), dict) else {}
    question = str(p.get("question") or "").strip()
    options = p.get("options")
    if not question or not isinstance(options, list) or len(options) != 4:
        return None
    try:
        correct = int(p.get("correct_index")) if p.get("correct_index") is not None else None
    except (TypeError, ValueError):
        correct = None
    return {"question": question, "options": [str(x) for x in options], "correct_index": correct, "explanation": str(p.get("explanation") or ""), "source": str(p.get("source") or row.get("source") or "App"), "mode": str(p.get("mode") or "Quiz"), "quiz_name": str(p.get("quiz_name") or p.get("room") or p.get("mode") or "Practice Quiz"), "created_at": str(row.get("created_at") or "")}


def make_pdf(title: str, rows: list[dict], include_answers: bool) -> bytes:
    out = io.BytesIO(); doc = SimpleDocTemplate(out, pagesize=A4, rightMargin=16*mm, leftMargin=16*mm, topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet(); styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=8.5, leading=11)); styles.add(ParagraphStyle(name="Question", parent=styles["Heading3"], fontSize=10.5, leading=14, spaceBefore=8, spaceAfter=4))
    story = [Paragraph(escape(title), styles["Title"]), Spacer(1, 5*mm), Paragraph(escape(f"Questions: {len(rows)} | Generated by RATHOD HUB"), styles["Small"]), Spacer(1, 4*mm)]
    for i, q in enumerate(rows, 1):
        story.append(Paragraph(escape(f"{i}. {q['question']}"), styles["Question"]))
        for j, option in enumerate(q["options"]):
            story.append(Paragraph(escape(f"{chr(65+j)}. {option}"), styles["Small"]))
        if include_answers:
            answer = "Not available" if q.get("correct_index") is None else chr(65 + int(q["correct_index"]))
            story.append(Paragraph(escape(f"Answer: {answer} | {q.get('explanation') or ''}"), styles["Small"]))
        story.append(Spacer(1, 2*mm))
    doc.build(story); return out.getvalue()


def fetch_rows(start: datetime, end: datetime) -> list[dict]:
    params = {"select": "id,event_type,payload,created_at", "created_at": f"gte.{start.isoformat()}", "order": "created_at.asc", "limit": "2000"}
    rows = rest("GET", "rh_bridge_events", params) or []
    result = []
    for row in rows:
        try:
            created = datetime.fromisoformat(str(row.get("created_at", "")).replace("Z", "+00:00"))
        except ValueError:
            continue
        if created >= end or is_daily(row):
            continue
        if row.get("event_type") not in {"quiz_question", "question_solved", "quiz_item"}:
            continue
        q = question_from(row)
        if q:
            q["event_id"] = row.get("id"); result.append(q)
    unique = {}; [unique.setdefault((q["question"], q["mode"]), q) for q in result]
    return list(unique.values())


def run_once() -> None:
    now = datetime.now(timezone.utc); start, end = batch_dates(now); rows = fetch_rows(start, end)
    if not rows:
        log.info("No archive questions for %s to %s", start.date(), (end-timedelta(days=1)).date()); return
    token = access_token(); start_text = start.strftime("%d-%b"); end_text = (end-timedelta(days=1)).strftime("%d-%b-%Y")
    notes_name = f"Notes_{start_text}_to_{end_text}.pdf"; tests_name = f"Test_{start_text}_to_{end_text}.pdf"
    if NOTES_FOLDER:
        info = upload_or_update(token, NOTES_FOLDER, notes_name, make_pdf(f"RATHOD HUB Notes — {start_text} to {end_text}", rows, True)); log.info("Notes archive ready: %s", info["url"])
    if TESTS_FOLDER:
        info = upload_or_update(token, TESTS_FOLDER, tests_name, make_pdf(f"RATHOD HUB Test Bank — {start_text} to {end_text}", rows, False)); log.info("Test archive ready: %s", info["url"])


def main() -> None:
    required = (SUPA_URL, SUPA_KEY, CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN)
    if not all(required): raise SystemExit("Supabase and Google Drive OAuth variables are required")
    while True:
        try: run_once()
        except Exception: log.exception("Archive pass failed")
        time.sleep(POLL_SECONDS)

if __name__ == "__main__": main()
