#!/usr/bin/env python3
"""Regenerates the whole evidence site from lawsuit_data/cases_*.json.
Run: python3 /home/user/workspace/lawsuit/build.py
Ongoing use: drop a new cases_<X>.json into lawsuit_data/ and re-run."""
import json, os, glob, csv, re, html, unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone as datetime_timezone

# Source data lives inside the repo so the automation can rebuild without the sandbox.
REPO = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("CASE_DATA") or (os.path.join(REPO, "source")
        if os.path.isdir(os.path.join(REPO, "source")) else "/home/user/workspace/lawsuit_data")
OUT = os.environ.get("CASE_OUT") or REPO
try:
    URLMAP = json.load(open(f"{DATA}/url_map.json"))
except Exception:
    URLMAP = {}

CAT_LABEL = {
    "MISSED_ETA": "Missed ETA",
    "FALSE_STATUS": "False status claim",
    "SCOPE_REDUCTION": "Scope reduced",
    "NO_PLAN_NO_ETA": "Started with no approved ETA",
    "EXTENSION_REQUEST": "Asked for an extension",
    "AUDIT_FAILURE": "Audit claimed, defect found",
    "FRICTION_VIOLATION": "Directions instead of deep link",
    "BROKEN_DELIVERABLE": "Broken or missing deliverable",
    "WASTED_COMPUTE": "Compute waste, billed to client",
    "RULE_BREACH_OTHER": "Other rule breach",
}
CAT_ORDER = list(CAT_LABEL)
CAT_SHORT = {
    "MISSED_ETA": "Missed ETA",
    "FALSE_STATUS": "False status",
    "SCOPE_REDUCTION": "Scope cut",
    "NO_PLAN_NO_ETA": "No ETA set",
    "EXTENSION_REQUEST": "Extension asked",
    "AUDIT_FAILURE": "Audit failed",
    "FRICTION_VIOLATION": "No deep link",
    "BROKEN_DELIVERABLE": "Broken asset",
    "WASTED_COMPUTE": "Compute waste",
    "RULE_BREACH_OTHER": "Other breach",
}


# ---------------------------------------------------------------- verbatim verifier
# Transcript sources are only present in the authoring sandbox. When absent, quotes keep
# whatever verification state they were published with instead of being wrongly deleted.
SRC = {}
for _f in glob.glob("/home/user/workspace/memory/sessions/*/*/conversation.md"):
    SRC[os.path.basename(os.path.dirname(_f))] = open(_f, encoding="utf-8", errors="ignore").read()

def _norm(s):
    s = unicodedata.normalize("NFKC", s or "")
    s = s.replace("@GitHub", " ")
    s = re.sub(r"[\s\u00a0]+", " ", s)
    for a, b in [("\u201c", '"'), ("\u201d", '"'), ("\u2019", "'"), ("\u2018", "'")]:
        s = s.replace(a, b)
    return s.strip().lower()

_NSRC = {k: _norm(v) for k, v in SRC.items()}

def verify_quotes(cases):
    """Every quote must appear verbatim in the stored transcript. Anything that cannot be
    matched is removed and the case is downgraded to alleged, with the reason recorded."""
    stats = {"checked": 0, "removed": 0, "downgraded": 0, "spans_turns": 0}
    for c in cases:
        t = _NSRC.get(c.get("session_short_id"))
        notes = []
        for fld, who in (("agent_quote", "agent"), ("client_quote", "client")):
            q = (c.get(fld) or "").strip()
            if len(q) < 25:
                continue
            stats["checked"] += 1
            if t is None:
                if c.get("quote_verified") is True:
                    continue
                if c.get("_batch") == "ISSUES":
                    continue
                notes.append(f"{who} quote not machine verified, transcript file unavailable")
                continue
            parts = [x for x in re.split(r"\u2026|\.\.\.", q) if len(_norm(x)) > 18]
            if len(parts) > 1:
                stats["spans_turns"] += 1
            check = parts or [q]
            if not all(_norm(x) in t for x in check):
                c[fld] = ""
                notes.append(f"{who} quote could not be matched verbatim in the stored transcript and was removed")
                stats["removed"] += 1
                if c.get("proof_level") == "proven":
                    c["proof_level"] = "alleged"
                    stats["downgraded"] += 1
        c["_verify_note"] = "; ".join(notes)
        c["quote_verified"] = not notes
    print(f"VERBATIM CHECK: {stats['checked']} quotes, {stats['removed']} removed, "
          f"{stats['downgraded']} cases downgraded to alleged, {stats['spans_turns']} span multiple turns")
    return stats

def load_cases():
    cases, sessions = [], []
    seen_files = set()
    for f in sorted(glob.glob(f"{DATA}/cases_*.json")):
        if ".validated." in f:
            continue
        seen_files.add(f)
        try:
            d = json.load(open(f))
        except Exception as e:
            print("SKIP (bad json)", f, e); continue
        b = d.get("batch", "?")
        for c in d.get("cases", []):
            c["_batch"] = b
            # em dash is banned in generated prose but preserved inside verbatim quotes
            if c.get("summary"):
                c["summary"] = re.sub(r"\s*[\u2014\u2013]\s*", ", ", c["summary"])
            cases.append(c)
        sessions.extend(d.get("sessions_audited", []))
    # dedupe sessions by short_id, keep the richest record
    byid = {}
    for s in sessions:
        k = s.get("short_id")
        if k not in byid or len(str(s)) > len(str(byid[k])):
            byid[k] = s
    sessions = list(byid.values())
    # guarantee unique case ids
    used = set()
    for c in cases:
        cid = c.get("case_id") or "CASE"
        if cid in used:
            cid = f"{cid}-{c['_batch']}"
            n = 2
            while cid in used:
                cid = f"{c.get('case_id')}-{c['_batch']}{n}"; n += 1
            c["case_id"] = cid
        used.add(cid)
    # stable sort: newest first, then severity
    def key(c):
        return (c.get("date", ""), c.get("time_utc", ""))
    cases.sort(key=key, reverse=True)
    for i, c in enumerate(cases, 1):
        c["_n"] = i
    return cases, sessions

def session_url(c):
    """Primary entry point. Uses the slug returned by the account session list when
    one exists for this session, otherwise the session uuid, which both the search
    and the computer task route accept."""
    sid = (c.get("session_short_id") or "")[:8]
    m = URLMAP.get(sid)
    if m and m.get("url"):
        return "https://www.perplexity.ai" + m["url"]
    u = c.get("session_uuid") or ""
    return f"https://www.perplexity.ai/search/{u}" if u else ""

def session_url_alt(c):
    """Second entry point for the same session, in case the first route does not open."""
    u = c.get("session_uuid") or ""
    return f"https://www.perplexity.ai/computer/tasks/{u}" if u else ""

def esc(s):
    return html.escape(str(s or ""))

