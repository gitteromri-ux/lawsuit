#!/usr/bin/env python3
"""Turns a submitted issue form into a case in source/cases_ISSUES.json.
Runs inside GitHub Actions. Reads the issue payload from the event file."""
import json, os, re, sys, datetime

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORE = os.path.join(REPO, "source", "cases_ISSUES.json")

CAT = {
    "missed eta": "MISSED_ETA",
    "false status claim": "FALSE_STATUS",
    "scope reduced": "SCOPE_REDUCTION",
    "started with no approved eta": "NO_PLAN_NO_ETA",
    "asked for an extension": "EXTENSION_REQUEST",
    "audit claimed, defect found": "AUDIT_FAILURE",
    "broken or missing deliverable": "BROKEN_DELIVERABLE",
    "compute waste, billed to me": "WASTED_COMPUTE",
    "directions instead of a deep link": "FRICTION_VIOLATION",
    "other rule breach": "RULE_BREACH_OTHER",
}

def parse_form(body):
    """GitHub renders an issue form as '### Label\\n\\nvalue' blocks."""
    out = {}
    for m in re.finditer(r"^###\s+(.+?)\s*\n+(.*?)(?=\n###\s|\Z)", body or "", re.S | re.M):
        out[m.group(1).strip().lower()] = m.group(2).strip()
    return out

def blank(v):
    return (not v) or v.strip().lower() in ("_no response_", "n/a", "none", "-")

def main():
    ev = json.load(open(os.environ["GITHUB_EVENT_PATH"]))
    issue = ev["issue"]
    f = parse_form(issue.get("body", ""))

    summary = f.get("what happened", "").strip()
    if not summary:
        print("no summary, nothing to do"); return

    cat_raw = f.get("what kind of failure", "").strip().lower()
    category = CAT.get(cat_raw, "RULE_BREACH_OTHER")

    sev_raw = f.get("how bad", "").strip()
    m = re.match(r"\s*([1-5])", sev_raw)
    severity = int(m.group(1)) if m else 3

    date = f.get("date", "").strip()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        date = issue["created_at"][:10]

    minutes = f.get("minutes lost", "").strip()
    minutes = int(minutes) if minutes.isdigit() else None

    thread = f.get("thread link or session id", "").strip()
    if blank(thread):
        thread = ""
    uuid = ""
    mu = re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", thread)
    if mu:
        uuid = mu.group(0)

    aq = f.get("what the agent said, copied exactly", "")
    cq = f.get("what you said, copied exactly", "")
    aq = "" if blank(aq) else aq.strip()
    cq = "" if blank(cq) else cq.strip()

    if os.path.exists(STORE):
        d = json.load(open(STORE))
    else:
        d = {"batch": "ISSUES", "sessions_audited": [], "cases": []}

    n = issue["number"]
    d["cases"] = [c for c in d["cases"] if c.get("case_id") != f"I-{n:03d}"]
    d["cases"].append({
        "case_id": f"I-{n:03d}",
        "session_short_id": uuid[:8] if uuid else "reported",
        "session_uuid": uuid,
        "date": date,
        "time_utc": issue["created_at"][11:16],
        "project": f.get("which project", "Other").strip() or "Other",
        "category": category,
        "severity": severity,
        "proof_level": "proven" if aq else "alleged",
        "summary": summary,
        "agent_quote": aq,
        "client_quote": cq,
        "turn_ref": f"reported in issue #{n}",
        "minutes_lost": minutes,
        "compute_note": "Logged directly by the account owner through the case form."
                        + (f" Thread: {thread}" if thread and not uuid else ""),
        "reported_issue": n,
        "reported_url": issue["html_url"],
    })
    d["cases"].sort(key=lambda c: c["case_id"])

    seen = {s.get("short_id") for s in d["sessions_audited"]}
    key = uuid[:8] if uuid else "reported"
    if key not in seen:
        d["sessions_audited"].append({
            "short_id": key, "uuid": uuid, "date": date,
            "turns": 0, "project": f.get("which project", "Other").strip() or "Other",
            "cases_found": 1, "notes": "Reported directly by the account owner."})
    for s in d["sessions_audited"]:
        if s.get("short_id") == key:
            s["cases_found"] = sum(1 for c in d["cases"]
                                   if (c.get("session_uuid") or "")[:8] == key
                                   or (not c.get("session_uuid") and key == "reported"))

    os.makedirs(os.path.dirname(STORE), exist_ok=True)
    json.dump(d, open(STORE, "w"), indent=1, ensure_ascii=False)
    print(f"wrote case I-{n:03d} ({category}, severity {severity}) to {STORE}")
    with open(os.environ["GITHUB_OUTPUT"], "a") as g:
        g.write(f"case_id=I-{n:03d}\n")
        g.write(f"total={len(d['cases'])}\n")

if __name__ == "__main__":
    main()
