"""Chat with the arena's supplier bots yourself, in a browser. Basic, local only.

Every session you open is a REAL practice session (one of the 200 per day), logged to notes/ui_sessions.txt.
The arena key stays on this machine; the page talks only to this server.

    cd tacto/starter-kit && .venv/bin/python ../../src/ui/chat_app.py      # http://127.0.0.1:8765
    # from the laptop:  ssh -N -L 8765:127.0.0.1:8765 macmini   then open http://localhost:8765

"Ask NoIdea" runs our agent on the current thread and fills the form with what it would send (nothing is sent
until you press Send). With LLM_* set in the environment the agent's model writes; otherwise code only.
"""
import json
import math
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "tacto/starter-kit"
sys.path.insert(0, str(KIT))
for line in (KIT / ".env").read_text().splitlines():  # same .env as the kit (ARENA_URL, ARENA_API_KEY, LLM_*)
    if "=" in line and not line.lstrip().startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

import uvicorn  # noqa: E402
from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.responses import HTMLResponse  # noqa: E402

from arena_kit.client import ArenaClient  # noqa: E402
from arena_kit.cost import total_cost  # noqa: E402
from arena_kit.docs import read_document, standard_terms  # noqa: E402

app = FastAPI()
client = ArenaClient()
CASES = {}      # case_id -> case file
SESSIONS = {}   # session_id -> {"case": case, "agent": NoIdeaAgent|None}
PROBES = {f.stem: json.loads(f.read_text()).get("result", {}) for f in (ROOT / "analysis/cases/openings").glob("*.json")}
PROBES["P01"] = {"c_open": 1153779.74, "c_best": 1096815.78}
LOG = ROOT / "notes/ui_sessions.txt"


def err(e):
    raise HTTPException(status_code=getattr(e, "status", 500), detail=str(getattr(e, "detail", e)))


def thread_with_text(sid, sup):
    """The thread with every attachment's text (the agent reads the quote PDF for standard terms)."""
    th = client.thread(sid, sup)
    for m in th.get("messages", []):
        for att in m.get("attachments") or []:
            if att.get("attachment_id") and "text" not in att:
                try:
                    att["text"] = read_document(att["name"], client.attachment(sid, att["attachment_id"]))
                except Exception:
                    att["text"] = ""
    return th


@app.get("/api/cases")
def cases():
    try:
        out = []
        for set_ in ("practice", "sandbox"):
            for c in client.cases(set_):
                if set_ == "sandbox" or c.get("hosted"):
                    CASES[c["case_id"]] = c
                    out.append({"case_id": c["case_id"], "set": set_, "type": c["type"], "title": c["title"],
                                "goal": c["buyer"]["category_goal"]})
        return {"cases": out, "me": client.me()}
    except Exception as e:
        err(e)


@app.post("/api/open")
def open_session(body: dict):
    cid = body["case_id"]
    try:
        s = client.open_session(cid)
    except Exception as e:
        err(e)
    sid = s["session_id"]
    case = CASES.get(cid) or next(c for c in client.cases("practice") if c["case_id"] == cid)
    agent = None
    try:
        from arena_kit.agents.noidea import NoIdeaAgent
        from arena_kit.agents.llm import llm_from_env
        agent = NoIdeaAgent(llm_from_env() if os.environ.get("LLM_MODEL") else None)
    except Exception as e:
        print("NoIdea agent not available:", e)
    SESSIONS[sid] = {"case": case, "agent": agent}
    with LOG.open("a") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M')} {cid} {sid} (ui)\n")
    return {"session_id": sid, "case": case, "suppliers": list((s.get("threads") or {}).keys()) or case["suppliers"]}


