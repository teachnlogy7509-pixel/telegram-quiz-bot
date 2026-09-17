from pathlib import Path

# Keep the old worker source importable if it is ever used by an existing queue,
# but repair malformed Drive URL literals before Python imports it.
song = Path('song_library_worker.py')
if song.exists():
    source = song.read_text()
    left = chr(123)
    right = chr(125)
    file_id_expr = left + 'file_id' + right
    good_permission = 'f"https://www.googleapis.com/drive/v3/files/' + file_id_expr + '/permissions?fields=id"'
    good_view = 'f"https://drive.google.com/file/d/' + file_id_expr + '/view?usp=sharing"'
    bad_permission = 'f"' + left * 2 + 'https://www.googleapis.com/drive/v3/files/' + file_id_expr + right * 2 + '/permissions?fields=id"'
    bad_view = 'f"' + left * 2 + 'https://drive.google.com/file/d/' + file_id_expr + right * 2 + '/view?usp=sharing"'
    source = source.replace(bad_permission, good_permission)
    source = source.replace(bad_view, good_view)
    song.write_text(source)

# Apply the same repair to the direct API source during the Railway build. This
# keeps older cached deployments from reintroducing the old owner gate or URL.
upload = Path('song_upload_server.py')
if upload.exists():
    source = upload.read_text()
    source = source.replace(
        'OWNER_EMAIL = "teachnlogy7509@gmail.com"',
        'OWNER_EMAILS = frozenset({"ashisharmy1982@gmail.com", "teachnlogy7509@gmail.com"})',
    )
    source = source.replace('if email != OWNER_EMAIL:', 'if email not in OWNER_EMAILS:')
    source = source.replace(
        'permission_url = f"{{https://www.googleapis.com/drive/v3/files/{file_id}}}/permissions?fields=id"',
        'permission_url = f"https://www.googleapis.com/drive/v3/files/{file_id}/permissions?fields=id"',
    )
    source = source.replace(
        'return file_id, f"{{https://drive.google.com/file/d/{file_id}}}/view?usp=sharing"',
        'return file_id, f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"',
    )
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

print('RATHOD HUB direct Google Drive song API connected')
