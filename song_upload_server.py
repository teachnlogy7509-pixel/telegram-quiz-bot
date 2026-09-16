"""Small authenticated HTTP endpoint for app-to-Google-Drive song uploads.

The app sends the Supabase access token and an MP4/MP3 multipart upload. The
worker verifies the owner through Supabase Auth, converts in Railway's
temporary disk, uploads only the final MP3 to Google Drive, and stores only
song metadata in Supabase. No Supabase Storage bucket is used by this path.
"""
from __future__ import annotations

import cgi
import io
import json
import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import error, request

import master_control
import song_library_worker as core

log = logging.getLogger("rathod-song-upload-api")
OWNER_EMAIL = "teachnlogy7509@gmail.com"
MAX_BYTES = 250 * 1024 * 1024
_server = None


def _auth_user(token: str) -> dict:
    if not core.SUPA_URL or not core.SUPA_KEY:
        raise RuntimeError("Supabase service configuration missing")
    raw = core._http(
        "GET",
        f"{core.SUPA_URL}/auth/v1/user",
        headers={
            "apikey": core.SUPA_KEY,
            "Authorization": "Bearer " + token,
            "Accept": "application/json",
        },
    )
    user = json.loads(raw.decode("utf-8"))
    email = str(user.get("email") or "").strip().lower()
    if email != OWNER_EMAIL:
        raise PermissionError("Only the RATHOD HUB owner can upload songs")
    return user


def _process(title: str, filename: str, content: bytes, user: dict) -> dict:
    if not master_control.is_enabled("pdf_worker"):
        raise RuntimeError("Song worker is paused by master control")
    if not core.SONG_FOLDER:
        raise RuntimeError("DRIVE_FOLDER_SONGS is not configured on the PDF worker")
    suffix = ".mp4" if filename.lower().endswith(".mp4") else ".bin"
    audio = core._convert(content, suffix)
    drive_id, drive_url = core._drive_upload(core._google_token(), title, audio)
    audio_url = "https://drive.google.com/uc?export=download&id=" + drive_id
    rows = core._rest("POST", "rh_song_library", body={
        "title": title,
        "source_bucket": None,
        "source_path": None,
        "source_type": "audio/mpeg",
        "audio_url": audio_url,
        "drive_url": drive_url,
        "drive_file_id": drive_id,
        "status": "ready",
        "error_message": None,
        "uploaded_by": user.get("id"),
    }) or []
    return {
        "id": rows[0].get("id") if rows else None,
        "title": title,
        "audio_url": audio_url,
        "drive_url": drive_url,
        "drive_file_id": drive_id,
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "RATHOD-HUB-SongAPI/1.0"

    def _headers(self, content_type: str = "application/json") -> None:
        origin = os.getenv("SONG_CORS_ORIGIN", "*")
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Vary", "Origin")
        self.send_header("Content-Type", content_type)

    def _json(self, status: int, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._headers()
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._headers()
        self.end_headers()

    def do_GET(self) -> None:
        if self.path == "/health":
            self._json(200, {"ok": True, "service": "rathod-song-upload"})
        else:
            self._json(404, {"ok": False, "error": "Not found"})

    def do_POST(self) -> None:
        if self.path.rstrip("/") != "/song/upload":
            self._json(404, {"ok": False, "error": "Not found"})
            return
        try:
            auth = self.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                raise PermissionError("Supabase login token missing")
            user = _auth_user(auth[7:].strip())
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_BYTES:
                raise ValueError("Song file must be between 1 byte and 250 MB")
            body = self.rfile.read(length)
            form = cgi.FieldStorage(
                fp=io.BytesIO(body),
                headers=self.headers,
                environ={
                    "REQUEST_METHOD": "POST",
                    "CONTENT_TYPE": self.headers.get("Content-Type", ""),
                    "CONTENT_LENGTH": str(length),
                },
            )
            if "file" not in form:
                raise ValueError("file field is required")
            file_item = form["file"]
            filename = str(getattr(file_item, "filename", "") or "song.mp4")
            content = file_item.file.read()
            title = str(form.getfirst("title") or filename.rsplit("/", 1)[-1].rsplit(".", 1)[0]).strip()[:120]
            if not title:
                title = "RATHOD HUB Song"
            if not content:
                raise ValueError("Uploaded song is empty")
            result = _process(title, filename, content, user)
            self._json(200, {"ok": True, "song": result})
        except PermissionError as exc:
            self._json(403, {"ok": False, "error": str(exc)})
        except Exception as exc:
            log.exception("Song upload failed")
            self._json(500, {"ok": False, "error": str(exc)[:500]})

    def log_message(self, format: str, *args) -> None:
        log.info("%s - %s", self.address_string(), format % args)


def start() -> None:
    global _server
    if _server is not None:
        return
    port = int(os.getenv("PORT") or os.getenv("SONG_UPLOAD_PORT", "8080"))
    _server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    thread = threading.Thread(target=_server.serve_forever, name="rathod-song-upload-api", daemon=True)
    thread.start()
    log.info("Song upload API listening on port %s", port)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    start()
    threading.Event().wait()
