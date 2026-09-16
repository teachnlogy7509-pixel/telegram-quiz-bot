from pathlib import Path
p=Path('question_archive_worker.py');s=p.read_text()
def r(old,new):
 global s
 if new in s:return
 if old not in s:raise SystemExit('PDF shaping patch anchor missing')
 s=s.replace(old,new,1)
r('from urllib import parse,request','from urllib import parse,request,error')
r('TTFont(FONT_NAME,FONT_PATH)','TTFont(FONT_NAME,FONT_PATH,shapable=True)')
r('fontName=font));styles.add(ParagraphStyle(name="RA",parent=styles["BodyText"],fontName=font,fontSize=8.5,leading=12));styles.add(ParagraphStyle(name="RQ",parent=styles["Heading3"],fontName=font,fontSize=10.5,leading=14,spaceBefore=8,spaceAfter=4))','fontName=font,shaping=1));styles.add(ParagraphStyle(name="RA",parent=styles["BodyText"],fontName=font,fontSize=8.5,leading=12,shaping=1));styles.add(ParagraphStyle(name="RQ",parent=styles["Heading3"],fontName=font,fontSize=10.5,leading=14,spaceBefore=8,spaceAfter=4,shaping=1))')
r('escape(f"Questions: {len(rows)} | RATHOD HUB archive")','escape(f"कुल प्रश्न: {len(rows)} | RATHOD HUB संग्रह")')
r('escape(f"{chr(65+i)}. {o}")','escape(f"{(\'क\',\'ख\',\'ग\',\'घ\')[i]}. {o}")')
r('answer="Not available" if q["correct_index"] is None else chr(65+q["correct_index"]);story.append(Paragraph(escape("Answer: "+answer),styles["RA"]))','answer="उपलब्ध नहीं" if q["correct_index"] is None else ("क","ख","ग","घ")[q["correct_index"]];story.append(Paragraph(escape("सही उत्तर: "+answer),styles["RA"]))')
r('make_pdf("RATHOD HUB Notes - "+label,rows,True)','make_pdf("RATHOD HUB नोट्स - "+label,rows,True)')
r('make_pdf("RATHOD HUB Test Bank - "+label,rows,False)','make_pdf("RATHOD HUB टेस्ट प्रश्नपत्र - "+label,rows,False)')
# Log the real PostgREST response instead of a context-free HTTP 400.
r('with request.urlopen(request.Request(url,data=data,headers=headers,method=method),timeout=30) as r:text=r.read().decode();return json.loads(text) if text else None','try:\n        with request.urlopen(request.Request(url,data=data,headers=headers,method=method),timeout=30) as r:text=r.read().decode();return json.loads(text) if text else None\n    except error.HTTPError as exc:\n        detail=exc.read().decode(errors="replace")[:800]\n        raise RuntimeError(f"Supabase {method} {table} failed HTTP {exc.code}: {detail}") from exc')
# rh_bridge_events accepts immediate/digest only; archive links stay command-only as digest.
s=s.replace('"delivery_mode":"archive"','"delivery_mode":"digest"')
# Correct malformed Google Drive permissions endpoints.
s=s.replace('f"{{https://www.googleapis.com/drive/v3/files/{file_id}}}/permissions?fields=permissions(id,type,role)"','f"https://www.googleapis.com/drive/v3/files/{file_id}/permissions?fields=permissions(id,type,role)"')
s=s.replace('f"{{https://www.googleapis.com/drive/v3/files/{file_id}}}/permissions?fields=id"','f"https://www.googleapis.com/drive/v3/files/{file_id}/permissions?fields=id"')
# A Sakhi link-sync issue must never stop Notes/Test PDF generation or replacement.
r('if notes_url or test_url:publish_archive_links(label,notes_url,test_url)','if notes_url or test_url:\n        try:publish_archive_links(label,notes_url,test_url)\n        except Exception as exc:log.warning("PDFs updated, but Sakhi archive link sync failed: %s",str(exc)[:800])')
p.write_text(s)
print('Devanagari shaping and resilient archive sync enabled')
