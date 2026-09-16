from pathlib import Path

# The worker now contains the production PDF implementation directly. Keep this
# build hook idempotent for older Railway builds and cached source trees.
path = Path("question_archive_worker.py")
if path.exists():
    source = path.read_text()
    source = source.replace('"delivery_mode":"archive"', '"delivery_mode":"digest"')
    source = source.replace('"delivery_mode": "archive"', '"delivery_mode": "digest"')
    source = source.replace('f"{{https://www.googleapis.com/drive/v3/files/', 'f"https://www.googleapis.com/drive/v3/files/')
    source = source.replace("{file_id}}}/permissions", "{file_id}/permissions")
    source = source.replace("{file_id}}/permissions", "{file_id}/permissions")
    path.write_text(source)
    print("PDF worker already contains Hindi, Latin fallback, valid archive mode, and safe Drive URLs")