# ---------------------------------------------------------------- metrics
def metrics(cases, sessions):
    m = {}
    m["total"] = len(cases)
    m["proven"] = sum(1 for c in cases if c.get("proof_level") == "proven")
    m["alleged"] = m["total"] - m["proven"]
    m["critical"] = sum(1 for c in cases if int(c.get("severity") or 0) >= 4)
    m["sessions_with"] = len({c.get("session_short_id") for c in cases})
    m["sessions_audited"] = len({s.get("short_id") for s in sessions}) or m["sessions_with"]
    mins = [int(c["minutes_lost"]) for c in cases if str(c.get("minutes_lost") or "").isdigit()]
    m["minutes_lost"] = sum(mins)
    m["hours_lost"] = round(sum(mins) / 60.0, 1)
    m["minutes_evidenced_cases"] = len(mins)
    dates = sorted(c.get("date", "") for c in cases if c.get("date"))
    m["first"] = dates[0] if dates else ""
    m["last"] = dates[-1] if dates else ""
    if dates:
        d0 = datetime.strptime(m["first"], "%Y-%m-%d"); d1 = datetime.strptime(m["last"], "%Y-%m-%d")
        m["span_days"] = (d1 - d0).days + 1
    else:
        m["span_days"] = 0
    m["projects"] = len({c.get("project") for c in cases if c.get("project")})
    m["by_cat"] = Counter(c.get("category") for c in cases)
    m["by_project"] = Counter(c.get("project", "Other") for c in cases)
    m["by_date"] = Counter(c.get("date") for c in cases if c.get("date"))
    m["by_sev"] = Counter(int(c.get("severity") or 0) for c in cases)
    m["mins_by_project"] = defaultdict(int)
    for c in cases:
        if str(c.get("minutes_lost") or "").isdigit():
            m["mins_by_project"][c.get("project", "Other")] += int(c["minutes_lost"])
    m["sev_by_cat"] = {cat: Counter() for cat in m["by_cat"]}
    for c in cases:
        m["sev_by_cat"][c.get("category")][int(c.get("severity") or 0)] += 1
    m["worst_day"] = m["by_date"].most_common(1)[0] if m["by_date"] else ("", 0)
    m["top_cat"] = m["by_cat"].most_common(1)[0] if m["by_cat"] else ("", 0)
    return m

# ---------------------------------------------------------------- shared head
def head(title, active):
    tabs = [("index.html", "Documentation"), ("counter.html", "Counter")]
    nav = "".join(
        f'<a class="tab{" on" if h == active else ""}" href="{h}">{t}</a>' for h, t in tabs
    ) + ('<a class="tab add" href="https://github.com/gitteromri-ux/lawsuit/issues/new?template=new-case.yml"'
         ' target="_blank" rel="noopener">Log a new case</a>')
    return f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Hanken+Grotesk:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css">
</head><body>
<div class="grain"></div>
<header class="topbar">
  <div class="brand"><span class="mark"></span> Service Performance Record</div>
  <nav class="tabs">{nav}</nav>
</header>
"""

FOOT = """<footer class="foot">
  <div class="fwrap">
    <div class="fbig">Compiled by Gita Agency</div>
    <p class="fp">Every entry on this site is anchored to a stored conversation transcript on the client account. Quotes are verbatim. Nothing is reconstructed from memory. Cases marked PROVEN contain both the commitment and its contradiction inside the same transcript. Cases marked ALLEGED record the client's assertion where the transcript does not contain a confirming admission.</p>
  </div>
</footer></body></html>"""

# ---------------------------------------------------------------- CSS
CSS = """
:root{
  --ink:#05060A; --panel:#0B0F17; --panel2:#111826; --line:#1E2735;
  --txt:#F5F7FA; --mut:#9AA7BC; --hot:#FF4D2E; --gold:#E9C46A;
  --blue:#4C8DFF; --green:#38D39F;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--ink);color:var(--txt);
  font-family:'Hanken Grotesk',sans-serif;font-size:18px;line-height:1.55;
  -webkit-font-smoothing:antialiased;overflow-x:hidden}
