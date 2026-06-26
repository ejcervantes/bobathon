# Regulatory Radar — 5-Person Team Plan

## Overview

**Goal:** Build a working end-to-end Regulatory Radar pipeline for the Core tier:
fetch 1–2 live EU regulatory sources → extract structured rules with IBM Bob →
assess the portfolio for gaps → fire real Twilio alerts per company.

**Scope:** Core tier — 1–2 live sources (ECHA SVHC list + EUR-Lex Battery Regulation),
several portfolio companies assessed, at least one real alert fires in the demo.

**Approach:** Five roles work in parallel. Each role has a clearly defined **input contract**
(what they receive) and **output contract** (what they produce as a file/JSON). Nobody waits
on another person unless explicitly noted. The shared interface is a small set of JSON files
stored in the repo.

---

## Shared Interface Files (the "contracts")

These files are the handoff points between roles. Format is fixed — everyone reads from /
writes to the same shape.

| File | Produced by | Consumed by | Description |
|---|---|---|---|
| `raw_rules/echa_svhc.json` | Role 1 | Role 2 | Raw ECHA SVHC data fetched live |
| `raw_rules/eurlex_battery.json` | Role 1 | Role 2 | Raw EUR-Lex Battery Reg text/excerpts |
| `structured_rules.json` | Role 2 | Role 3 | Structured rules extracted by Bob |
| `findings.json` | Role 3 | Role 4, Role 5 | All detected gaps (one object per gap) |
| `alerts_log.json` | Role 4 | Role 5 | Record of every alert sent |
| `demo_script.md` | Role 5 | Everyone | Talking points + live demo steps |

---

## Role Assignments

| Role | Label | Technical level needed | Works on |
|---|---|---|---|
| **Role 1** | Data Fetcher | One script-comfortable person | Fetch live regulatory data |
| **Role 2** | Rule Extractor | Bob-prompt work | Extract structured rules with Bob |
| **Role 3** | Gap Assessor | Bob-prompt + JSON editing | Assess portfolio, produce findings |
| **Role 4** | Alert Sender | Twilio console / low-code | Send alerts, log results |
| **Role 5** | Demo & QA | Anyone | Validate output, build demo script |

---

## Sub-Task 1 — Data Fetcher (Role 1)

**Status:** [ ] pending

### Intent
Pull current EU regulatory data from two live official sources and save it locally as raw
JSON files. This gives the rest of the team real, citable regulatory content without anyone
else needing to touch the web or write code.

### Input Contract
Nothing — this role starts from scratch using public URLs.

### Output Contract
Two files in `raw_rules/`:

```
raw_rules/
  echa_svhc.json        ← ECHA SVHC Candidate List (all current entries)
  eurlex_battery.json   ← key excerpts from EU Battery Reg (EU) 2023/1542
```

Each file must include:
- `fetched_at` — ISO timestamp of when the data was pulled
- `source_url` — the exact URL used
- `data` — the raw content (array of entries or text excerpts)

### Todo List

1. **ECHA SVHC list** — Download the Candidate List from:
   `https://echa.europa.eu/candidate-list-table`
   The page offers a direct CSV/XML export — download it and convert to JSON.
   Save as `raw_rules/echa_svhc.json`.

2. **EUR-Lex Battery Regulation** — Fetch the consolidated text of Reg (EU) 2023/1542 from:
   `https://eur-lex.europa.eu/eli/reg/2023/1542/oj`
   Extract the sections relevant to battery passport obligations (Art. 77 for LMT batteries,
   Art. 77 for industrial batteries). Save key excerpts as `raw_rules/eurlex_battery.json`.

3. Add `fetched_at` (current UTC timestamp) and `source_url` to both files.

4. Commit both files to the repo so Role 2 can pick them up immediately.

### Relevant Context
- ECHA tip from `SOURCES.md`: "Candidate List and restriction lists are downloadable (and searchable)"
- EUR-Lex CELEX number for Battery Reg: `32023R1542`
- Deadline dates to capture: LMT battery passport → `2027-02-18`; industrial → `2027-08-18`
- If the live site is unreachable on the day, fall back to `regulatory_updates.json` entries
  with `regulation_family: "Battery"` or `"REACH"` as the raw data source.

