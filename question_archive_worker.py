"""Build four-day Notes/Test PDFs from quiz_question bridge events and keep them in Drive."""
from __future__ import annotations
import io,json,logging,os,re,time
from datetime import datetime,timedelta,timezone
from html import escape
from urllib import parse,request
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s",level=logging.INFO)
log=logging.getLogger("rathod-question-archive")
SUPA_URL=os.getenv("SUPABASE_URL","").rstrip("/"); SUPA_KEY=os.getenv("SUPABASE_SERVICE_ROLE_KEY","")
CLIENT_ID=os.getenv("GOOGLE_CLIENT_ID","").strip(); CLIENT_SECRET=os.getenv("GOOGLE_CLIENT_SECRET","").strip(); REFRESH_TOKEN=os.getenv("GOOGLE_REFRESH_TOKEN","").strip()
NOTES_FOLDER=os.getenv("DRIVE_FOLDER_QUESTION_NOTES","").strip(); TESTS_FOLDER=os.getenv("DRIVE_FOLDER_QUESTION_TESTS","").strip(); POLL_SECONDS=max(60,int(os.getenv("ARCHIVE_POLL_SECONDS","120")))
FONT_NAME="RathodDevanagari"; FONT_PATH="/tmp/NotoSansDevanagari-Regular.ttf"

def ensure_hindi_font():
    try:
        if FONT_NAME not in pdfmetrics.getRegisteredFontNames():
            if not os.path.exists(FONT_PATH):
                css_req=request.Request("https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@400&display=swap",headers={"User-Agent":"Mozilla/5.0"})
                css=request.urlopen(css_req,timeout=30).read().decode("utf-8")
                blocks=re.findall(r"@font-face\\s*\\{(.*?)\\}",css,re.S)
                url=None
                for block in blocks:
                    if "U+0900" in block or "U+0901" in block:
                        match=re.search(r"url\\((https://fonts\\.gstatic\\.com/[^)]+)\\)",block)
                        if match:url=match.group(1);break
                if not url:
                    match=re.search(r"url\\((https://fonts\\.gstatic\\.com/[^)]+)\\)",css)
                    url=match.group(1) if match else None
                if not url: raise RuntimeError("Noto Devanagari font URL not found")
                with request.urlopen(request.Request(url,headers={"User-Agent":"Mozilla/5.0"}),timeout=60) as r:
                    open(FONT_PATH,"wb").write(r.read())
            pdfmetrics.registerFont(TTFont(FONT_NAME,FONT_PATH))
            log.info("Hindi PDF font ready")
        return FONT_NAME
    except Exception as exc:
        log.warning("Hindi font unavailable; PDF will use fallback font: %s",str(exc)[:180])
        return "Helvetica"

def rest(method,table,params=None,body=None):
    if not SUPA_URL or not SUPA_KEY: raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")
    url=f"{SUPA_URL}/rest/v1/{table}"+("?"+parse.urlencode(params,safe="(),.*") if params else "")
    headers={"apikey":SUPA_KEY,"Authorization":f"Bearer {SUPA_KEY}","Content-Type":"application/json","Accept":"application/json"}; data=None if body is None else json.dumps(body).encode()
    with request.urlopen(request.Request(url,data=data,headers=headers,method=method),timeout=30) as r:
        text=r.read().decode(); return json.loads(text) if text else None

def token():
    if not all((CLIENT_ID,CLIENT_SECRET,REFRESH_TOKEN)): raise RuntimeError("Google Drive OAuth variables are missing")
    body=parse.urlencode({"client_id":CLIENT_ID,"client_secret":CLIENT_SECRET,"refresh_token":REFRESH_TOKEN,"grant_type":"refresh_token"}).encode()
    with request.urlopen(request.Request("https://oauth2.googleapis.com/token",data=body,headers={"Content-Type":"application/x-www-form-urlencoded"},method="POST"),timeout=25) as r: data=json.loads(r.read().decode())
    if not data.get("access_token"): raise RuntimeError("Google OAuth refresh failed")
    return str(data["access_token"])

def drive(method,url,access,body=None,content_type=None):
    headers={"Authorization":f"Bearer {access}"}
    if content_type: headers["Content-Type"]=content_type
    with request.urlopen(request.Request(url,data=body,headers=headers,method=method),timeout=60) as r:
        text=r.read().decode(); return json.loads(text) if text else {}

def find_file(access,folder,name):
    safe=name.replace("'","\\'"); q=f"'{folder}' in parents and name = '{safe}' and trashed = false"; params=parse.urlencode({"q":q,"fields":"files(id,name,webViewLink)","pageSize":"10"})
    data=drive("GET","https://www.googleapis.com/drive/v3/files?"+params,access); files=data.get("files") or []; return files[0] if files else None

