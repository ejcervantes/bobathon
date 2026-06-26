# Regulatory Radar — 2-Hour Hackathon Plan

## Top-Level Overview

**Goal:** Build an end-to-end AI agent that finds current EU regulatory gaps in the SME portfolio,
assesses compliance, and fires real alerts via Twilio. Target the **Core tier** (one or two live
sources, real gaps, real alerts) — scored 30% on "works end-to-end" and 25% on "quality of insight".

**Scope:** Focus on the 5 companies that already have `compliance_status.known_gaps` (easy-to-verify
findings), then extend to 2–3 inferred companies for bonus points. Use two well-defined regulations
that are cleanest to verify live: **EU Battery Regulation (2023/1542)** and **RED common-charger
rule (2022/2380)**. Add **REACH/PFAS** as a third if time allows.

**Stack choice (minimal effort):** Python script + IBM Bob (or OpenAI) for rule extraction +
Twilio Python SDK for alerts. No web framework needed — just a CLI pipeline.

**Key constraint:** All alerts must go to **your own Twilio test number**, never the
`@example.com` contacts in the dataset.

---

## Task Division (2-person or solo)

```
Person A — Data + Assessment logic        Person B — Alert + Integration
─────────────────────────────────────     ─────────────────────────────────────
Task 1: Project scaffold + deps           Task 3: Twilio alert sender
Task 2: Fetch live regulation sources     Task 4: Output formatter (JSON findings)
         + parse rules with Bob           (can start after Task 1 is done)
Task 5 (together): Wire pipeline end-to-end + demo run
```

---

## Sub-Tasks

---

### Task 1 — Project Scaffold
**Status:** `[x] done`

**Intent:** Get a runnable Python project with all dependencies in place so both people
can work immediately without environment friction.

**Expected Outcomes:**
- `requirements.txt` with `twilio`, `requests`, `python-dotenv`, `openai` (or ibm-watsonx)
- `.env.example` listing `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM`, `TWILIO_TO_TEST`, `OPENAI_API_KEY`
- `main.py` entry point that loads `.env` and runs the pipeline steps in order
- Project runs without error (even if steps are stubs)

**Todo List:**
1. Create `src/` folder with `__init__.py`
2. Create `requirements.txt`
3. Create `.env.example` and `.gitignore` entry for `.env`
4. Create `main.py` that imports and calls each step function
5. Verify `pip install -r requirements.txt` succeeds

**Relevant Context:**
- [`README.md`](regulatory-radar-bobathon-main/README.md) — tools section confirms Python + Twilio is fine
- [`sample_expected_output.json`](regulatory-radar-bobathon-main/sample_expected_output.json) — final output shape
- `.gitignore` already exists — add `.env` to it

---

### Task 2 — Fetch & Parse Live Regulation Rules
**Status:** `[x] done`

**Intent:** Pull current regulation text from 2 live sources and extract the structured
rule facts (requirement, scope, deadline). This is the "Find the rules" step (Step 1+2
from the challenge). Using the regulatory_updates.json examples as a reference shape.

**Regulations to cover (highest bang-for-buck):**

| Regulation | Source URL | Why |
|---|---|---|
| EU Battery Reg 2023/1542 Art. 77 (LMT battery passport) | https://eur-lex.europa.eu/eli/reg/2023/1542/oj | Deadline 2027-02-18, hits P013 (RideVolt) directly |
| RED Delegated Reg 2022/2380 (USB-C common charger) | https://eur-lex.europa.eu/eli/reg_del/2022/2380/oj | Hits P022 (KidVision micro-USB) directly |
| REACH SVHC PFAS/PFHxA restriction | https://echa.europa.eu/candidate-list-table | Hits P006 (FitTrack PulseBand) directly |

**Expected Outcomes:**
- `src/fetch_rules.py` with a `fetch_rules()` function
- Returns a list of rule dicts matching the shape in `regulatory_updates.json`
- Each rule has: `regulation`, `requirement`, `source_url`, `deadline`, `scope`
- Gracefully falls back to `regulatory_updates.json` + `feed/` if live fetch fails (Wi-Fi)

**Todo List:**
1. Create `src/fetch_rules.py`
2. Implement `fetch_battery_rule()` — HTTP GET EUR-Lex, extract key text (requests + basic text parsing)
3. Implement `fetch_red_charger_rule()` — same approach for RED 2022/2380
4. Implement `fetch_reach_pfas_rule()` — ECHA candidate list page
5. Add offline fallback: if any fetch fails, load the matching entry from `regulatory_updates.json`
6. Return unified list of rule dicts from `fetch_rules()`

**Relevant Context:**
- [`SOURCES.md`](regulatory-radar-bobathon-main/SOURCES.md) — exact URLs and access tips per source
- [`regulatory_updates.json`](regulatory-radar-bobathon-main/regulatory_updates.json) — shape of a rule object (use as fallback)
- [`feed/`](regulatory-radar-bobathon-main/feed/) — HTML examples if needed for parsing reference

---

### Task 3 — Twilio Alert Sender
**Status:** `[x] done`

**Intent:** Implement a reusable function that fires one real notification per gap finding.
This is isolated from the assessment logic — takes a finding dict, sends the alert.

**Expected Outcomes:**
- `src/alert.py` with `send_alert(finding)` function
- Supports `sms` channel (required), optionally `email` / `whatsapp`
- Uses `TWILIO_TO_TEST` env var — never the `@example.com` contacts in the dataset
- Prints a confirmation with Twilio message SID on success
- Alert message follows the sample: `"CompanyX: ProductY must meet RegZ by Deadline — action. Source: url"`
- Message stays under 300 characters (SMS limit)