@app.get("/api/thread/{sid}/{sup}")
def thread(sid: str, sup: str):
    try:
        th = thread_with_text(sid, sup)
    except Exception as e:
        err(e)
    case = SESSIONS.get(sid, {}).get("case")
    std = standard_terms(th.get("messages", []))
    for m in th.get("messages", []):  # our cost C (and score, if the case was probed) of every term sheet shown
        for ts in m.get("term_sheets") or []:
            if case and ts.get("terms", {}).get("unit_price") is not None:
                c = total_cost(case, ts["terms"], std)
                ts["C"] = None if c == math.inf else round(c)
                p = PROBES.get(case["case_id"][5:])
                if p and ts["C"] is not None:
                    ts["score"] = round(max(0.0, min(1.0, (p["c_open"] - c) / (p["c_open"] - p["c_best"]))), 3)
    return th


@app.post("/api/send")
def send(body: dict):
    sid, sup = body["session_id"], body["supplier_id"]
    msg = {"subject": body.get("subject") or "Re: your offer", "body": body.get("body", ""),
           "term_sheets": [{"terms": t} for t in body.get("term_sheets", []) if t],
           "refs": body.get("refs") or []}
    try:
        return client.send_message(sid, sup, msg)
    except Exception as e:
        err(e)


@app.post("/api/accept")
def accept(body: dict):
    try:
        return client.send_message(body["session_id"], body["supplier_id"],
                                   {"action": {"type": "accept", "term_sheet_id": body["term_sheet_id"]}})
    except Exception as e:
        err(e)


@app.post("/api/walk")
def walk(body: dict):
    try:
        return client.send_message(body["session_id"], body["supplier_id"], {"action": {"type": "walk_away"}})
    except Exception as e:
        err(e)


@app.get("/api/result/{sid}")
def result(sid: str):
    try:
        d = client.session(sid)
        return d.get("result", d)
    except Exception as e:
        err(e)


@app.post("/api/suggest")
def suggest(body: dict):
    """What our agent would send now (not sent)."""
    sid = body["session_id"]
    st = SESSIONS.get(sid)
    if not st or not st["agent"]:
        raise HTTPException(400, "agent not available for this session (open it from this page)")
    case = st["case"]
    try:
        threads = {s: thread_with_text(sid, s)["messages"] for s in case["suppliers"]}
        d = st["agent"].decide(case, threads)
    except Exception as e:
        err(e)
    return d


