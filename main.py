"""Regulatory Radar — main pipeline entry point."""
import json
from src.fetch_rules import fetch_rules
from src.assess import load_partners, assess_portfolio
from src.alert import send_alert


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

    # ── Step 4: Send ONE demo alert (highest-severity finding only) ──────────
    print("\n📡 Sending demo alert (1 SMS — highest priority gap)...")
    demo_finding = findings[0] if findings else None
    alerts_sent = 0
    if demo_finding:
        sid = send_alert(demo_finding)
        if sid:
            alerts_sent += 1
            print(f"   Demo alert fired for: {demo_finding['company']} / {demo_finding['product']}")
    else:
        print("   No findings to alert on.")

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n✅ Done. {len(findings)} gaps found in findings.json, {alerts_sent} alert sent.")
    print("   💡 To send all alerts, change main.py to loop over all findings.")


if __name__ == "__main__":
    main()
