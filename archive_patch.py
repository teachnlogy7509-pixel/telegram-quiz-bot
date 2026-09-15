from pathlib import Path

def replace_once(path, old, new):
    p=Path(path); text=p.read_text()
    if new in text:return
    if old not in text: raise SystemExit(f"Archive patch anchor missing: {path}")
    p.write_text(text.replace(old,new,1))

p=Path("quiz.py"); text=p.read_text()
if "import archive_sync" not in text:
    if "import supabase_sync\n" in text: text=text.replace("import supabase_sync\n","import supabase_sync\nimport archive_sync\n",1)
    else: raise SystemExit("quiz.py import anchor missing")
marker="    return accumulated[:count]\n\n\n# (rest of file unchanged from your current quiz logic)"
replacement="    result = accumulated[:count]\n    try:\n        await asyncio.to_thread(archive_sync.record_questions, topic, style, result)\n    except Exception as exc:\n        logger.warning(\"Question archive enqueue failed: %s\", str(exc)[:180])\n    return result\n\n\n# (rest of file unchanged from your current quiz logic)"
if marker in text:
    text=text.replace(marker,replacement,1)
else:
    marker2="    return accumulated[:count]\n\n\n# =====================\n# Voice (used by main.py)"
    replacement2="    result = accumulated[:count]\n    try:\n        await asyncio.to_thread(archive_sync.record_questions, topic, style, result)\n    except Exception as exc:\n        logger.warning(\"Question archive enqueue failed: %s\", str(exc)[:180])\n    return result\n\n\n# =====================\n# Voice (used by main.py)"
    if marker2 in text:text=text.replace(marker2,replacement2,1)
    else: raise SystemExit("quiz.py question-generation return anchor missing")
p.write_text(text)
print("Telegram question archive hook applied")
