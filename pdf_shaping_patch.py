from pathlib import Path

path = Path("question_archive_worker.py")
source = path.read_text()


def replace_once(old: str, new: str, label: str) -> None:
    global source
    if new in source:
        return
    if old not in source:
        raise SystemExit(f"PDF patch anchor missing: {label}")
    source = source.replace(old, new, 1)


replace_once(
    "from urllib import parse,request",
    "from urllib import parse,request,error",
    "urllib error logging",
)
replace_once(
    "TTFont(FONT_NAME,FONT_PATH)",
    "TTFont(FONT_NAME,FONT_PATH,shapable=True)",
    "Devanagari shaping",
)
replace_once(
    'FONT_NAME="RathodDevanagari"; FONT_PATH="/tmp/NotoSansDevanagari-Regular.ttf"',
    'FONT_NAME="RathodDevanagari"; FONT_PATH=next((p for p in ("/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf","/usr/share/fonts/opentype/noto/NotoSansDevanagari-Regular.ttf","/tmp/NotoSansDevanagari-Regular.ttf") if os.path.exists(p)), "/tmp/NotoSansDevanagari-Regular.ttf")',
    "system Hindi font",
)
replace_once(
    'fontName=font));styles.add(ParagraphStyle(name="RA",parent=styles["BodyText"],fontName=font,fontSize=8.5,leading=12));styles.add(ParagraphStyle(name="RQ",parent=styles["Heading3"],fontName=font,fontSize=10.5,leading=14,spaceBefore=8,spaceAfter=4))',
    'fontName=font,shaping=1));styles.add(ParagraphStyle(name="RA",parent=styles["BodyText"],fontName=font,fontSize=8.5,leading=12,shaping=1));styles.add(ParagraphStyle(name="RQ",parent=styles["Heading3"],fontName=font,fontSize=10.5,leading=14,spaceBefore=8,spaceAfter=4,shaping=1))',
    "Paragraph shaping",
)
replace_once(
    'escape(f"Questions: {len(rows)} | RATHOD HUB archive")',
    'escape(f"कुल प्रश्न: {len(rows)} | RATHOD HUB संग्रह")',
    "Hindi question label",
)
replace_once(
    'escape(f"{chr(65+i)}. {o}")',
    'escape(f"{(\'क\',\'ख\',\'ग\',\'घ\')[i]}. {o}")',
    "Hindi option labels",
)
replace_once(
    'answer="Not available" if q["correct_index"] is None else chr(65+q["correct_index"]);story.append(Paragraph(escape("Answer: "+answer),styles["RA"]))',
    'answer="उपलब्ध नहीं" if q["correct_index"] is None else ("क","ख","ग","घ")[q["correct_index"]];story.append(Paragraph(escape("सही उत्तर: "+answer),styles["RA"]))',
    "Hindi answer label",
)
replace_once(
    'make_pdf("RATHOD HUB Notes - "+label,rows,True)',
    'make_pdf("RATHOD HUB नोट्स - "+label,rows,True)',
    "Hindi notes title",
)
replace_once(
    'make_pdf("RATHOD HUB Test Bank - "+label,rows,False)',
    'make_pdf("RATHOD HUB टेस्ट प्रश्नपत्र - "+label,rows,False)',
    "Hindi test title",
)
replace_once(
    'with request.urlopen(request.Request(url,data=data,headers=headers,method=method),timeout=30) as r:text=r.read().decode();return json.loads(text) if text else None',
    'try:\n        with request.urlopen(request.Request(url,data=data,headers=headers,method=method),timeout=30) as r:text=r.read().decode();return json.loads(text) if text else None\n    except error.HTTPError as exc:\n        detail=exc.read().decode(errors="replace")[:800]\n        raise RuntimeError(f"Supabase {method} {table} failed HTTP {exc.code}: {detail}") from exc',
    "Supabase error details",
)
replace_once(
    'f"{{https://www.googleapis.com/drive/v3/files/{file_id}}}/permissions?fields=permissions(id,type,role)"',
    'f"https://www.googleapis.com/drive/v3/files/{file_id}/permissions?fields=permissions(id,type,role)"',
    "Google Drive permission read URL",
)
replace_once(
    'f"{{https://www.googleapis.com/drive/v3/files/{file_id}}}/permissions?fields=id"',
    'f"https://www.googleapis.com/drive/v3/files/{file_id}/permissions?fields=id"',
    "Google Drive permission write URL",
)
replace_once(
    'except Exception as exc:\n        log.exception("Hindi font unavailable; PDF will use fallback font: %s",str(exc)[:180]);return "Helvetica"',
    'except Exception as exc:\n        raise RuntimeError("Hindi Devanagari font unavailable; refusing to create an incorrectly rendered PDF") from exc',
    "Hindi font fail-fast",
)
replace_once(
    'if notes_url or test_url:publish_archive_links(label,notes_url,test_url)',
    'if notes_url or test_url:\n        try:publish_archive_links(label,notes_url,test_url)\n        except Exception as exc:log.warning("PDFs updated, but Sakhi archive link sync failed: %s",str(exc)[:800])',
    "resilient Sakhi link sync",
)

path.write_text(source)
print("Devanagari shaping, Drive URL, and archive resilience patches applied")
