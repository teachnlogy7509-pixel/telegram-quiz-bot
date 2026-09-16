"""Process RATHOD HUB song uploads.

The static app places an MP4 in the private Supabase queue. This worker uses
FFmpeg to create an MP3, mirrors it to public Supabase Storage for reliable
browser playback, and archives the same MP3 in Google Drive.
"""
from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from urllib import error, parse, request

import master_control

log = logging.getLogger("rathod-song-library")
SUPA_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPA_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SONG_FOLDER = os.getenv("DRIVE_FOLDER_SONGS", "").strip()
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN", "").strip()
UPLOAD_BUCKET = "rh-song-uploads"
AUDIO_BUCKET = "rh-song-audio"


def _headers(content_type: str | None = None) -> dict[str, str]:
    headers = {
        "apikey": SUPA_KEY,
        "Authorization": f"Bearer {SUPA_KEY}",
        "Accept": "application/json",
    }
    if content_type:
        headers["Content-Type"] = content_type
    return headers


def _http(method: str, url: str, body: bytes | None = None, headers: dict[str, str] | None = None):
    req = request.Request(url, data=body, headers=headers or {}, method=method)
    try:
        with request.urlopen(req, timeout=60) as response:
            raw = response.read()
        return raw
    except error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:500]
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc


def _rest(method: str, table: str, params: dict[str, str] | None = None, body: dict | None = None):
    url = f"{SUPA_URL}/rest/v1/{table}"
    if params:
        url += "?" + parse.urlencode(params, safe="(),.*")
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = _headers("application/json")
    if method in {"POST", "PATCH"}:
        headers["Prefer"] = "return=representation"
    raw = _http(method, url, data, headers)
    if not raw:
        return []
    return json.loads(raw.decode("utf-8"))


def _storage_download(bucket: str, path: str) -> bytes:
    url = f"{SUPA_URL}/storage/v1/object/{bucket}/{parse.quote(path, safe='/')}"
    return _http("GET", url, headers=_headers())


def _storage_upload(bucket: str, path: str, data: bytes, content_type: str) -> None:
    url = f"{SUPA_URL}/storage/v1/object/{bucket}/{parse.quote(path, safe='/')}"
    headers = _headers(content_type)
    headers["x-upsert"] = "true"
    _http("POST", url, data, headers)


def _safe_name(value: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9._-]+", "_", value).strip("._")
    return (clean[:100] or "song")


def _google_token() -> str:
    if not all((CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN)):
        raise RuntimeError("Google OAuth variables are missing")
    body = parse.urlencode({
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type": "refresh_token",
    }).encode()
    data = json.loads(_http(
        "POST",
        "https://oauth2.googleapis.com/token",
        body,
        {"Content-Type": "application/x-www-form-urlencoded"},
    ).decode("utf-8"))
    if not data.get("access_token"):
        raise RuntimeError("Google OAuth refresh failed")
    return str(data["access_token"])


def _drive_request(method: str, url: str, token: str, body: bytes | None = None, content_type: str | None = None):
    headers = {"Authorization": f"Bearer {token}"}
    if content_type:
        headers["Content-Type"] = content_type
    return _http(method, url, body, headers)


def _drive_upload(token: str, title: str, data: bytes) -> tuple[str, str]:
    boundary = "rathodsongboundary"
    name = "RATHOD_HUB_SONG_" + _safe_name(title) + ".mp3"
    metadata = json.dumps({"name": name, "parents": [SONG_FOLDER]}, ensure_ascii=False).encode("utf-8")
    body = (
        b"--" + boundary.encode() + b"\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n"
        + metadata
        + b"\r\n--" + boundary.encode() + b"\r\nContent-Type: audio/mpeg\r\n\r\n"
        + data
        + b"\r\n--" + boundary.encode() + b"--\r\n"
    )
    response = json.loads(_drive_request(
        "POST",
        "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,webViewLink",
        token,
        body,
        "multipart/related; boundary=" + boundary,
    ).decode("utf-8"))
    file_id = str(response.get("id") or "")
    if not file_id:
        raise RuntimeError("Google Drive did not return a song file ID")
    try:
        _drive_request(
            "POST",
            f"https://www.googleapis.com/drive/v3/files/{file_id}/permissions?fields=id",
            token,
            json.dumps({"type": "anyone", "role": "reader"}).encode("utf-8"),
            "application/json",
        )
    except Exception as exc:
        log.warning("Song uploaded but Drive sharing failed: %s", str(exc)[:180])
    return file_id, f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"


def _update(song_id: str, values: dict) -> None:
    _rest("PATCH", "rh_song_library", {"id": f"eq.{song_id}"}, values)


def _convert(source: bytes, suffix: str = ".mp4") -> bytes:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg is not installed on Railway")
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
            raise RuntimeError((result.stderr or "FFmpeg conversion failed")[-600:])
        with open(output_path, "rb") as handle:
            return handle.read()


def process_once() -> None:
    if not master_control.is_enabled("pdf_worker"):
        return
    if not SUPA_URL or not SUPA_KEY or not SONG_FOLDER:
        return
    rows = _rest("GET", "rh_song_library", {
        "select": "id,title,source_bucket,source_path,source_type",
        "status": "eq.queued",
        "order": "created_at.asc",
        "limit": "3",
    }) or []
    for row in rows:
        song_id = str(row.get("id") or "")
        if not song_id:
            continue
        claimed = _rest("PATCH", "rh_song_library", {"id": f"eq.{song_id}", "status": "eq.queued"}, {
            "status": "processing",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }) or []
        if not claimed:
            continue
        try:
            source = _storage_download(str(row.get("source_bucket") or UPLOAD_BUCKET), str(row["source_path"]))
            audio = _convert(source, ".mp4" if str(row.get("source_type") or "").endswith("mp4") else ".bin")
            audio_path = f"songs/{song_id}.mp3"
            _storage_upload(AUDIO_BUCKET, audio_path, audio, "audio/mpeg")
            drive_id, drive_url = _drive_upload(_google_token(), str(row.get("title") or "RATHOD HUB Song"), audio)
            audio_url = f"{SUPA_URL}/storage/v1/object/public/{AUDIO_BUCKET}/{parse.quote(audio_path, safe='/')}"
            _update(song_id, {
                "status": "ready",
                "audio_url": audio_url,
                "drive_file_id": drive_id,
                "drive_url": drive_url,
                "error_message": None,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })
            log.info("Song ready: %s", row.get("title"))
        except Exception as exc:
            log.exception("Song conversion failed for %s", song_id)
            try:
                _update(song_id, {
                    "status": "error",
                    "error_message": str(exc)[:1000],
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                })
            except Exception:
                log.exception("Could not mark song as error: %s", song_id)