---

## Sub-Task 2 — Rule Extractor (Role 2)

**Status:** [ ] pending

### Intent
Use IBM Bob to read the raw fetched data and produce clean, structured rule objects that the
Gap Assessor can work with directly. This is a Bob-prompt job — no coding needed.

### Input Contract
- `raw_rules/echa_svhc.json` — from Role 1
- `raw_rules/eurlex_battery.json` — from Role 1
- `taxonomy.json` — already in repo (controlled vocabulary for categories/substances)

### Output Contract
`structured_rules.json` — an array of rule objects, one per distinct obligation:

```json
[
  {
    "rule_id": "REACH-SVHC-DEHP",
    "regulation": "REACH Regulation (EC) 1907/2006 — SVHC Candidate List",
    "requirement": "Products placed on EU market containing DEHP above 0.1% w/w must not be sold to consumers without notification / safe use instructions.",
    "source_url": "https://echa.europa.eu/candidate-list-table",
    "fetched_at": "2025-...",
    "deadline": "in force",
    "severity": "high",
    "scope": {
      "markets": ["EU"],
      "categories": "all",
      "substances": ["DEHP"],
      "conditions": "concentration > 0.1% w/w in any homogeneous material"
    }
  }
]
```

Target: at least **4 rule objects** — 2 from ECHA (e.g. DEHP, PFAS_PFHxA) and 2 from
EUR-Lex Battery Reg (LMT passport, industrial passport).

### Todo List

1. Open IBM Bob. Paste the contents of `raw_rules/echa_svhc.json` and ask:
   > "From this ECHA SVHC data, extract each current restriction as a structured JSON object
   > with fields: rule_id, regulation, requirement, source_url, deadline, severity, and a scope
   > block (markets, categories, substances, conditions). Focus on DEHP and PFAS_PFHxA entries."

2. Paste the contents of `raw_rules/eurlex_battery.json` and ask Bob:
   > "From this EUR-Lex Battery Regulation text, extract the battery passport obligations as
   > structured JSON. I need one rule for LMT batteries (deadline 2027-02-18) and one for
   > industrial batteries (deadline 2027-08-18). Use the same schema as above."

3. Combine Bob's outputs into a single array and save as `structured_rules.json`.

4. Validate each object has all required fields (rule_id, regulation, requirement, source_url,
   deadline, severity, scope). Fill in any missing fields manually.

5. Commit `structured_rules.json` to the repo.

### Relevant Context
- `taxonomy.json` lists all valid substance names and category keys — use exactly these values
  in the `scope.substances` and `scope.categories` fields so Role 3's matching works correctly.
- Target substances from portfolio: `DEHP`, `PFAS_PFHxA`, `decaBDE`, `MCCP`, `lead`, `mercury`.
- Example rule shape is visible in `regulatory_updates.json` — use it as a reference for the
  Bob prompt if needed.

---

## Sub-Task 3 — Gap Assessor (Role 3)

**Status:** [ ] pending

### Intent
For each company/product in the portfolio, check every structured rule and determine whether
the product is in scope and non-compliant. Produce one finding object per gap. This is the
core reasoning step — IBM Bob is used to reason about each product × rule pair.

### Input Contract
- `partners.json` — already in repo (22 companies, 53 products)
- `structured_rules.json` — from Role 2
- `sample_expected_output.json` — already in repo (defines finding schema)

### Output Contract
`findings.json` — an array of gap findings, one per detected gap:

