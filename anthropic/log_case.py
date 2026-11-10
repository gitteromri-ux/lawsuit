#!/usr/bin/env python3
"""Claude (Anthropic) claims counter. Separate from the Perplexity record on purpose:
adding these to ../source would renumber every CLAIM-#### already sent to Perplexity.
Usage: python3 log_case.py case.json   (one case object, or a list of them)
Writes cases.json (the record) and COUNTER.md (the running counter)."""
import json, os, sys, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(HERE, "cases.json")
CATS = ["FALSE_STATUS","AUDIT_FAILURE","BROKEN_DELIVERABLE","WASTED_COMPUTE","MISSED_ETA",
        "SCOPE_REDUCTION","RULE_BREACH_OTHER","CAPABILITY_CONTRADICTION"]
REQ = ["date","project","category","severity","proof_level","summary","chat_url"]

def load():
    if os.path.exists(STORE):
        return json.load(open(STORE))
    return {"service":"Anthropic Claude (claude.ai)","account":"Gita Agency","cases":[]}

def add(d, c):
    miss = [k for k in REQ if not c.get(k)]
    if miss: sys.exit(f"missing fields: {miss}")
    if c["category"] not in CATS: sys.exit(f"category must be one of {CATS}")
    if c["proof_level"] == "proven" and not (c.get("agent_quote") and c.get("client_quote")):
        sys.exit("proven needs both agent_quote and client_quote, verbatim")
    dup = [x for x in d["cases"] if x.get("chat_url")==c["chat_url"] and x.get("agent_quote")==c.get("agent_quote")]
    if dup: print("already logged:", dup[0]["claim_no"]); return dup[0]["claim_no"]
    c["claim_no"] = f"CLAUDE-{len(d['cases'])+1:04d}"
    c["logged_utc"] = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M")
    c.setdefault("financial_usd", None); c.setdefault("minutes_lost", None)
    d["cases"].append(c); return c["claim_no"]

def counter(d):
    cs = d["cases"]; usd = sum(c["financial_usd"] or 0 for c in cs)
    mins = sum(c["minutes_lost"] or 0 for c in cs)
    L = ["# Claude claims counter","",f"Service: {d['service']}  ",
         f"Updated: {datetime.datetime.now(datetime.UTC):%Y-%m-%d %H:%M} UTC","",
         f"**Claims logged:** {len(cs)}  ",
         f"**Proven in transcript:** {sum(c['proof_level']=='proven' for c in cs)}  ",
         f"**Severity 4 or 5:** {sum(int(c['severity'])>=4 for c in cs)}  ",
         f"**Minutes lost, evidenced:** {mins}  ",
         f"**Value claimed by account owner, USD:** {usd:,.0f}","","## By category",""]
    for k in CATS:
        n = sum(c["category"]==k for c in cs)
        if n: L.append(f"- {k}: {n}")
    L += ["","## Every claim",""]
    for c in cs:
        L += [f"### {c['claim_no']} · {c['date']} · {c['project']} · {c['category']} · severity {c['severity']} · {c['proof_level']}",
              "", c["summary"], ""]
        if c.get("agent_quote"): L += [f"> Claude: {c['agent_quote']}",""]
        if c.get("client_quote"): L += [f"> Omri: {c['client_quote']}",""]
        L += [f"Chat: {c['chat_url']}  ",
              f"Value claimed: {'USD %s' % c['financial_usd'] if c['financial_usd'] else 'pending'}  ",
              f"Terms clause contradicted: {c.get('terms_clause') or 'n/a'}",""]
    open(os.path.join(HERE,"COUNTER.md"),"w").write("\n".join(L))

if __name__ == "__main__":
    d = load()
    if len(sys.argv) > 1:
        x = json.load(open(sys.argv[1]))
        for c in (x if isinstance(x,list) else [x]): print("logged", add(d,c))
    json.dump(d, open(STORE,"w"), indent=1, ensure_ascii=False); counter(d)
    print("total", len(d["cases"]))
