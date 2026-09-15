"""Service-role event writer for Telegram question archiving."""
from __future__ import annotations
import json, os
from urllib import request

URL=(os.getenv("SUPABASE_URL","") or "").rstrip("/")
KEY=os.getenv("SUPABASE_SERVICE_ROLE_KEY","") or ""

def record_questions(topic: str, mode: str, questions: list[dict]) -> int:
    if not URL or not KEY or not questions:
        return 0
    topic_text=str(topic or "Quiz").strip()[:120]
    if any(x in topic_text.lower() for x in ("daily event","daily 9 pm","daily_9pm")):
        return 0
    rows=[]
    for q in questions:
        opts=q.get("options") if isinstance(q,dict) else None
        text=str(q.get("question") or "").strip() if isinstance(q,dict) else ""
        if not text or not isinstance(opts,list) or len(opts)!=4:
            continue
        rows.append({"event_type":"quiz_question","delivery_mode":"digest","display_name":"Telegram Quiz","payload":{"archive":True,"source":"Telegram","mode":str(mode or "Quiz"),"quiz_name":topic_text,"question":text,"options":[str(x) for x in opts],"correct_index":q.get("correct_index"),"explanation":str(q.get("explanation") or "")}})
    if not rows:
        return 0
    req=request.Request(f"{URL}/rest/v1/rh_bridge_events",data=json.dumps(rows).encode(),headers={"apikey":KEY,"Authorization":f"Bearer {KEY}","Content-Type":"application/json","Prefer":"return=minimal"},method="POST")
    with request.urlopen(req,timeout=25):
        pass
    return len(rows)
