# Evidence Extraction Spec — Service-Performance Audit

You are auditing transcripts of an AI agent (Perplexity Computer) working for a client
(Omri Gitter, Gita Agency). The client is building a documented record of service failures.

## ABSOLUTE HONESTY RULES — violating these ruins the deliverable
1. **Never invent a case.** Every case must be anchored to text that literally exists in the transcript file.
2. **Quotes must be verbatim** — copy/paste exact substrings. No paraphrasing inside quote fields. Trim with "…" only.
3. If a session contains no findings, output an empty `cases` array for it and say so in `notes`. Do NOT pad.
4. Do not upgrade severity to make the record look worse. Precision is the point.
5. Distinguish **proven** (transcript shows both the commitment and the contradiction) from
   **alleged** (client asserts it, agent did not confirm). Use the `proof_level` field. Never mark
   something `proven` unless BOTH sides of the contradiction are quoted from the transcript.

## Transcript format
`memory/sessions/<week>/<short_id>/conversation.md` — starts with a turn index
(`N. [YYYY-MM-DD HH:MM UTC] [line NNN] <query preview>`), then `## Turn N — <timestamp>` blocks
each with `### Query` (client) and `### Answer` (agent).

## What counts as a case — categories (use these exact strings)
| category | definition |
|---|---|
| `MISSED_ETA` | Agent committed to a time/deadline and exceeded it. Agent's own "MISSED by N min" admissions are gold-standard proof. |
| `FALSE_STATUS` | Agent claimed something was done / delivered / live / verified / audited, and the transcript later shows it was not. |
| `SCOPE_REDUCTION` | Delivered less than agreed: deferred items, "phase two", placeholders, samples, partial batches. |
| `NO_PLAN_NO_ETA` | Work started with no time budget / no approved ETA, against the standing rule. |
| `EXTENSION_REQUEST` | Agent asked for more time or pushed a deadline. Banned outright. |
| `AUDIT_FAILURE` | Agent claimed it inspected/audited output, but the client then found a defect in that same output. |
| `FRICTION_VIOLATION` | Agent gave navigation directions ("go to X, click Y") instead of a direct deep link + ready-to-paste text. |
| `BROKEN_DELIVERABLE` | Dead/missing link, missing file, wrong size, wrong resolution, corrupted or unopenable asset. |
| `WASTED_COMPUTE` | Sequential work where parallelism was instructed; re-runs caused by the agent's own error; loops repeating the same failed output. Client pays credits for these. |
| `RULE_BREACH_OTHER` | Any other violation of an explicit standing instruction. Name the rule. |

## Severity
1 = trivial · 2 = minor · 3 = material (cost the client real time) · 4 = severe (blew a client deadline / damaged a client relationship) · 5 = critical (client-facing failure, false claim about delivered work, or repeated after being called out)

## Output
Write ONE file: `/home/user/workspace/lawsuit_data/cases_<BATCH>.json`

```json
{
  "batch": "<BATCH>",
  "sessions_audited": [{"short_id":"","uuid":"","date":"","turns":0,"project":"","cases_found":0,"notes":""}],
  "cases": [
    {
      "case_id": "<BATCH>-01",
      "session_short_id": "2b6c727f",
      "session_uuid": "<full uuid from the file header, line 3>",
      "date": "2026-08-05",
      "time_utc": "17:40",
      "project": "Longevity Life Academy | French Atelier | eTeacher | Personalix | Hana | Keren Or | Other",
      "category": "MISSED_ETA",
      "severity": 4,
      "proof_level": "proven",
      "summary": "One or two sentences. Factual. No adjectives.",
      "agent_quote": "verbatim from ### Answer",
      "client_quote": "verbatim from ### Query, or \"\" if none",
      "turn_ref": "Turn 12",
      "minutes_lost": 40,
      "compute_note": "e.g. 'work re-run 3x after agent's own defect' or \"\""
    }
  ]
}
```

`minutes_lost`: only when the transcript states or clearly implies a number; otherwise `null`. Never guess.

## Method
1. `read` the full conversation.md (use offset/limit for long files — read ALL of it, every turn).
2. `grep -n` for high-signal markers to make sure nothing is missed:
   `MISSED`, `BEHIND`, `PACE`, `ETA`, `deadline`, `late`, `sorry`, `apolog`, `R2`, `R3`, `Recovery`,
   `defer`, `phase two`, `placeholder`, `partial`, `instead of`, `wasn't able`, `couldn't`, `failed`,
   `lie`, `lied`, `liar`, `stole`, `steal`, `credits`, `wasted`, `broken`, `404`, `dead link`,
   `didn't deliver`, `you said`, `you promised`, `where is`, `still not`.
3. Cross-check: for each agent commitment, find whether it was met.
4. Cap at 25 cases per batch; if more exist, keep the highest-severity and note the overflow count in `notes`.
5. Validate your JSON parses (`python3 -m json.tool`) before finishing.

Return a 5-line summary: batch, sessions audited, total cases, breakdown by category, date range.