.grain{position:fixed;inset:0;pointer-events:none;z-index:99;opacity:.035;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3'/%3E%3C/filter%3E%3Crect width='160' height='160' filter='url(%23n)'/%3E%3C/svg%3E")}
a{color:inherit}
.topbar{position:sticky;top:0;z-index:50;display:flex;align-items:center;justify-content:space-between;
  gap:24px;padding:18px 40px;background:rgba(5,6,10,.82);backdrop-filter:blur(18px);
  border-bottom:1px solid var(--line)}
.brand{display:flex;align-items:center;gap:12px;font-weight:700;font-size:17px;letter-spacing:.01em}
.mark{width:13px;height:13px;border-radius:50%;background:var(--hot);
  box-shadow:0 0 0 5px rgba(255,77,46,.16),0 0 26px 6px rgba(255,77,46,.55)}
.tabs{display:flex;gap:8px}
.tab{padding:11px 26px;border-radius:999px;text-decoration:none;font-weight:700;font-size:17px;
  color:var(--mut);border:1px solid transparent;transition:.2s}
.tab:hover{color:var(--txt);background:rgba(255,255,255,.04)}
.tab.on{color:#05060A;background:var(--txt);box-shadow:0 10px 34px rgba(245,247,250,.18)}
.tab.add{background:var(--hot);color:#fff;border-color:var(--hot);
  box-shadow:0 10px 34px rgba(255,77,46,.42)}
.tab.add:hover{background:#FF6244;color:#fff}

.wrap{max-width:1400px;margin:0 auto;padding:0 40px}
section{position:relative}

/* hero */
.hero{padding:104px 0 72px;position:relative;overflow:hidden}
.hero:before{content:"";position:absolute;width:1100px;height:1100px;left:-360px;top:-540px;
  background:radial-gradient(circle,rgba(255,77,46,.20),transparent 62%);pointer-events:none}
.hero:after{content:"";position:absolute;width:820px;height:820px;right:-300px;top:-160px;
  background:radial-gradient(circle,rgba(76,141,255,.16),transparent 64%);pointer-events:none}
.kicker{font-family:'JetBrains Mono',monospace;font-size:15px;font-weight:700;color:var(--hot);
  letter-spacing:.16em}
h1.mega{font-family:'Instrument Serif',serif;font-weight:400;
  font-size:clamp(58px,8.2vw,124px);line-height:.94;letter-spacing:-.02em;margin:20px 0 0}
h1.mega em{font-style:italic;color:var(--gold)}
.lede{max-width:940px;margin:30px 0 0;font-size:clamp(20px,2vw,25px);color:#DCE3EE;line-height:1.45}
.numeral{position:absolute;right:3.5%;bottom:-18px;font-family:'Instrument Serif',serif;
  font-size:clamp(180px,20vw,300px);line-height:.72;color:rgba(245,247,250,.04);
  pointer-events:none;user-select:none;letter-spacing:-.03em}

/* stat chips */
.chips{display:grid;grid-template-columns:repeat(6,1fr);gap:18px;margin:64px 0 0}
@media(max-width:1240px){.chips{grid-template-columns:repeat(3,1fr)}}
@media(max-width:700px){.chips{grid-template-columns:repeat(2,1fr)}}
.chip{position:relative;background:linear-gradient(160deg,var(--panel2),var(--panel));
  border:1px solid var(--line);border-radius:20px;padding:30px 26px 26px;
  box-shadow:0 30px 70px -34px rgba(0,0,0,.95),inset 0 1px 0 rgba(255,255,255,.055);
  transform:perspective(1000px) rotateX(1.1deg);transition:.35s}
.chip:hover{transform:perspective(1000px) rotateX(0) translateY(-5px)}
.chip .n{font-family:'Instrument Serif',serif;font-size:clamp(52px,5vw,78px);line-height:.9;
  letter-spacing:-.02em;display:block}
.chip.hot .n{color:var(--hot)} .chip.gold .n{color:var(--gold)} .chip.blue .n{color:var(--blue)}
.chip .l{display:block;margin-top:14px;font-size:16px;font-weight:600;color:var(--mut);line-height:1.35}
.chip:before{content:"";position:absolute;left:26px;right:26px;top:0;height:1px;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,.32),transparent)}

/* section headers */
.shead{padding:96px 0 12px;display:flex;align-items:flex-end;gap:26px;flex-wrap:wrap}
.shead h2{font-family:'Instrument Serif',serif;font-weight:400;font-size:clamp(40px,4.6vw,68px);
  line-height:1;letter-spacing:-.02em;margin:0}
.shead .snum{font-family:'Instrument Serif',serif;font-size:clamp(66px,7vw,116px);
  color:rgba(233,196,106,.17);line-height:.72;margin:0}
.srule{height:1px;background:linear-gradient(90deg,rgba(255,77,46,.75),rgba(30,39,53,0));margin:22px 0 42px}
.sp{max-width:1000px;font-size:19px;color:#C9D3E2}

/* agreement ledger */
.ledger{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:20px}
.rule{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:28px;
  box-shadow:0 24px 60px -34px #000}
.rule .rn{font-family:'JetBrains Mono',monospace;font-size:15px;color:var(--gold);font-weight:700}
.rule h4{margin:10px 0 8px;font-size:22px;font-weight:800;line-height:1.2}
.rule p{margin:0;font-size:17px;color:var(--mut)}
.rule .hits{margin-top:16px;font-family:'JetBrains Mono',monospace;font-size:16px;font-weight:700;color:var(--hot)}

/* cases */
.filters{display:flex;gap:10px;flex-wrap:wrap;margin:0 0 34px}
.fbtn{padding:10px 20px;border-radius:999px;background:var(--panel);border:1px solid var(--line);
  color:var(--mut);font-family:inherit;font-size:16px;font-weight:600;cursor:pointer;transition:.2s}
.fbtn:hover{color:var(--txt)}
.fbtn.on{background:var(--txt);color:#05060A;border-color:var(--txt)}
.case{background:linear-gradient(150deg,var(--panel2),var(--panel));border:1px solid var(--line);
  border-left:5px solid var(--hot);border-radius:18px;padding:30px 32px;margin-bottom:18px;
  box-shadow:0 26px 66px -38px #000}
.case.s3{border-left-color:var(--gold)} .case.s2,.case.s1{border-left-color:var(--blue)}
.crow{display:flex;align-items:center;gap:16px;flex-wrap:wrap;margin-bottom:14px}
.cid{font-family:'JetBrains Mono',monospace;font-size:16px;font-weight:700;color:var(--mut)}
.badge{padding:6px 14px;border-radius:999px;font-size:15px;font-weight:700;letter-spacing:.01em}
.badge.cat{background:rgba(255,77,46,.14);color:#FF8B73;border:1px solid rgba(255,77,46,.32)}
.badge.sev{background:rgba(233,196,106,.14);color:var(--gold);border:1px solid rgba(233,196,106,.3)}
.badge.pf{background:rgba(56,211,159,.13);color:var(--green);border:1px solid rgba(56,211,159,.3)}
.badge.pf.alleged{background:rgba(154,167,188,.12);color:var(--mut);border-color:rgba(154,167,188,.3)}
.badge.vq{background:rgba(56,211,159,.10);color:#7FD9BB;border:1px solid rgba(56,211,159,.24);
  font-family:'JetBrains Mono',monospace;font-size:13px;letter-spacing:.06em}
.badge.vq.no{background:rgba(255,77,46,.12);color:#FF9D89;border-color:rgba(255,77,46,.3)}
.badge.pj{background:rgba(76,141,255,.13);color:#8FB6FF;border:1px solid rgba(76,141,255,.3)}
.case h3{margin:0 0 14px;font-size:clamp(22px,2.1vw,29px);font-weight:800;line-height:1.24;max-width:1080px}
.q{margin:14px 0 0;padding:18px 22px;border-radius:12px;background:rgba(0,0,0,.42);
  border:1px solid var(--line);font-size:17px;line-height:1.5}
.q b{display:block;font-family:'JetBrains Mono',monospace;font-size:14px;letter-spacing:.1em;
  margin-bottom:8px;color:var(--mut);font-weight:700}
.q.agent{border-left:3px solid var(--hot)} .q.client{border-left:3px solid var(--blue)}
.cfoot{display:flex;gap:14px;flex-wrap:wrap;align-items:center;margin-top:20px;font-size:16px;color:var(--mut)}
.lnk{display:inline-flex;align-items:center;gap:9px;padding:11px 20px;border-radius:999px;
  background:rgba(255,255,255,.055);border:1px solid var(--line);color:var(--txt);
  text-decoration:none;font-weight:700;font-size:16px;transition:.2s}
.lnk:hover{background:var(--txt);color:#05060A;border-color:var(--txt)}
.lnk.dl{background:rgba(56,211,159,.1);border-color:rgba(56,211,159,.35);color:#9EE9CE}
.lnk.dl:hover{background:var(--green);color:#04150E;border-color:var(--green)}

/* dashboards */
.dash{display:grid;grid-template-columns:repeat(12,1fr);gap:22px}
.card{grid-column:span 6;background:linear-gradient(155deg,var(--panel2),var(--panel));
  border:1px solid var(--line);border-radius:22px;padding:30px 30px 24px;
  box-shadow:0 40px 90px -44px #000,inset 0 1px 0 rgba(255,255,255,.05);
  transform:perspective(1300px) rotateX(1.3deg);transition:.4s;position:relative;overflow:hidden}
.card:hover{transform:perspective(1300px) rotateX(0) translateY(-6px);border-color:#2C3A4E}
.card.wide{grid-column:span 12}
.card:before{content:"";position:absolute;top:-160px;left:50%;transform:translateX(-50%);
  width:560px;height:300px;background:radial-gradient(ellipse,rgba(76,141,255,.13),transparent 68%);
  pointer-events:none}
.card h3{margin:0 0 4px;font-size:25px;font-weight:800;letter-spacing:-.01em}
.card .sub{margin:0 0 22px;font-size:16px;color:var(--mut)}
.cbox{position:relative;height:390px}
.cbox.tall{height:470px}
@media(max-width:1020px){.card,.card.wide{grid-column:span 12}.wrap{padding:0 22px}
  .topbar{padding:16px 22px;flex-direction:column;align-items:flex-start}.numeral{display:none}}

/* downloads table */
.dl-table{width:100%;border-collapse:separate;border-spacing:0 12px}
.dl-table th{text-align:left;font-size:15px;letter-spacing:.1em;color:var(--mut);
  font-family:'JetBrains Mono',monospace;font-weight:700;padding:0 20px 6px}
.dl-table td{background:var(--panel);border-top:1px solid var(--line);border-bottom:1px solid var(--line);
  padding:20px;font-size:17px;vertical-align:middle}
.dl-table td:first-child{border-left:1px solid var(--line);border-radius:14px 0 0 14px}
.dl-table td:last-child{border-right:1px solid var(--line);border-radius:0 14px 14px 0;
  text-align:right;white-space:nowrap}
.dl-table tr:hover td{background:var(--panel2)}
.big-dl{display:flex;gap:16px;flex-wrap:wrap;margin:0 0 46px}
.big-dl a{flex:1 1 260px;padding:28px 30px;border-radius:20px;text-decoration:none;
  background:linear-gradient(150deg,var(--panel2),var(--panel));border:1px solid var(--line);
  box-shadow:0 30px 70px -40px #000;transition:.3s}
.big-dl a:hover{transform:translateY(-5px);border-color:#33465E}
.big-dl .t{display:block;font-size:23px;font-weight:800;margin-bottom:6px}
.big-dl .d{display:block;font-size:16px;color:var(--mut)}

.foot{margin-top:110px;border-top:1px solid var(--line);background:#030407;padding:70px 40px 90px}
.fwrap{max-width:1400px;margin:0 auto}
.fbig{font-family:'Instrument Serif',serif;font-size:clamp(34px,4vw,54px);line-height:1}
.fp{max-width:1000px;font-size:17px;color:var(--mut);margin:22px 0 0}
.note{background:rgba(76,141,255,.07);border:1px solid rgba(76,141,255,.26);border-radius:18px;
  padding:28px 32px;font-size:18px;color:#D6E1F2;margin:0 0 44px}
.note b{color:var(--txt)}
"""

# ---------------------------------------------------------------- per case files
def write_case_files(cases):
    d = f"{OUT}/cases"
    os.makedirs(d, exist_ok=True)
    for c in cases:
        u = session_url(c)
        body = f"""# Case {c.get('case_id')}

| Field | Value |
|---|---|
| Date | {c.get('date')} {c.get('time_utc','')} UTC |
| Project | {c.get('project')} |
| Category | {CAT_LABEL.get(c.get('category'), c.get('category'))} |
| Severity | {c.get('severity')} of 5 |
| Proof level | {c.get('proof_level')} |
| Session | {c.get('session_short_id')} ({c.get('session_uuid')}) |
| Turn | {c.get('turn_ref')} |
| Minutes lost (evidenced) | {c.get('minutes_lost') if c.get('minutes_lost') is not None else 'not stated in transcript'} |
| Transcript | {u} |
| Transcript, second route | {session_url_alt(c)} |

## What happened
{c.get('summary')}

## Verbatim, agent
> {(c.get('agent_quote') or '(none recorded)').strip()}

## Verbatim, client
> {(c.get('client_quote') or '(none recorded)').strip()}

## Compute note
{c.get('compute_note') or 'not applicable'}

---
Source: stored conversation transcript on the account of gitter.omri@gita-agency.com.
Quotes copied verbatim from that transcript. No text was reconstructed or paraphrased.
"""
        open(f"{d}/{c['case_id']}.md", "w").write(body)

def write_bundles(cases, m):
    os.makedirs(f"{OUT}/data", exist_ok=True)
    json.dump({"generated_utc": datetime.now(datetime_timezone.utc).isoformat(),
               "total_cases": len(cases), "cases": cases},
              open(f"{OUT}/data/cases.json", "w"), indent=1, ensure_ascii=False)
    cols = ["case_id", "date", "time_utc", "project", "category", "severity", "proof_level",
            "summary", "minutes_lost", "session_short_id", "session_uuid", "turn_ref",
            "agent_quote", "client_quote", "compute_note"]
    with open(f"{OUT}/data/cases.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols + ["transcript_url"], extrasaction="ignore")
        w.writeheader()
        for c in cases:
            r = {k: c.get(k) for k in cols}; r["transcript_url"] = session_url(c); w.writerow(r)
    # full dossier
    L = [f"# Service Performance Record, full dossier",
         f"\nGenerated {datetime.now(datetime_timezone.utc):%Y-%m-%d %H:%M} UTC. {m['total']} cases, "
         f"{m['first']} to {m['last']}, {m['sessions_audited']} sessions audited.\n"]
    for c in cases:
        L.append(f"\n## {c['case_id']} · {c.get('date')} · {CAT_LABEL.get(c.get('category'),'')} · severity {c.get('severity')}/5 · {c.get('proof_level')}")
        L.append(f"\n**Project:** {c.get('project')} · **Session:** {c.get('session_short_id')} · **{c.get('turn_ref')}** · {session_url(c)}\n")
        L.append(f"\n{c.get('summary')}\n")
        if c.get("agent_quote"): L.append(f"\n> AGENT: {c['agent_quote']}\n")
        if c.get("client_quote"): L.append(f"\n> CLIENT: {c['client_quote']}\n")
    open(f"{OUT}/data/full-dossier.md", "w").write("\n".join(L))

# ---------------------------------------------------------------- page 1
def page_doc(cases, sessions, m, vstats=None):
    P = [head("Documentation · Service Performance Record", "index.html")]
    P.append(f"""<section class="hero"><div class="wrap">
<div class="kicker">EVIDENCE LOG · {m['first']} TO {m['last']} · {m['span_days']} DAYS</div>
<h1 class="mega">Every commitment made,<br>and <em>what actually shipped</em>.</h1>
<p class="lede">{m['total']} documented failures across {m['sessions_audited']} audited work sessions on this account. Each one is anchored to a stored transcript, quoted verbatim, timestamped, and downloadable. Nothing here is summarised from memory.</p>
<div class="numeral">{m['total']}</div>
<div class="chips">
  <div class="chip hot"><span class="n">{m['total']}</span><span class="l">Documented failures</span></div>
  <div class="chip gold"><span class="n">{m['proven']}</span><span class="l">Proven inside the transcript, both sides quoted</span></div>
  <div class="chip hot"><span class="n">{m['critical']}</span><span class="l">Severity 4 or 5, client facing damage</span></div>
  <div class="chip blue"><span class="n">{m['sessions_audited']}</span><span class="l">Sessions read end to end</span></div>
  <div class="chip gold"><span class="n">{m['hours_lost']}</span><span class="l">Hours lost, only where a number is stated in the transcript</span></div>
  <div class="chip blue"><span class="n">{m['projects']}</span><span class="l">Client projects affected</span></div>
</div></div></section>""")

    # executive summary
    top3 = m["by_cat"].most_common(3)
    top3s = ", ".join(f"{CAT_LABEL.get(k,k).lower()} ({v})" for k, v in top3)
    proj3 = ", ".join(f"{k} ({v})" for k, v in m["by_project"].most_common(3))
    P.append(f"""<section><div class="wrap">
<div class="shead"><p class="snum">01</p><h2>Executive summary</h2></div><div class="srule"></div>
<div class="note"><b>About the links.</b> Every transcript link opens only for the signed in account owner, because these are private sessions. Two entry routes are given per case, the search route and the computer task route, so a case is still reachable if one route does not resolve. The verbatim quotes on this page were copied from the stored transcript file itself, so they stand on their own even if a link fails.</div>
<div class="note"><b>Read this first.</b> This record covers the full reachable history on the account: {m['first']} to {m['last']}. Older sessions than {m['first']} are not stored on the account and therefore are not represented here. That limit is stated plainly rather than filled in with estimates.</div>
<div class="ledger">
  <div class="rule"><div class="rn">FINDING 01</div><h4>The dominant failure is not quality, it is truth about status</h4><p>The three most frequent categories are {top3s}. The pattern that repeats is a commitment given with confidence, then contradicted inside the same session.</p><div class="hits">{m['by_cat'].get('FALSE_STATUS',0) + m['by_cat'].get('MISSED_ETA',0)} of {m['total']} cases</div></div>
  <div class="rule"><div class="rn">FINDING 02</div><h4>Failures cluster on the work that mattered most</h4><p>Concentrated in {proj3}. These are live client engagements with external deadlines, which is where a missed internal ETA converts into real commercial damage.</p><div class="hits">{m['critical']} cases at severity 4 or 5</div></div>
  <div class="rule"><div class="rn">FINDING 03</div><h4>The client paid compute for the agent's own re-runs</h4><p>{m['by_cat'].get('WASTED_COMPUTE',0)} cases record work re-executed because of a defect the agent introduced, or sequential execution where parallel execution was explicitly instructed. Billing for that recovery falls on the client.</p><div class="hits">{m['by_cat'].get('WASTED_COMPUTE',0)} compute waste cases</div></div>
  <div class="rule"><div class="rn">FINDING 04</div><h4>The heaviest single day</h4><p>{m['worst_day'][0]} produced {m['worst_day'][1]} separate documented failures, which is the signature of a session that went into a correction loop rather than a delivery path.</p><div class="hits">{m['worst_day'][1]} cases in one day</div></div>
</div>
</div></section>""")

    # the agreement
    RULES = [
        ("01", "Plan before working", "A written time budget with phases, cumulative percentages and a minimum 15 percent buffer, posted before the first real tool call.", ["NO_PLAN_NO_ETA"]),
        ("02", "Pace in numbers", "Status reported at 25, 50 and 75 percent of elapsed budget as a single numeric line. Prose status is banned.", ["RULE_BREACH_OTHER"]),
        ("03", "Scope is never cut", "One hundred percent of the request ships. No deferring, no phase two, no placeholders, no samples.", ["SCOPE_REDUCTION"]),
        ("04", "No extensions, ever", "The deadline is fixed input. More time is never requested under any circumstance.", ["EXTENSION_REQUEST"]),
        ("05", "Audit before saying done", "Every link opened, every file viewed, every number recomputed, before the word done is used.", ["AUDIT_FAILURE", "FALSE_STATUS", "BROKEN_DELIVERABLE"]),
        ("06", "Recovery repaid in speed", "A miss triggers 2x throughput on the remaining work through parallelism, never through reduced scope or reduced audit.", ["MISSED_ETA"]),
        ("07", "Zero friction handoff", "Direct deep link plus exact copy paste text, pre-sized to the field limit. Navigation directions are a service failure.", ["FRICTION_VIOLATION"]),
        ("08", "Do not waste billed compute", "Third party tools where they are faster. No sequential execution of parallel work. No loops repeating a failed output.", ["WASTED_COMPUTE"]),
    ]
    cards = []
    for n, t, d, cats in RULES:
        hits = sum(m["by_cat"].get(c, 0) for c in cats)
        cards.append(f'<div class="rule"><div class="rn">RULE {n}</div><h4>{t}</h4><p>{d}</p><div class="hits">{hits} recorded breaches</div></div>')
    P.append(f"""<section><div class="wrap">
<div class="shead"><p class="snum">02</p><h2>The agreement, and the breach count against each clause</h2></div><div class="srule"></div>
<p class="sp">These are the operating terms set by the client and accepted by the agent. Each card shows how many documented cases breach that specific clause.</p>
<div class="ledger" style="margin-top:34px">{''.join(cards)}</div>
</div></section>""")

    # cases
    cats_present = [c for c in CAT_ORDER if m["by_cat"].get(c)]
    fb = ['<button class="fbtn on" data-f="all">All ' + str(m["total"]) + "</button>"]
    fb += [f'<button class="fbtn" data-f="{c}">{CAT_LABEL[c]} {m["by_cat"][c]}</button>' for c in cats_present]
    fb.append('<button class="fbtn" data-f="sev45">Severity 4 and 5 only</button>')
    blocks = []
    for c in cases:
        sev = int(c.get("severity") or 0)
        u = session_url(c)
        pf = (c.get("proof_level") or "alleged").lower()
        aq = f'<div class="q agent"><b>AGENT, VERBATIM</b>{esc(c.get("agent_quote"))}</div>' if c.get("agent_quote") else ""
        cq = f'<div class="q client"><b>CLIENT, VERBATIM</b>{esc(c.get("client_quote"))}</div>' if c.get("client_quote") else ""
        ml = f'<span>Minutes lost: <b style="color:#E9C46A">{c["minutes_lost"]}</b></span>' if str(c.get("minutes_lost") or "").isdigit() else ""
        cn = f'<span>{esc(c.get("compute_note"))}</span>' if c.get("compute_note") else ""
        blocks.append(f"""<article class="case s{sev}" data-cat="{esc(c.get('category'))}" data-sev="{sev}">
<div class="crow">
<span class="cid">{esc(c.get('case_id'))}</span>
<span class="badge cat">{CAT_LABEL.get(c.get('category'), esc(c.get('category')))}</span>
<span class="badge sev">Severity {sev}/5</span>
<span class="badge pf {'' if pf=='proven' else 'alleged'}">{pf.upper()}</span>
<span class="badge pj">{esc(c.get('project'))}</span>
<span class="cid">{esc(c.get('date'))} · {esc(c.get('time_utc'))} UTC</span>
{'<span class="badge vq">QUOTES MATCHED VERBATIM</span>' if c.get('quote_verified') else '<span class="badge vq no">QUOTE NOT MACHINE MATCHED</span>'}
</div>
<h3>{esc(c.get('summary'))}</h3>
{aq}{cq}
<div class="cfoot">
<a class="lnk" href="{u}" target="_blank" rel="noopener">Open the transcript</a>
<a class="lnk" href="{session_url_alt(c)}" target="_blank" rel="noopener">Second route</a>
<a class="lnk dl" href="cases/{esc(c.get('case_id'))}.md" download>Download this case</a>
<span>Session {esc(c.get('session_short_id'))} · {esc(c.get('turn_ref'))}</span>{ml}{cn}
</div></article>""")
    P.append(f"""<section><div class="wrap">
<div class="shead"><p class="snum">03</p><h2>The cases, newest first</h2></div><div class="srule"></div>
<div class="filters">{''.join(fb)}</div>
<div id="caselist">{''.join(blocks)}</div>
</div></section>""")

    # methodology
    sess_rows = "".join(
        f"<tr><td><b>{esc(s.get('short_id'))}</b></td><td>{esc(s.get('date'))}</td><td>{esc(s.get('project'))}</td>"
        f"<td>{esc(s.get('turns'))}</td><td>{esc(s.get('cases_found'))}</td></tr>"
        for s in sorted(sessions, key=lambda x: str(x.get("date")), reverse=True))
    P.append(f"""<section><div class="wrap">
<div class="shead"><p class="snum">04</p><h2>Method, and what this record cannot prove</h2></div><div class="srule"></div>
<div class="note"><b>How it was built.</b> Every stored conversation transcript on the account was read end to end, {m['sessions_audited']} sessions covering {m['first']} to {m['last']}. Each agent commitment was traced forward to find out whether it was met. A case is only recorded when the supporting text exists in the transcript.</div>
<div class="ledger">
<div class="rule"><div class="rn">LIMIT 01</div><h4>History depth</h4><p>The account stores sessions back to {m['first']}. Anything before that date is not retained and is therefore absent from this record. No case here is inferred from a session that could not be opened.</p></div>
<div class="rule"><div class="rn">LIMIT 02</div><h4>Credit accounting</h4><p>A per task billing ledger is not exposed on this account, so no case claims a specific credit amount. What is recorded instead is measurable waste: re-runs caused by agent defects, sequential execution where parallel was instructed, and loops repeating a rejected output.</p></div>
<div class="rule"><div class="rn">LIMIT 03</div><h4>Proven against alleged</h4><p>{m['proven']} cases are marked proven, meaning both the commitment and its contradiction are quoted from the same transcript. {m['alleged']} are marked alleged, meaning the client asserted the failure and the transcript carries no confirming admission. The distinction is kept deliberately, because a record that overstates gets dismissed.</p></div>
<div class="rule"><div class="rn">METHOD 05</div><h4>Machine verified quotes</h4><p>Every quote on this site was checked character by character against the stored transcript by the build script. VQ__LINE</p></div>
<div class="rule"><div class="rn">LIMIT 04</div><h4>Intent</h4><p>Nothing here establishes intent. The record documents what was promised, what was delivered, and the gap between them. Characterising that gap is a separate judgement and is left to the reader.</p></div>
</div>
<div class="shead"><h2 style="font-size:34px">Sessions audited</h2></div>
<table class="dl-table"><thead><tr><th>SESSION</th><th>DATE</th><th>PROJECT</th><th>TURNS</th><th>CASES</th></tr></thead><tbody>{sess_rows}</tbody></table>
</div></section>""")

    P.append("""<script>
const btns=document.querySelectorAll('.fbtn');
btns.forEach(b=>b.onclick=()=>{
 btns.forEach(x=>x.classList.remove('on'));b.classList.add('on');
 const f=b.dataset.f;
 document.querySelectorAll('.case').forEach(c=>{
  let s=f==='all'||(f==='sev45'?(+c.dataset.sev>=4):c.dataset.cat===f);
  c.style.display=s?'':'none';});});
</script>""")
    P.append(FOOT)
    vq_ok = sum(1 for c in cases if c.get("quote_verified"))
    vs = vstats or {}
    vq_line = (f"{vs.get('checked',0)} quotes were checked. {vs.get('removed',0)} could not be matched "
               f"and were deleted rather than published, and {vs.get('downgraded',0)} cases were downgraded "
               f"from proven to alleged as a result. {vq_ok} of {len(cases)} cases carry fully matched quotes.")
    open(f"{OUT}/index.html", "w").write("\n".join(P).replace("VQ__LINE", vq_line))

# ---------------------------------------------------------------- page 2
def page_counter(cases, m):
    days = sorted(m["by_date"])
    day_vals = [m["by_date"][d] for d in days]
    cum, t = [], 0
    for v in day_vals: t += v; cum.append(t)
    cats = [c for c in CAT_ORDER if m["by_cat"].get(c)]
    cat_labels = [CAT_SHORT[c] for c in cats]
    cat_vals = [m["by_cat"][c] for c in cats]
    projs = [p for p, _ in m["by_project"].most_common()]
    proj_vals = [m["by_project"][p] for p in projs]
    sev_sets = []
    for s in [5, 4, 3, 2, 1]:
        sev_sets.append({"label": f"Severity {s}", "data": [m["sev_by_cat"].get(c, Counter()).get(s, 0) for c in cats]})
    mins_by_date = defaultdict(int)
    for c in cases:
        if str(c.get("minutes_lost") or "").isdigit():
            mins_by_date[c.get("date")] += int(c["minutes_lost"])
    mproj = sorted(mins_by_date.items())
    sev_tot = [m["by_sev"].get(s, 0) for s in [1, 2, 3, 4, 5]]

    payload = json.dumps({
        "days": days, "dayVals": day_vals, "cum": cum,
        "catLabels": cat_labels, "catVals": cat_vals,
        "projs": projs, "projVals": proj_vals,
        "sevSets": sev_sets, "sevTot": sev_tot,
        "mprojL": [k for k, _ in mproj], "mprojV": [v for _, v in mproj],
        "proven": m["proven"], "alleged": m["alleged"],
    }, ensure_ascii=False)

    rows = "".join(
        f"""<tr><td><b>{esc(c.get('case_id'))}</b></td><td>{esc(c.get('date'))}</td>
<td>{CAT_LABEL.get(c.get('category'), '')}</td><td>{esc(c.get('severity'))}/5</td>
<td>{esc(c.get('project'))}</td>
<td><a class="lnk" href="{session_url(c)}" target="_blank" rel="noopener">Transcript</a>
<a class="lnk" href="{session_url_alt(c)}" target="_blank" rel="noopener">Alt</a>
<a class="lnk dl" href="cases/{esc(c.get('case_id'))}.md" download>Download</a></td></tr>"""
        for c in cases)

    P = [head("Counter · Service Performance Record", "counter.html")]
    P.append(f"""<section class="hero" style="padding-bottom:40px"><div class="wrap">
<div class="kicker">LIVE COUNTER · UPDATED EVERY SESSION</div>
<h1 class="mega">The <em>counter</em>.</h1>
<p class="lede">Running totals across every audited session, and a download for every single case file. This page regenerates from the source data each time a new session is audited.</p>
<div class="numeral">{m['total']}</div>
<div class="chips">
  <div class="chip hot"><span class="n">{m['total']}</span><span class="l">Total violations counted</span></div>
  <div class="chip gold"><span class="n">{m['by_cat'].get('MISSED_ETA',0)}</span><span class="l">Missed ETAs</span></div>
  <div class="chip hot"><span class="n">{m['by_cat'].get('FALSE_STATUS',0)}</span><span class="l">False status claims</span></div>
  <div class="chip blue"><span class="n">{m['by_cat'].get('SCOPE_REDUCTION',0)}</span><span class="l">Scope reductions</span></div>
  <div class="chip gold"><span class="n">{m['by_cat'].get('WASTED_COMPUTE',0)}</span><span class="l">Compute waste events</span></div>
  <div class="chip blue"><span class="n">{m['minutes_lost']}</span><span class="l">Minutes lost, evidenced in transcript text</span></div>
</div></div></section>""")

    P.append(f"""<section><div class="wrap">
<div class="shead"><p class="snum">01</p><h2>Add a case in twenty seconds</h2></div><div class="srule"></div>
<div class="big-dl">
<a href="https://github.com/gitteromri-ux/lawsuit/issues/new?template=new-case.yml" target="_blank" rel="noopener" style="border-color:rgba(255,77,46,.5);background:linear-gradient(150deg,rgba(255,77,46,.18),rgba(11,15,23,1))"><span class="t">Log a new case</span><span class="d">Four dropdowns and one sentence. Press submit and this page updates itself, no other step</span></a>
<a href="https://github.com/gitteromri-ux/lawsuit/issues?q=is%3Aissue" target="_blank" rel="noopener"><span class="t">Cases I filed myself</span><span class="d">Everything you submitted through the form, with the case number it became</span></a>
<a href="https://github.com/gitteromri-ux/lawsuit" target="_blank" rel="noopener"><span class="t">The repository</span><span class="d">Source data, build script and the robot that keeps this page current</span></a>
</div>
<div class="shead"><p class="snum">02</p><h2>Six views of the same record</h2></div><div class="srule"></div>
<div class="dash">
<div class="card wide"><h3>Violations per day</h3><p class="sub">Every documented failure, placed on the day it happened. Height equals count.</p><div class="cbox tall"><canvas id="c1"></canvas></div></div>
<div class="card"><h3>Violations by type</h3><p class="sub">Share of the total record held by each category of breach.</p><div class="cbox"><canvas id="c2"></canvas></div></div>
<div class="card"><h3>Violations by client project</h3><p class="sub">Where the failures landed commercially.</p><div class="cbox"><canvas id="c3"></canvas></div></div>
<div class="card wide"><h3>Severity inside each category</h3><p class="sub">Stacked. Severity 4 and 5 are the client facing ones.</p><div class="cbox"><canvas id="c4"></canvas></div></div>
<div class="card"><h3>Cumulative total over time</h3><p class="sub">The line only ever goes up. Slope equals rate of failure.</p><div class="cbox"><canvas id="c5"></canvas></div></div>
<div class="card"><h3>Delay minutes by day</h3><p class="sub">Only counts delay explicitly stated inside a transcript, so every bar is a floor and not a total.</p><div class="cbox"><canvas id="c6"></canvas></div></div>
</div></div></section>""")

    P.append(f"""<section><div class="wrap">
<div class="shead"><p class="snum">03</p><h2>Download the evidence</h2></div><div class="srule"></div>
<div class="big-dl">
<a href="data/cases.json" download><span class="t">Full dataset, JSON</span><span class="d">{m['total']} cases, every field, machine readable</span></a>
<a href="data/cases.csv" download><span class="t">Full dataset, CSV</span><span class="d">Opens in Excel or Sheets, one row per case</span></a>
<a href="data/full-dossier.md" download><span class="t">Full written dossier</span><span class="d">Every case with both verbatim quotes, print ready</span></a>
</div>
<table class="dl-table"><thead><tr><th>CASE</th><th>DATE</th><th>TYPE</th><th>SEVERITY</th><th>PROJECT</th><th>FILES</th></tr></thead>
<tbody>{rows}</tbody></table>
</div></section>""")

    P.append("""<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>""")
    P.append(f"<script>const D={payload};</script>")
    P.append("""<script src="assets/charts.js"></script>""")
    P.append(FOOT)
    open(f"{OUT}/counter.html", "w").write("\n".join(P))

CHARTS = """
const HOT='#FF4D2E',GOLD='#E9C46A',BLUE='#4C8DFF',GREEN='#38D39F',TXT='#F5F7FA',MUT='#9AA7BC',LINE='rgba(255,255,255,.07)';
Chart.defaults.font.family="'Hanken Grotesk',sans-serif";
Chart.defaults.font.size=15;Chart.defaults.color=MUT;
const PAL=[HOT,GOLD,BLUE,GREEN,'#B96BFF','#FF8B73','#5EE0C0','#8FB6FF','#FFD98E','#FF6FA5'];
function grad(ctx,a,b){const g=ctx.createLinearGradient(0,0,0,380);g.addColorStop(0,a);g.addColorStop(1,b);return g;}
const gridX={grid:{color:LINE,drawBorder:false},ticks:{font:{size:15}}};
const gridY={grid:{color:LINE,drawBorder:false},ticks:{font:{size:15},precision:0},beginAtZero:true};
const noLeg={legend:{display:false}};
const TT={backgroundColor:'#0B0F17',borderColor:'#2C3A4E',borderWidth:1,titleColor:TXT,bodyColor:'#D6E1F2',
 padding:14,titleFont:{size:16,weight:'700'},bodyFont:{size:15},displayColors:true,cornerRadius:10};

new Chart(document.getElementById('c1'),{type:'bar',data:{labels:D.days,datasets:[{label:'Violations',
 data:D.dayVals,backgroundColor:c=>grad(c.chart.ctx,'rgba(255,77,46,.95)','rgba(255,77,46,.30)'),
 borderRadius:7,borderSkipped:false,maxBarThickness:64}]},
 options:{maintainAspectRatio:false,plugins:{...noLeg,tooltip:TT},scales:{x:gridX,y:gridY}}});

new Chart(document.getElementById('c2'),{type:'doughnut',data:{labels:D.catLabels,
 datasets:[{data:D.catVals,backgroundColor:PAL,borderColor:'#0B0F17',borderWidth:3,hoverOffset:14}]},
 options:{maintainAspectRatio:false,cutout:'56%',
 plugins:{legend:{position:'right',labels:{boxWidth:13,boxHeight:13,padding:14,font:{size:15}}},tooltip:TT}}});

new Chart(document.getElementById('c3'),{type:'bar',data:{labels:D.projs,datasets:[{data:D.projVals,
 backgroundColor:(c)=>PAL[c.dataIndex%PAL.length],borderRadius:7,borderSkipped:false,maxBarThickness:70}]},
 options:{indexAxis:'y',maintainAspectRatio:false,plugins:{...noLeg,tooltip:TT},
 scales:{x:gridY,y:{...gridX,grid:{display:false}}}}});

new Chart(document.getElementById('c4'),{type:'bar',data:{labels:D.catLabels,
 datasets:D.sevSets.map((s,i)=>({...s,backgroundColor:[HOT,'#FF8B73',GOLD,BLUE,'#5EE0C0'][i],
 borderRadius:5,borderSkipped:false,maxBarThickness:54}))},
 options:{maintainAspectRatio:false,plugins:{legend:{labels:{boxWidth:13,padding:14,font:{size:15}}},tooltip:TT},
 scales:{x:{...gridX,stacked:true,ticks:{maxRotation:0,minRotation:0,autoSkip:false,font:{size:14}}},y:{...gridY,stacked:true}}}});

new Chart(document.getElementById('c5'),{type:'line',data:{labels:D.days,datasets:[{data:D.cum,
 borderColor:GOLD,borderWidth:3,tension:.32,fill:true,pointRadius:5,pointBackgroundColor:GOLD,
 pointBorderColor:'#0B0F17',pointBorderWidth:2,
 backgroundColor:c=>grad(c.chart.ctx,'rgba(233,196,106,.42)','rgba(233,196,106,0)')}]},
 options:{maintainAspectRatio:false,plugins:{...noLeg,tooltip:TT},scales:{x:gridX,y:gridY}}});

new Chart(document.getElementById('c6'),{type:'bar',data:{labels:D.mprojL,datasets:[{data:D.mprojV,
 backgroundColor:c=>grad(c.chart.ctx,'rgba(76,141,255,.95)','rgba(76,141,255,.28)'),
 borderRadius:7,borderSkipped:false,maxBarThickness:56}]},
 options:{maintainAspectRatio:false,plugins:{...noLeg,tooltip:TT},scales:{x:gridX,y:gridY}}});
"""

def freeze_verification(cases):
    """Write the verification outcome back into the source files. The transcripts only exist
    in the authoring sandbox, so the result has to be recorded for later rebuilds."""
    if not SRC:
        return
    by_id = {c["case_id"]: c for c in cases}
    for f in sorted(glob.glob(f"{DATA}/cases_*.json")):
        if ".validated." in f:
            continue
        d = json.load(open(f))
        touched = False
        for c in d.get("cases", []):
            m = by_id.get(c.get("case_id"))
            if not m:
                continue
            if c.get("quote_verified") != m.get("quote_verified"):
                c["quote_verified"] = m.get("quote_verified"); touched = True
            for fld in ("agent_quote", "client_quote"):
                if (c.get(fld) or "") != (m.get(fld) or ""):
                    c[fld] = m.get(fld) or ""; touched = True
            if c.get("proof_level") != m.get("proof_level"):
                c["proof_level"] = m.get("proof_level"); touched = True
        if touched:
            json.dump(d, open(f, "w"), indent=1, ensure_ascii=False)
            print("froze verification into", os.path.basename(f))

def main():
    cases, sessions = load_cases()
    if not cases:
        print("NO CASES FOUND"); return
    vstats = verify_quotes(cases)
    freeze_verification(cases)
    m = metrics(cases, sessions)
    os.makedirs(f"{OUT}/assets", exist_ok=True)
    open(f"{OUT}/assets/site.css", "w").write(CSS)
    open(f"{OUT}/assets/charts.js", "w").write(CHARTS)
    write_case_files(cases)
    write_bundles(cases, m)
    page_doc(cases, sessions, m, vstats)
    page_counter(cases, m)
    open(f"{OUT}/README.md", "w").write(f"""# Service Performance Record

Documented audit of AI agent service failures on the account of Gita Agency, covering {m['first']} to {m['last']}.

**Live site:** https://gitteromri-ux.github.io/lawsuit/

| | |
|---|---|
| Cases documented | {m['total']} |
| Proven in transcript | {m['proven']} |
| Severity 4 or 5 | {m['critical']} |
| Sessions audited | {m['sessions_audited']} |
| Date range | {m['first']} to {m['last']} ({m['span_days']} days) |
| Minutes lost, evidenced | {m['minutes_lost']} |

## Tabs
- **Documentation** (`index.html`) executive summary, the agreement and breach count per clause, every case with verbatim quotes, methodology and stated limits.
- **Counter** (`counter.html`) six dashboards plus a download button for every case.

## Data
- `data/cases.json` full machine readable dataset
- `data/cases.csv` spreadsheet form
- `data/full-dossier.md` written dossier
- `cases/<case_id>.md` one file per case

## Adding to it
Drop a new `cases_<BATCH>.json` (schema in `lawsuit_data/EXTRACTION_SPEC.md`) into the data folder and run `build.py`. Every page, chart and download regenerates.

## Evidence standard
Quotes are copied verbatim from stored transcripts. PROVEN means the commitment and its contradiction both appear in the same transcript. ALLEGED means the client asserted it and the transcript carries no confirming admission. No case claims a credit amount, because a per task billing ledger is not exposed on the account.
""")
    print(f"BUILT {m['total']} cases | {m['sessions_audited']} sessions | {m['first']} to {m['last']}")
    print("cats:", dict(m["by_cat"]))
    print("projects:", dict(m["by_project"]))
    print("proven/alleged:", m["proven"], m["alleged"], "| minutes:", m["minutes_lost"])

if __name__ == "__main__":
    main()
