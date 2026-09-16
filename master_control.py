"""Fail-safe cached reader for the RATHOD central service locker."""
from __future__ import annotations
import json,logging,os,time
from urllib import parse,request
log=logging.getLogger("rathod-master-control")
URL=os.getenv("SUPABASE_URL","").rstrip("/"); KEY=os.getenv("SUPABASE_SERVICE_ROLE_KEY","")
_cache=None; _at=0.0
FIELDS={"hub":"hub_enabled","quiz_bot":"quiz_bot_enabled","sakhi":"sakhi_enabled","pdf_worker":"pdf_worker_enabled"}
def state(force=False):
 global _cache,_at
 if not force and _cache is not None and time.time()-_at<15:return _cache
 if not URL or not KEY:return {"master_enabled":True,"hub_enabled":True,"quiz_bot_enabled":True,"sakhi_enabled":True,"pdf_worker_enabled":True}
 try:
  q=parse.urlencode({"select":"master_enabled,hub_enabled,quiz_bot_enabled,sakhi_enabled,pdf_worker_enabled,maintenance_message","id":"eq.global","limit":"1"})
  req=request.Request(f"{URL}/rest/v1/rh_system_control?{q}",headers={"apikey":KEY,"Authorization":f"Bearer {KEY}","Accept":"application/json"})
  with request.urlopen(req,timeout=8) as r:rows=json.loads(r.read().decode() or "[]")
  if rows:_cache=rows[0];_at=time.time()
 except Exception as exc:
  log.warning("Master control unavailable; preserving current service state: %s",str(exc)[:140])
 return _cache or {"master_enabled":True,"hub_enabled":True,"quiz_bot_enabled":True,"sakhi_enabled":True,"pdf_worker_enabled":True}
def is_enabled(service):
 s=state();return bool(s.get("master_enabled",True) and s.get(FIELDS.get(service,service),True))
def message():return str(state().get("maintenance_message") or "System maintenance चल रहा है।")
