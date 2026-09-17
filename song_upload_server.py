"""Authenticated Railway endpoint for RATHOD HUB songs.

Uploads are converted to MP3 and stored in Google Drive. The API also proxies
Drive media with byte-range support so the browser audio player can seek and
change volume normally, and lets the verified owner delete a song.
"""
from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import error, parse, request

import master_control

log = logging.getLogger("rathod-song-upload-api")
OWNER_EMAILS = frozenset({"ashisharmy1982@gmail.com", "teachnlogy7509@gmail.com"})
MAX_BYTES = 250 * 1024 * 1024
SUPA_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPA_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SONG_FOLDER = os.getenv("DRIVE_FOLDER_SONGS", "").strip()
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN", "").strip()
_server = None


def _http(method: str, url: str, body: bytes | None = None, headers: dict | None = None, timeout: int = 60) -> bytes:
    try:
        with request.urlopen(request.Request(url, data=body, headers=headers or {}, method=method), timeout=timeout) as response:
            return response.read()
    except error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:700]
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc


def _rest(method: str, table: str, params: dict | None = None, body: dict | None = None):
    if not SUPA_URL or not SUPA_KEY:
        raise RuntimeError("SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY is missing")
    url = f"{SUPA_URL}/rest/v1/{table}"
    if params:
        url += "?" + parse.urlencode(params, safe="(),.*")
    headers = {
        "apikey": SUPA_KEY,
        "Authorization": "Bearer " + SUPA_KEY,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if method in {"POST", "PATCH", "DELETE"}:
        headers["Prefer"] = "return=representation"
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    raw = _http(method, url, data, headers)
    return json.loads(raw.decode("utf-8")) if raw else []


def _auth_user(token: str) -> dict:
    if not SUPA_URL or not SUPA_KEY:
        raise RuntimeError("Supabase service configuration missing")
    raw = _http(
        "GET",
        f"{SUPA_URL}/auth/v1/user",
        headers={
            "apikey": SUPA_KEY,
            "Authorization": "Bearer " + token,
            "Accept": "application/json",
        },
    )
    user = json.loads(raw.decode("utf-8"))
    email = str(user.get("email") or "").strip().lower()
    if email not in OWNER_EMAILS:
        raise PermissionError("Only the RATHOD HUB owner can manage songs")
    return user


def _google_token() -> str:
    if not all((CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN)):
        raise RuntimeError("Google OAuth variables are missing")
    body = parse.urlencode({
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type": "refresh_token",
    }).encode()
    raw = _http(
        "POST",
        "https://oauth2.googleapis.com/token",
        body,
        {"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    data = json.loads(raw.decode("utf-8"))
    if not data.get("access_token"):
        raise RuntimeError("Google OAuth refresh failed")
    return str(data["access_token"])


def _drive_upload(token: str, title: str, data: bytes) -> tuple[str, str]:
    if not SONG_FOLDER:
        raise RuntimeError("DRIVE_FOLDER_SONGS is not configured on the PDF worker")
    boundary = "rathodsongboundary"
    safe_title = "".join(ch if ch.isalnum() or ch in " ._-" else "_" for ch in title).strip()[:100] or "song"
    metadata = json.dumps({"name": "RATHOD_HUB_SONG_" + safe_title + ".mp3", "parents": [SONG_FOLDER]}, ensure_ascii=False).encode("utf-8")
    body = (
        b"--" + boundary.encode() + b"\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n"
        + metadata
        + b"\r\n--" + boundary.encode() + b"\r\nContent-Type: audio/mpeg\r\n\r\n"
        + data
        + b"\r\n--" + boundary.encode() + b"--\r\n"
    )
    raw = _http(
        "POST",
        "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,webViewLink",
        body,
        {"Authorization": "Bearer " + token, "Content-Type": "multipart/related; boundary=" + boundary},
        timeout=120,
    )
    response = json.loads(raw.decode("utf-8"))
    file_id = str(response.get("id") or "")
    if not file_id:
        raise RuntimeError("Google Drive did not return a song file ID")
    permission_url = "https://www.googleapis.com/drive/v3/files/" + parse.quote(file_id, safe="") + "/permissions?fields=id"
    try:
        _http(
            "POST",
            permission_url,
            json.dumps({"type": "anyone", "role": "reader"}).encode("utf-8"),
            {"Authorization": "Bearer " + token, "Content-Type": "application/json"},
            timeout=30,
        )
    except Exception as exc:
        log.warning("Song uploaded but Drive sharing failed: %s", str(exc)[:180])
    return file_id, "https://drive.google.com/file/d/" + parse.quote(file_id, safe="") + "/view?usp=sharing"


def _ffmpeg_binary() -> str:
    binary = shutil.which("ffmpeg")
    if binary:
        return binary
    try:
        import imageio_ffmpeg
        embedded = imageio_ffmpeg.get_ffmpeg_exe()
        if embedded and os.path.exists(embedded):
            return embedded
    except Exception as exc:
        log.warning("Embedded FFmpeg fallback unavailable: %s", str(exc)[:180])
    raise RuntimeError("FFmpeg is not installed on Railway")


def _convert(source: bytes, suffix: str) -> bytes:
    ffmpeg = _ffmpeg_binary()
    with tempfile.TemporaryDirectory(prefix="rathod-song-") as directory:
        source_path = os.path.join(directory, "source" + suffix)
        output_path = os.path.join(directory, "song.mp3")
        with open(source_path, "wb") as handle:
            handle.write(source)
        result = subprocess.run(
            [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", source_path,
             "-vn", "-codec:a", "libmp3lame", "-b:a", "192k", "-ar", "44100", output_path],
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode != 0 or not os.path.exists(output_path):
            raise RuntimeError((result.stderr or "FFmpeg conversion failed")[-700:])
        with open(output_path, "rb") as handle:
            return handle.read()


def _parse_multipart(content_type: str, body: bytes) -> tuple[dict[str, str], tuple[str, bytes] | None]:
    """Minimal multipart/form-data parser; cgi was removed in Python 3.13."""
    match = re.search(r"boundary=(?:\"([^\"]+)\"|([^;]+))", content_type, re.I)
    if not match:
        raise ValueError("multipart boundary is missing")
    boundary = (match.group(1) or match.group(2)).strip().encode("utf-8")
    delimiter = b"--" + boundary
    fields: dict[str, str] = {}
    upload: tuple[str, bytes] | None = None
    for chunk in body.split(delimiter)[1:]:
        if chunk.startswith(b"--"):
            break
        if chunk.startswith(b"\r\n"):
            chunk = chunk[2:]
        if b"\r\n\r\n" not in chunk:
            continue
        raw_headers, payload = chunk.split(b"\r\n\r\n", 1)
        if payload.endswith(b"\r\n"):
            payload = payload[:-2]
        header_text = raw_headers.decode("latin-1")
        disposition = re.search(r"content-disposition:\s*form-data;([^\r\n]+)", header_text, re.I)
        if not disposition:
            continue
        params = dict(re.findall(r"(name|filename)=\"([^\"]*)\"", disposition.group(1), re.I))
        name = params.get("name", "")
        if name == "file":
            upload = (params.get("filename") or "song.bin", payload)
        elif name:
            fields[name] = payload.decode("utf-8", errors="replace")
    return fields, upload


def _public_base_url() -> str:
    explicit = str(os.getenv("SONG_PUBLIC_BASE_URL") or os.getenv("PUBLIC_BASE_URL") or "").strip().rstrip("/")
    if explicit:
        return explicit
    domain = str(os.getenv("RAILWAY_PUBLIC_DOMAIN") or "").strip().strip("/")
    return ("https://" + domain) if domain else ""


def _audio_url(file_id: str) -> str:
    base = _public_base_url()
    if base:
        return base + "/song/audio/" + parse.quote(file_id, safe="")
    return "https://drive.google.com/uc?export=download&id=" + parse.quote(file_id, safe="")


def _process(title: str, filename: str, content: bytes, user: dict) -> dict:
    if not master_control.is_enabled("pdf_worker"):
        raise RuntimeError("Song worker is paused by master control")
    lower = filename.lower()
    suffix = ".mp4" if lower.endswith(".mp4") else ".m4a" if lower.endswith(".m4a") else ".mp3" if lower.endswith(".mp3") else ".bin"
    audio = _convert(content, suffix)
    drive_id, drive_url = _drive_upload(_google_token(), title, audio)
    audio_url = _audio_url(drive_id)
    rows = _rest("POST", "rh_song_library", body={
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


def _delete_song(song_id: str) -> None:
    if not re.fullmatch(r"[0-9a-fA-F-]{16,}", song_id):
        raise ValueError("Invalid song id")
    rows = _rest("GET", "rh_song_library", params={"id": "eq." + song_id, "select": "id,drive_file_id"}) or []
    if not rows:
        raise FileNotFoundError("Song not found")
    drive_id = str(rows[0].get("drive_file_id") or "").strip()
    if drive_id:
        try:
            _http(
                "DELETE",
                "https://www.googleapis.com/drive/v3/files/" + parse.quote(drive_id, safe=""),
                headers={"Authorization": "Bearer " + _google_token()},
                timeout=45,
            )
        except RuntimeError as exc:
            if "HTTP 404" not in str(exc):
                raise
    _rest("DELETE", "rh_song_library", params={"id": "eq." + song_id})


def _drive_media_response(file_id: str, range_header: str | None = None):
    if not re.fullmatch(r"[A-Za-z0-9_-]{8,}", file_id):
        raise ValueError("Invalid Drive file id")
    headers = {"Authorization": "Bearer " + _google_token()}
    if range_header:
        headers["Range"] = range_header
    url = "https://www.googleapis.com/drive/v3/files/" + parse.quote(file_id, safe="") + "?alt=media"
    return request.urlopen(request.Request(url, headers=headers, method="GET"), timeout=120)


class Handler(BaseHTTPRequestHandler):
    server_version = "RATHOD-HUB-SongAPI/4.0"

    def _headers(self, content_type: str = "application/json") -> None:
        origin = os.getenv("SONG_CORS_ORIGIN", "*")
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, Range")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Expose-Headers", "Accept-Ranges, Content-Length, Content-Range, Content-Type")
        self.send_header("Vary", "Origin")
        self.send_header("Content-Type", content_type)

    def _json(self, status: int, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._headers()
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def _stream_audio(self, file_id: str, head_only: bool = False) -> None:
        upstream = None
        try:
            upstream = _drive_media_response(file_id, self.headers.get("Range"))
            status = int(getattr(upstream, "status", 200) or 200)
            content_length = upstream.headers.get("Content-Length")
            content_range = upstream.headers.get("Content-Range")
            self.send_response(status)
            self._headers("audio/mpeg")
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Cache-Control", "public, max-age=300")
            if content_length:
                self.send_header("Content-Length", content_length)
            if content_range:
                self.send_header("Content-Range", content_range)
            self.end_headers()
            if not head_only:
                while True:
                    chunk = upstream.read(256 * 1024)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
        except error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:400]
            self._json(exc.code, {"ok": False, "error": detail or "Drive audio unavailable"})
        except Exception as exc:
            self._json(502, {"ok": False, "error": str(exc)[:400]})
        finally:
            if upstream is not None:
                upstream.close()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._headers()
        self.end_headers()

    def do_HEAD(self) -> None:
        path = parse.urlsplit(self.path).path.rstrip("/")
        if path.startswith("/song/audio/"):
            self._stream_audio(path.rsplit("/", 1)[-1], head_only=True)
        else:
            self.send_response(404)
            self._headers()
            self.end_headers()

    def do_GET(self) -> None:
        path = parse.urlsplit(self.path).path.rstrip("/")
        if path == "/health":
            self._json(200, {"ok": True, "service": "rathod-song-upload", "media_proxy": True})
        elif path.startswith("/song/audio/"):
            self._stream_audio(path.rsplit("/", 1)[-1])
        else:
            self._json(404, {"ok": False, "error": "Not found"})

    def do_DELETE(self) -> None:
        path = parse.urlsplit(self.path).path.rstrip("/")
        if not path.startswith("/song/"):
            self._json(404, {"ok": False, "error": "Not found"})
            return
        song_id = path.rsplit("/", 1)[-1]
        try:
            auth = self.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                raise PermissionError("Supabase login token missing")
            _auth_user(auth[7:].strip())
            _delete_song(song_id)
            self._json(200, {"ok": True, "deleted": song_id})
        except PermissionError as exc:
            self._json(403, {"ok": False, "error": str(exc)})
        except FileNotFoundError as exc:
            self._json(404, {"ok": False, "error": str(exc)})
        except Exception as exc:
            log.exception("Song delete failed")
            self._json(500, {"ok": False, "error": str(exc)[:500]})

    def do_POST(self) -> None:
        if parse.urlsplit(self.path).path.rstrip("/") != "/song/upload":
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
            fields, upload = _parse_multipart(self.headers.get("Content-Type", ""), body)
            if upload is None:
                raise ValueError("file field is required")
            filename, content = upload
            title = str(fields.get("title") or filename.rsplit("/", 1)[-1].rsplit(".", 1)[0]).strip()[:120] or "RATHOD HUB Song"
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
