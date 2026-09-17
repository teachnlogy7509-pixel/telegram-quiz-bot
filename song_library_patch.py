from pathlib import Path

left = chr(123)
right = chr(125)
file_id_expr = left + 'file_id' + right

# Keep the old worker source importable if it is ever used by an existing queue,
# but repair malformed Drive URL literals before Python imports it.
song = Path('song_library_worker.py')
if song.exists():
    source = song.read_text()
    permission_prefix = 'permission_url = f"'
    good_permission = permission_prefix + 'https://www.googleapis.com/drive/v3/files/' + file_id_expr + '/permissions?fields=id"'
    bad_permission = permission_prefix + left * 2 + 'https://www.googleapis.com/drive/v3/files/' + file_id_expr + right * 2 + '/permissions?fields=id"'
    good_view = 'return file_id, f"https://drive.google.com/file/d/' + file_id_expr + '/view?usp=sharing"'
    bad_view = 'return file_id, f"' + left * 2 + 'https://drive.google.com/file/d/' + file_id_expr + right * 2 + '/view?usp=sharing"'
    source = source.replace(bad_permission, good_permission)
    source = source.replace(bad_view, good_view)
    song.write_text(source)

# Apply the same repair and a pip-provided FFmpeg fallback to the direct API
# during the Railway build. This also repairs older cached source deployments.
upload = Path('song_upload_server.py')
if upload.exists():
    source = upload.read_text()
    source = source.replace(
        'OWNER_EMAIL = "teachnlogy7509@gmail.com"',
        'OWNER_EMAILS = frozenset({"ashisharmy1982@gmail.com", "teachnlogy7509@gmail.com"})',
    )
    source = source.replace('if email != OWNER_EMAIL:', 'if email not in OWNER_EMAILS:')

    # Repair both the old malformed literals and the temporary proxy rewrite.
    source = source.replace(
        left * 2 + 'https://www.googleapis.com/drive/v3/files/' + file_id_expr + right * 2,
        'https://www.googleapis.com/drive/v3/files/' + file_id_expr,
    )
    source = source.replace(
        left * 2 + 'https://drive.google.com/file/d/' + file_id_expr + right * 2,
        'https://drive.google.com/file/d/' + file_id_expr,
    )
    source = source.replace(
        '''    permission_url = f"{{https://www.googleapis.com/drive/v3/files/{parse.quote(file_id}}, safe='')}/permissions?fields=id"''',
        '''    permission_url = "https://www.googleapis.com/drive/v3/files/" + parse.quote(file_id, safe="") + "/permissions?fields=id"''',
    )
    source = source.replace(
        '''    return file_id, f"{{https://drive.google.com/file/d/{parse.quote(file_id}}, safe='')}/view?usp=sharing"''',
        '''    return file_id, "https://drive.google.com/file/d/" + parse.quote(file_id, safe="") + "/view?usp=sharing"''',
    )
    if 'def _ffmpeg_binary()' not in source:
        old_block = '''def _convert(source: bytes, suffix: str) -> bytes:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg is not installed on Railway")
'''
        new_block = '''def _ffmpeg_binary() -> str:
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
'''
        source = source.replace(old_block, new_block, 1)
    upload.write_text(source)

# The direct API is independent of the old Supabase-Storage polling worker.
# Inject only the API server into the archive worker so the PDF worker keeps its
# existing loop while also exposing /health and /song/upload.
worker = Path('question_archive_worker.py')
if worker.exists():
    source = worker.read_text()
    source = source.replace('import song_library_worker\n', '')
    if 'import song_upload_server\n' not in source:
        source = source.replace(
            'from __future__ import annotations\n',
            'from __future__ import annotations\n\nimport song_upload_server\n',
            1,
        )
    source = source.replace('            song_library_worker.process_once()\n', '')
    if 'song_upload_server.start()' not in source:
        source = source.replace('    while True:\n', '    song_upload_server.start()\n    while True:\n', 1)
    worker.write_text(source)

print('RATHOD HUB direct Google Drive song API connected with media proxy and FFmpeg fallback')