```json
[
  {
    "company": "RideVolt Mobility GmbH",
    "partner_id": "P013",
    "product_id": "P013-A",
    "product": "e-Scooter Battery Pack 280Wh",
    "regulation": "EU Battery Regulation (EU) 2023/1542 - battery passport (Art. 77)",
    "requirement": "LMT batteries must carry a digital battery passport.",
    "source_url": "https://eur-lex.europa.eu/eli/reg/2023/1542/oj",
    "gap": "LMT e-scooter battery sold in EU with no battery passport / data carrier.",
    "deadline": "2027-02-18",
    "severity": "high",
    "recommended_action": "Create the battery passport (QR + data carrier) before the deadline.",
    "alert": {
      "channel": "sms",
      "to": "<twilio-test-number>",
      "message": "RideVolt: e-Scooter Battery Pack 280Wh needs EU battery passport by 18 Feb 2027 (Reg 2023/1542). Set up the QR/data carrier. Source: eur-lex.europa.eu"
    }
  }
]
```

### Todo List

1. Start with the **5 seeded gaps** — these are confirmed and require no inference:
   - P006 · FitTrack · PulseBand (PFAS_PFHxA REACH gap)
   - P008 · PlayBright · RoboPup (DEHP toy limit) + SingAlong Mic (GPSR button-cell)
   - P010 · DisplayOne · Legacy CCFL Panel (mercury, RoHS)
   - P013 · RideVolt · e-Scooter Battery Pack (LMT battery passport)
   - P022 · KidVision · LittleView Monitor (micro-USB / RED common-charger)
   Create one finding object per gap and add to `findings.json`.

2. For each remaining product that has a substance listed in `structured_rules.json`, ask Bob:
   > "Given this product: [paste product JSON from partners.json] and this rule: [paste rule
   > from structured_rules.json], does the rule apply? Walk through: (1) market overlap,
   > (2) category match, (3) substance present, (4) any exclusions. If it applies and there is
   > no compliance cert, what is the gap?"

3. For each Bob-confirmed gap, create a finding object matching the schema in
   `sample_expected_output.json`.

4. **Look-alike traps to avoid:**
   - P016-B (ChromaPrint US Edition) has `lead` but `markets: ["US"]` only → RoHS EU does NOT apply.
   - P007 (MediBand) has `intended_use: "medical"` → RoHS has a medical device exclusion.
   - P014-C (AirLink UK Edition) only sells in `UK` → no EU directive obligations.

5. Set `"to": "<twilio-test-number>"` in every alert object — Role 4 will replace this with
   the real Twilio test number before sending.

6. Commit `findings.json` to the repo.

### Relevant Context
- `partners.json` — product attributes: `substances`, `battery_type`, `has_radio`, `connector`,
  `markets`, `intended_use`, `compliance_streams`.
- `sample_expected_output.json` — the exact field names and types to match.
- `compliance_status.known_gaps` on P006, P008, P010, P013, P022 are ground truth for the
  seeded findings — use the exact wording as the `gap` field.

---

## Sub-Task 4 — Alert Sender (Role 4)

**Status:** [ ] pending

### Intent
Take every finding in `findings.json` and fire a real notification via Twilio on the correct
channel (SMS, WhatsApp, or email). Log every sent alert so Role 5 can show the audit trail
in the demo.

### Input Contract
- `findings.json` — from Role 3

### Output Contract
`alerts_log.json` — one entry per alert fired:

```json
[
  {
    "partner_id": "P013",
    "product_id": "P013-A",
    "channel": "sms",
    "to": "<your-twilio-test-number>",
    "message": "...",
    "sent_at": "2025-...",
    "twilio_sid": "SM..."
  }
]
```

### Todo List

1. **Set up Twilio** — create a free account, apply promo code `TUM-TWILIO-50`, get a Twilio
   phone number. Note your test number — this replaces every `<twilio-test-number>` placeholder.

2. **Channel map** — each company's `preferred_channel` determines the Twilio service to use:
   - `sms` (P003, P006, P013, P021) → Twilio SMS
   - `whatsapp` (P004, P017) → Twilio WhatsApp sandbox
   - `email` (all others) → Twilio SendGrid or Email API

3. For the demo, send ALL alerts to **your own** Twilio test number / email — never to the
   `@example.com` addresses in the dataset.

4. For each finding in `findings.json`, send the alert using the Twilio console (no-code) or
   the Twilio API. Copy the message text exactly from `finding.alert.message`.

5. After each send, record the result in `alerts_log.json`: include `sent_at` timestamp and
   the Twilio message SID returned.