PAGE = r"""<!doctype html><html><head><meta charset="utf-8"><title>NoIdea Supplier Chat</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--bg:#f6f7f9;--card:#fff;--ink:#1d2330;--mute:#677086;--line:#dfe3ea;--buyer:#e8f0ff;--sup:#fff6e6;--ok:#127a3a;--bad:#b42318;--acc:#2f5bea}
@media (prefers-color-scheme:dark){:root{--bg:#12151b;--card:#1b2029;--ink:#e6e9ef;--mute:#9aa3b5;--line:#2c3340;--buyer:#1d2a45;--sup:#3a2f1c;--acc:#7c9bff}}
body{margin:0;font:14px/1.45 system-ui,sans-serif;background:var(--bg);color:var(--ink)}
header{padding:12px 16px;border-bottom:1px solid var(--line);display:flex;gap:12px;align-items:center;flex-wrap:wrap}
main{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr);gap:16px;padding:16px}
@media (max-width:900px){main{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px}
.msg{border-radius:8px;padding:10px;margin:8px 0;white-space:pre-wrap;word-wrap:break-word}
.buyer{background:var(--buyer)}.sup{background:var(--sup)}.meta{color:var(--mute);font-size:12px;margin-bottom:4px}
.sheet{font:12px ui-monospace,monospace;border-top:1px dashed var(--line);margin-top:6px;padding-top:6px}
button{background:var(--acc);color:#fff;border:0;border-radius:6px;padding:7px 12px;cursor:pointer;font-weight:600}
button.sec{background:transparent;color:var(--acc);border:1px solid var(--acc)}button.bad{background:var(--bad)}
select,input,textarea{background:var(--card);color:var(--ink);border:1px solid var(--line);border-radius:6px;padding:6px;font:inherit;max-width:100%}
textarea{width:100%;box-sizing:border-box;min-height:150px}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:6px 0}
.ts{border:1px solid var(--line);border-radius:8px;padding:8px;margin:6px 0}.ts label{display:inline-block;min-width:150px;color:var(--mute)}
.warn{color:var(--bad);font-weight:600}.good{color:var(--ok);font-weight:600}
</style></head><body>
<header><b>NoIdea · Supplier Chat</b>
<select id="case"></select><button onclick="openCase()">Open session</button>
<span id="quota" class="meta"></span><span class="warn">Each session = 1 practice game</span></header>
<main>
<section class="card"><div class="row"><b>Thread</b><select id="sup" onchange="load()"></select>
<button class="sec" onclick="load()">Refresh</button><span id="status" class="meta"></span></div><div id="thread"></div></section>
<section class="card"><div id="caseinfo" class="meta"></div>
<div class="row"><input id="subject" placeholder="Subject" style="flex:1"></div>
<textarea id="body" placeholder="Your e-mail. Cite data by ID with its figure, one argument per sentence."></textarea>
<div class="row"><input id="refs" placeholder="data IDs (comma-separated, optional)" style="flex:1"></div>
<div id="sheets"></div><div class="row"><button class="sec" onclick="addSheet()">+ term sheet</button></div>
<div class="row"><button onclick="send()">Send</button><button class="sec" onclick="suggest()">Ask NoIdea</button>
<button class="sec" onclick="acceptStanding()">Accept its standing offer</button><button class="bad" onclick="walk()">Walk away</button></div>
<div id="out" class="meta"></div></section></main>
<script>
let S={sid:null,case:null,threadMsgs:[]};
const $=id=>document.getElementById(id);
async function api(p,b){const r=await fetch(p,b?{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(b)}:{});
 const j=await r.json().catch(()=>({}));if(!r.ok)throw new Error(j.detail||r.status);return j}
async function init(){try{const d=await api('/api/cases');$('case').innerHTML=d.cases.map(c=>`<option value="${c.case_id}">${c.case_id} · ${c.type} · ${c.goal} · ${c.title.slice(0,50)}</option>`).join('');
 $('quota').textContent=`practice used ${d.me.practice.used}/${d.me.practice.limit}`}catch(e){$('out').textContent='Error: '+e.message}}
async function openCase(){const cid=$('case').value;if(!confirm('Open '+cid+'? This uses one practice game.'))return;
 try{const d=await api('/api/open',{case_id:cid});S.sid=d.session_id;S.case=d.case;
 $('sup').innerHTML=d.suppliers.map(s=>`<option>${s}</option>`).join('');
 const b=d.case.buyer;$('caseinfo').innerHTML=`<b>${d.case.title}</b><br>${d.case.briefing}<br>negotiable: <b>${d.case.negotiable.join(', ')}</b> · need ${b.need_per_year}/yr · ${b.horizon_years} y · must-haves: ${JSON.stringify(b.must_haves)} · alternative: ${b.alternative?b.alternative.kind:'none'}<br>session ${S.sid}`;
 $('sheets').innerHTML='';addSheet();$('subject').value='Re: '+d.case.title;load();init()}catch(e){$('out').textContent='Error: '+e.message}}
function addSheet(t){const c=S.case;if(!c)return;const div=document.createElement('div');div.className='ts';
 div.innerHTML=c.negotiable.map(f=>{const o=(c.term_options||{})[f];const v=t&&t[f]!==undefined?t[f]:'';
  if(o&&o.length)return `<div><label>${f}</label><select data-f="${f}"><option value="">(its standard)</option>${o.map(x=>`<option ${JSON.stringify(x)===JSON.stringify(v)?'selected':''} value='${JSON.stringify(x)}'>${typeof x==='object'?JSON.stringify(x):x}</option>`).join('')}</select></div>`;
  return `<div><label>${f}</label><input data-f="${f}" value="${v}" size="10"></div>`}).join('')+'<button class="sec" onclick="this.parentNode.remove()">remove</button>';$('sheets').appendChild(div)}
function sheets(){return [...document.querySelectorAll('.ts')].map(d=>{const t={};d.querySelectorAll('[data-f]').forEach(el=>{if(el.value==='')return;
 t[el.dataset.f]=el.tagName==='SELECT'?JSON.parse(el.value):(isNaN(+el.value)?el.value:+el.value)});return t}).filter(t=>Object.keys(t).length)}
async function load(){if(!S.sid)return;try{const th=await api(`/api/thread/${S.sid}/${$('sup').value}`);S.threadMsgs=th.messages||[];
 $('status').textContent=`status: ${th.status} · offers ${th.offers??''}`;
 $('thread').innerHTML=S.threadMsgs.map(m=>`<div class="msg ${m.from==='buyer'?'buyer':'sup'}"><div class="meta">${m.from} · ${m.status||''} ${m.claim_results?'· claims: '+m.claim_results.map(c=>c.result||c.status).join(', '):''}</div>${esc(m.body||(m.action?JSON.stringify(m.action):''))}
 ${(m.term_sheets||[]).map(t=>`<div class="sheet">${t.term_sheet_id||'our sheet'}: ${esc(JSON.stringify(t.terms))}${t.C!=null?` → <b>C €${t.C.toLocaleString()}</b>`:''}${t.score!=null?` · score ${t.score}`:''}</div>`).join('')}</div>`).join('');
 if(th.status&&!['open','final_offer','agreed'].includes(th.status)){const r=await api('/api/result/'+S.sid);$('out').innerHTML=r.score!=null?`<span class="good">Result: score ${(+r.score).toFixed(3)} · deal ${r.deal} · C ${Math.round(r.c_deal||0).toLocaleString()}</span>`:''}}catch(e){$('out').textContent='Error: '+e.message}}
function esc(s){return String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
async function send(){if(!S.sid)return;$('out').textContent='sending… (the supplier can take up to a minute)';
 try{await api('/api/send',{session_id:S.sid,supplier_id:$('sup').value,subject:$('subject').value,body:$('body').value,term_sheets:sheets(),refs:$('refs').value.split(',').map(x=>x.trim()).filter(Boolean)});
 $('out').textContent='sent';$('body').value='';load()}catch(e){$('out').textContent='Error: '+e.message}}
async function suggest(){if(!S.sid)return;$('out').textContent='asking NoIdea…';try{const d=await api('/api/suggest',{session_id:S.sid});const m=d.message||{};
 if(m.action){$('out').innerHTML=`NoIdea would: <b>${m.action.type}</b> ${m.action.term_sheet_id||''}`;return}
 $('subject').value=m.subject||'';$('body').value=m.body||'';$('refs').value=(m.refs||[]).join(', ');$('sheets').innerHTML='';(m.term_sheets||[]).forEach(t=>addSheet(t.terms));
 $('out').textContent='NoIdea filled the form (to '+d.supplier_id+'). Edit and press Send, or ignore.'}catch(e){$('out').textContent='Error: '+e.message}}
async function acceptStanding(){const sts=S.threadMsgs.filter(m=>m.from!=='buyer'&&m.term_sheets&&m.term_sheets.length);if(!sts.length)return;
 const id=sts[sts.length-1].term_sheets[0].term_sheet_id;if(!confirm('Accept '+id+'? This ends the case.'))return;
 try{await api('/api/accept',{session_id:S.sid,supplier_id:$('sup').value,term_sheet_id:id});load()}catch(e){$('out').textContent='Error: '+e.message}}
async function walk(){if(!confirm('Walk away? No deal from this supplier.'))return;try{await api('/api/walk',{session_id:S.sid,supplier_id:$('sup').value});load()}catch(e){$('out').textContent='Error: '+e.message}}
init();
</script></body></html>"""


@app.get("/", response_class=HTMLResponse)
def index():
    return PAGE


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("UI_PORT", "8765")))
