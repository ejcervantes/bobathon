"""Regulatory Radar — main pipeline entry point.

Run:
    python main.py

Requires a .env file with:
    TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM, TWILIO_TO_TEST
"""
import json
from dotenv import load_dotenv

from src.fetch_rules import fetch_rules
from src.assess import load_partners, assess_portfolio
from src.alert import send_alert

load_dotenv()


def main() -> None:
    # ── Step 1: Fetch live regulations ──────────────────────────────────────
    print("🔍 Fetching live regulations...")
    rules = fetch_rules()
    print(f"\n   {len(rules)} rule(s) loaded:")
    for rule in rules:
        print(f"   • {rule['regulation']}")
        print(f"     source: {rule['source_url']}")

    # ── Step 2: Assess portfolio ─────────────────────────────────────────────
    print("\n📋 Assessing portfolio...")
    partners = load_partners()
    findings = assess_portfolio(partners, rules)
    print(f"\n   {len(findings)} gap(s) detected across {len(partners)} companies:\n")
    for finding in findings:
        reg_short = finding["regulation"][:60] + ("…" if len(finding["regulation"]) > 60 else "")
        print(f"   ⚠️  {finding['partner_id']} | {finding['company']}")
        print(f"        {finding['product']} → {reg_short}")

    # ── Step 3: Write findings.json ──────────────────────────────────────────
    output_path = "findings.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(findings, f, indent=2, ensure_ascii=False)
    print(f"\n📄 Findings written to {output_path}")

    # ── Step 4: Send alerts ──────────────────────────────────────────────────
    print("\n📡 Sending alerts...")
    alerts_sent = 0
    for finding in findings:
        sid = send_alert(finding)
        if sid:
            alerts_sent += 1

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n✅ Done. {len(findings)} gaps found, {alerts_sent} alerts attempted.")


if __name__ == "__main__":
    main()
