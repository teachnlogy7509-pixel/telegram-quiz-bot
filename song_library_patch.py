from pathlib import Path

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

worker = Path('question_archive_worker.py')
if worker.exists():
    source = worker.read_text()
    if 'import song_library_worker' not in source:
        if 'import master_control\n' in source:
            source = source.replace('import master_control\n', 'import master_control\nimport song_library_worker\n', 1)
        else:
            source = source.replace('from __future__ import annotations\n', 'from __future__ import annotations\n\nimport song_library_worker\n', 1)
    if 'song_library_worker.process_once()' not in source:
        source = source.replace('            run_once()\n', '            run_once()\n            song_library_worker.process_once()\n', 1)
    worker.write_text(source)

print('RATHOD HUB song queue connected to the PDF worker')
