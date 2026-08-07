# Service Performance Record

Documented audit of AI agent service failures on the account of Gita Agency, covering 2026-07-20 to 2026-08-07.

**Live site:** https://gitteromri-ux.github.io/lawsuit/

| | |
|---|---|
| Cases documented | 440 |
| Proven in transcript | 232 |
| Severity 4 or 5 | 242 |
| Sessions audited | 40 |
| Date range | 2026-07-20 to 2026-08-07 (19 days) |
| Minutes lost, evidenced | 1281 |
| Financial implication claimed, USD | 15,000 |

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