6. **Priority for the demo:** send the P013 RideVolt SMS first — this is the sample output the
   judges know, so it's the strongest opener.

7. Commit `alerts_log.json` to the repo.

### Relevant Context
- Twilio promo code: `TUM-TWILIO-50`
- SMS message limit: 160 chars per segment; keep messages under 300 chars to avoid splitting.
- WhatsApp sandbox requires joining the sandbox with a WhatsApp message first.
- All dataset contacts are fabricated — using real contact details would send to nobody and is
  not needed.

---

## Sub-Task 5 — Demo & QA (Role 5)

**Status:** [ ] pending

### Intent
Validate that every file in the pipeline is complete and correctly shaped, then build the
3-minute demo script and 1-minute pitch so the team can present confidently and in sync.

### Input Contract
- All repo files: `findings.json`, `alerts_log.json`, `structured_rules.json`,
  `raw_rules/`, `partners.json`, `sample_expected_output.json`

### Output Contract
`demo_script.md` — a step-by-step walkthrough of the live demo with talking points.

### Todo List

1. **Validate `structured_rules.json`** — check every rule has: `rule_id`, `regulation`,
   `requirement`, `source_url`, `deadline`, `severity`, `scope`. Flag any missing fields to
   Role 2.

2. **Validate `findings.json`** — check every finding matches the schema in
   `sample_expected_output.json`. Confirm `source_url` is a real, reachable URL.
   Flag any issues to Role 3.

3. **Validate `alerts_log.json`** — confirm at least one alert has a real `twilio_sid`
   (not a placeholder). Flag any issues to Role 4.

4. **Write `demo_script.md`** with this structure:
   - **Slide 1 (30 s):** Problem — "EU regulations change constantly; SMEs miss them and face
     fines." Show the portfolio size (22 companies, 53 products).
   - **Slide 2 (30 s):** Pipeline diagram — Fetch → Extract → Assess → Alert.
   - **Live step 1 (45 s):** Show `structured_rules.json` — "We fetched this live from ECHA
     and EUR-Lex today, cite the URL."
   - **Live step 2 (45 s):** Show a finding in `findings.json` — walk through the gap reasoning
     (market ✓, category ✓, substance ✓, no cert → gap).
   - **Live step 3 (30 s):** Show the Twilio alert arriving on a phone in real time.
   - **Wrap (20 s):** "One real gap, one real source, one real alert — this is what EcoComply
     can automate at scale."

5. Share `demo_script.md` with the full team at least 30 minutes before the presentation.

### Relevant Context
- Judging weights: end-to-end working (30%), quality of insight with source cited (25%),
  use of IBM Bob (15%), alert delivery (10%), real-world fit (10%), demo (10%).
- The strongest demo moment is the Twilio SMS arriving live — coordinate with Role 4 to
  trigger it during the presentation.
- `dataset_stats.json` has the portfolio numbers to quote: 22 partners, 53 products.

---

## Dependency Map

```
Role 1 (Fetch)
    └──→ Role 2 (Extract)  [needs raw_rules/]
              └──→ Role 3 (Assess)  [needs structured_rules.json]
                        └──→ Role 4 (Alert)  [needs findings.json]
                        └──→ Role 5 (QA/Demo)  [needs all files]

Role 5 also validates Role 1, 2, 3 output independently.
```

**Roles 1, 2, 3 are sequential.** While waiting:
- Role 4 can set up Twilio and test a dummy message immediately.
- Role 5 can write the demo script skeleton and validate whatever is already committed.

---

## Definition of Done

- [ ] `raw_rules/echa_svhc.json` and `raw_rules/eurlex_battery.json` exist with `source_url` and `fetched_at`.
- [ ] `structured_rules.json` has at least 4 rule objects with all required fields.
- [ ] `findings.json` has at least 5 gap findings (the seeded ones) with correct schema and real `source_url`.
- [ ] `alerts_log.json` has at least 1 entry with a real Twilio SID.
- [ ] `demo_script.md` is written and shared with the team.
- [ ] The full loop (rule → gap → alert) can be shown live in the demo.
