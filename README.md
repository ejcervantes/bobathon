
# 🛰️ Regulatory Radar — AI-Powered EU Compliance Agent

> An automated AI agent built with IBM Bob and Twilio that monitors live EU regulatory updates, cross-references requirements against SME product portfolios, detects compliance gaps, and dispatches real-time alerts.
> *Developed during the GenAI Builders Day Hackathon (GDGoC TUM Campus Heilbronn) for the EcoComply challenge.*

---

## 📌 Overview

Small and Medium Enterprises (SMEs) in the electronics sector face significant overhead keeping up with fast-changing EU regulations (e.g., RoHS, REACH, WEEE, Cyber Resilience Act). Manual compliance tracking leads to missed deadlines, costly delays, or regulatory penalties.

Regulatory Radar automates this end-to-end continuous monitoring pipeline:

1. Fetch: Pulls live regulatory directives and rules from official sources.
2. Extract: Uses IBM Bob to convert complex legal text into structured requirement schemas.
3. Assess: Cross-references rules against product attributes in `partners.json` to identify compliance gaps.
4. Alert: Triggers immediate, actionable multi-channel notifications (SMS / WhatsApp) via Twilio.

---

## 🏗️ Architecture & Pipeline

```text
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  1. LIVE SCRAPE  │ →   │  2. AI PARSING   │ →   │ 3. GAP MATCHING  │ →   │ 4. AUTO ALERTING │
│  (EUR-Lex / ECHA)│     │    (IBM Bob)     │     │  (Portfolio Engine)│   │     (Twilio)     │
└──────────────────┘     └──────────────────┘     └──────────────────┘     └──────────────────┘
 Extracts current         Converts law into        Maps rules against       Fires actionable
 regulatory text          structured JSON schema   product attributes       alerts with fix steps

```

---

## 🛠️ Tech Stack & Dependencies

* Language: Python 3.10+, PowerShell (`run.ps1`)
* AI Engine & Parsing: IBM Bob (GenAI Prompting & Structured Extraction)
* Alerting Service: Twilio API (SMS / WhatsApp Integration)
* Data Format: JSON Schemas (`findings.json`, `partners.json`, `taxonomy.json`)

---

## 📂 Repository Structure

```text
├── main.py              # Core execution script (scrape, assess, and alert pipeline)
├── run.ps1              # PowerShell execution script for local environment
├── requirements.txt     # Python package dependencies
├── PLAN.md              # Detailed project architecture & execution roadmap
├── team-plan.md         # Team task breakdown and initial workflow planning
├── findings.json        # Output findings containing identified gaps and alert logs
├── .env.example         # Template for environment configuration variables
└── README.md            # Project documentation

```

---

## 🚀 Getting Started

### Prerequisites

* Python 3.10 or higher
* IBM Bob API access
* Twilio Account SID & Auth Token

### Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/ejcervantes/bobathon.git
cd bobathon

```


2. Configure environment variables:
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env

```


Add your keys inside `.env`:
```env
IBM_BOB_API_KEY=your_ibm_bob_key
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number

```


3. Install dependencies & run:
Using PowerShell:
```powershell
.\run.ps1

```


Or directly via Python:
```bash
pip install -r requirements.txt
python main.py

```



---

## 📑 Generated Findings Example (`findings.json`)

When a gap is detected, the agent logs a structured entry and triggers a Twilio notification:

```json
{
  "company_id": "COMP-102",
  "product_id": "PROD-405",
  "regulation_ref": "Directive 2011/65/EU (RoHS)",
  "source_url": "https://eur-lex.europa.eu/...",
  "gap_identified": "Exceeds permissible restricted substance threshold for lead content.",
  "deadline": "2026-12-31",
  "recommended_action": "Update component supplier certificates for sub-assembly B.",
  "alert_status": "SENT_VIA_TWILIO"
}

```

---

## 🏅 Hackathon Context & Acknowledgments

Built during the GenAI Builders Day hackathon hosted by GDGoC TUM Campus Heilbronn.

Special thanks to EcoComply, IBM, and Twilio for the challenge, tools, and support.