**Todo List:**
1. Create `src/alert.py`
2. Implement `format_sms_message(finding)` — builds <300-char string from finding fields
3. Implement `send_alert(finding)` using `twilio.rest.Client`
4. Load Twilio credentials from env vars
5. Test with a single hardcoded finding (the P013 RideVolt battery passport gap from `sample_expected_output.json`)

**Relevant Context:**
- [`sample_expected_output.json`](regulatory-radar-bobathon-main/sample_expected_output.json) — exact message format
- README "Alert" step — "use your own test number"
- Twilio promo code `TUM-TWILIO-50`

---

### Task 4 — Portfolio Assessment & Gap Detection
**Status:** `[x] done`

**Intent:** For each partner + product, check whether the fetched rules apply and whether a
gap exists. Emit one finding dict per gap in the output shape. This is Step 3 of the challenge.

**Priority companies (known gaps — easiest to verify):**

| Partner | Company | Gap | Regulation |
|---|---|---|---|
| P013 | RideVolt Mobility GmbH | LMT battery, no passport | Battery 2023/1542 |
| P022 | KidVision Cams SARL | micro-USB port | RED 2022/2380 |
| P022 | KidVision Cams SARL | no RED cybersecurity docs | RED 2014/53/EU |
| P006 | FitTrack Wearables AB | PFAS/PFHxA coating | REACH SVHC |
| P008 | PlayWave Toys GmbH | DEHP in toy plastic | RoHS/REACH |
| P010 | VisionTech Displays | Mercury in CCFL panel | RoHS |

**Expected Outcomes:**
- `src/assess.py` with `assess_portfolio(partners, rules)` function
- Loads `partners.json` and for each product applies rule-matching logic
- Returns a list of finding dicts matching `sample_expected_output.json` shape
- Each finding has: `company`, `partner_id`, `product_id`, `product`, `regulation`, `requirement`, `source_url`, `gap`, `deadline`, `severity`, `recommended_action`, `alert`
- Known-gap companies always produce at least one finding (deterministic path)

**Todo List:**
1. Create `src/assess.py`
2. Implement `load_partners()` — reads `partners.json`
3. Implement rule-matching logic per product:
   - Battery passport: `battery_type == "lmt"` → gap if no Battery passport cert
   - Common charger: `has_radio == true AND connector == "micro_usb"` → gap
   - PFAS/PFHxA REACH: `"PFAS_PFHxA" in substances` → gap
   - RoHS/DEHP toy: `category == "toy_electronic" AND "DEHP" in substances` → gap
   - RoHS/Mercury: `"mercury" in substances` → gap
4. For each gap, build the finding dict using the rule's `source_url` and `deadline`
5. Populate `finding["alert"]["to"]` with `os.environ["TWILIO_TO_TEST"]` (never the CSV contact)

**Relevant Context:**
- [`partners.json`](regulatory-radar-bobathon-main/partners.json) — all 22 companies, product attributes
- [`DATASET_README.md`](regulatory-radar-bobathon-main/DATASET_README.md) — "How to think about obligations & gaps"
- [`sample_expected_output.json`](regulatory-radar-bobathon-main/sample_expected_output.json) — exact output dict shape
- Compliance_status blocks at lines 507, 679, 853, 1070, 1776 of partners.json

---

### Task 5 — Wire Pipeline + Output + Demo Run
**Status:** `[x] done`

**Intent:** Connect all four modules into a single runnable demo: fetch rules → assess portfolio
→ write findings JSON → fire real alerts. Produce the demo artifact and confirm it works end-to-end.

**Expected Outcomes:**
- `main.py` runs the full pipeline in sequence
- `findings.json` output file written (list of finding dicts)
- At least 1 real Twilio alert fires and prints a message SID to the console
- `findings.json` validates against `sample_expected_output.json` shape
- Short "How to run" section added describing stack, .env setup, and Bob usage

**Todo List:**
1. In `main.py`: call `fetch_rules()` → `assess_portfolio()` → write `findings.json`
2. Loop over findings and call `send_alert(finding)` for each
3. Print summary: "X gaps found, Y alerts sent"
4. Run `python main.py` and confirm output + Twilio SID appears
5. Add a "## How to run" section to `README.md` with `.env` setup instructions
6. Prepare 3-min demo script: show source URL → show gap in findings.json → show Twilio log

**Relevant Context:**
- All `src/` modules from Tasks 1–4
- [`sample_expected_output.json`](regulatory-radar-bobathon-main/sample_expected_output.json) — validate output against this shape
- Judging: 30% "works end-to-end", 10% "alert delivery"

---

## Recommended 2-Hour Schedule

```
0:00–0:20   Both: Read README + SOURCES + DATASET_README. Agree on stack.
0:20–0:40   A: Task 1 scaffold + Task 2 fetch stubs
            B: Task 3 Twilio sender (test with hardcoded P013 finding)
0:40–1:10   A: Task 2 finish live fetches + fallback
            B: Task 4 assess.py + gap matching logic
1:10–1:40   Both: Task 5 wire-up + debug end-to-end run
1:40–2:00   Both: Polish findings.json, record demo, write short README
```

## Fallback Strategy (if live scraping fails)

If the EUR-Lex / ECHA pages are unreachable on hackathon Wi-Fi:
- Use `regulatory_updates.json` entries as rule sources — data is already local and correctly shaped
- The assessment logic and Twilio alert still work identically
- Cite the canonical source URL (e.g. `https://eur-lex.europa.eu/eli/reg/2023/1542/oj`) even if
  you read the local copy — the URL is the authoritative reference
- The jury cares about correctness of reasoning, not whether you hit the live URL on the day