def upload_or_update(access,folder,name,pdf):
    old=find_file(access,folder,name)
    if old:
        url="https://www.googleapis.com/upload/drive/v3/files/"+str(old["id"])+"?uploadType=media&fields=id,name,webViewLink"; data=drive("PATCH",url,access,pdf,"application/pdf"); file_id=str(data.get("id") or old["id"])
    else:
        boundary="rathodarchiveboundary"; meta=json.dumps({"name":name,"parents":[folder]}).encode(); body=b"--"+boundary.encode()+b"\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n"+meta+b"\r\n--"+boundary.encode()+b"\r\nContent-Type: application/pdf\r\n\r\n"+pdf+b"\r\n--"+boundary.encode()+b"--\r\n"; data=drive("POST","https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,webViewLink",access,body,"multipart/related; boundary="+boundary); file_id=str(data.get("id") or "")
    if not file_id: raise RuntimeError("Drive did not return a file ID")
    return "https://drive.google.com/file/d/"+file_id+"/view?usp=sharing"

def window(now):
    start=now.replace(day=((now.day-1)//4)*4+1,hour=0,minute=0,second=0,microsecond=0); return start,start+timedelta(days=4)

def is_daily(row):
    p=row.get("payload") if isinstance(row.get("payload"),dict) else {}; text=" ".join(str(p.get(k,"")) for k in ("source","mode","quiz_name","event_type")).lower(); return any(x in text for x in ("daily event","daily 9 pm","daily_9pm","dailyevent"))

def extract(row):
    p=row.get("payload") if isinstance(row.get("payload"),dict) else {}; q=str(p.get("question") or "").strip(); opts=p.get("options")
    if not q or not isinstance(opts,list) or len(opts)!=4:return None
    try: correct=int(p.get("correct_index")) if p.get("correct_index") is not None else None
    except (TypeError,ValueError): correct=None
    return {"question":q,"options":[str(x) for x in opts],"correct_index":correct,"mode":str(p.get("mode") or "Quiz")}

def make_pdf(title,rows,answers):
    font=ensure_hindi_font(); out=io.BytesIO(); doc=SimpleDocTemplate(out,pagesize=A4,rightMargin=16*mm,leftMargin=16*mm,topMargin=15*mm,bottomMargin=15*mm); styles=getSampleStyleSheet(); styles.add(ParagraphStyle(name="RATitle",parent=styles["Title"],fontName=font)); styles.add(ParagraphStyle(name="RA",parent=styles["BodyText"],fontName=font,fontSize=8.5,leading=12)); styles.add(ParagraphStyle(name="RQ",parent=styles["Heading3"],fontName=font,fontSize=10.5,leading=14,spaceBefore=8,spaceAfter=4)); story=[Paragraph(escape(title),styles["RATitle"]),Spacer(1,5*mm),Paragraph(escape(f"Questions: {len(rows)} | RATHOD HUB archive"),styles["RA"])]
    for n,q in enumerate(rows,1):
        story.append(Paragraph(escape(f"{n}. [{q['mode']}] {q['question']}"),styles["RQ"])); [story.append(Paragraph(escape(f"{chr(65+i)}. {o}"),styles["RA"])) for i,o in enumerate(q["options"])]
        if answers:
            answer="Not available" if q["correct_index"] is None else chr(65+q["correct_index"])
            story.append(Paragraph(escape("Answer: "+answer),styles["RA"]))
    doc.build(story); return out.getvalue()

def rows_for(start,end):
    raw=rest("GET","rh_bridge_events",{"select":"id,event_type,payload,created_at","created_at":f"gte.{start.isoformat()}","order":"created_at.asc","limit":"2000"}) or []; unique={}
    for row in raw:
        try: created=datetime.fromisoformat(str(row.get("created_at","")).replace("Z","+00:00"))
        except ValueError: continue
        if created>=end or is_daily(row) or row.get("event_type") not in {"quiz_question","quiz_item","question_solved"}: continue
        q=extract(row)
        if q: unique.setdefault((q["question"],q["mode"]),q)
    return list(unique.values())

def run_once():
    start,end=window(datetime.now(timezone.utc)); rows=rows_for(start,end)
    if not rows: log.info("No questions in %s-%s",start.date(),(end-timedelta(days=1)).date()); return
    access=token(); label=start.strftime("%d-%b")+"_to_"+(end-timedelta(days=1)).strftime("%d-%b-%Y")
    if NOTES_FOLDER: log.info("Notes PDF: %s",upload_or_update(access,NOTES_FOLDER,"Notes_"+label+".pdf",make_pdf("RATHOD HUB Notes - "+label,rows,True)))
    if TESTS_FOLDER: log.info("Test PDF: %s",upload_or_update(access,TESTS_FOLDER,"Test_"+label+".pdf",make_pdf("RATHOD HUB Test Bank - "+label,rows,False)))

def main():
    if not all((SUPA_URL,SUPA_KEY,CLIENT_ID,CLIENT_SECRET,REFRESH_TOKEN)): raise SystemExit("Supabase and Google Drive OAuth variables are required")
    while True:
        try: run_once()
        except Exception: log.exception("Archive pass failed")
        time.sleep(POLL_SECONDS)
if __name__=="__main__": main()
