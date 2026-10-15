"""Assess the SME portfolio against fetched regulations and emit compliance gap findings.

Rules covered:
  1. EU Battery Regulation 2023/1542 Art. 77   -- LMT battery passport
  2. RED Del. Reg. 2022/2380                   -- USB-C common charger
  3. REACH Annex XVII (PFHxA group)            -- PFAS coating restriction
  4. RoHS Directive 2011/65/EU Annex II        -- mercury restriction
  5. Toy Safety Directive 2009/48/EC Annex II  -- DEHP in toy electronics
  6. RED Del. Reg. 2022/30 / EN 18031          -- cybersecurity (internet-connected radio EE)
"""

import json
import os
from pathlib import Path

from src.alert import format_sms_message


# -----------------------------------------------------------------------------
# Data loader
# -----------------------------------------------------------------------------

def load_partners() -> list[dict]:
    """Load the partner portfolio from partners.json."""
    data_path = Path(__file__).parent.parent / "regulatory-radar-bobathon-main" / "partners.json"
    with open(data_path, encoding="utf-8") as f:
        return json.load(f)["partners"]


# -----------------------------------------------------------------------------
# Rule-matching predicates
# -----------------------------------------------------------------------------

def _matches_battery_passport(product: dict, rule: dict) -> bool:
    """LMT battery -> requires EU battery passport."""
    return (
        rule["scope"].get("battery_type") == "lmt"
        and product.get("battery_type") == "lmt"
    )


def _matches_common_charger(product: dict, rule: dict) -> bool:
    """Radio-enabled consumer device with micro-USB -> must switch to USB-C."""
    return (
        rule["scope"].get("connector") == "micro_usb"
        and product.get("has_radio") is True
        and product.get("connector") == "micro_usb"
        and product.get("intended_use") not in ("medical", "industrial")
    )


def _matches_substance(product: dict, rule: dict) -> bool:
    """Product contains a substance listed in rule scope."""
    rule_substances = rule["scope"].get("substances", [])
    if not rule_substances:
        return False
    return any(s in product.get("substances", []) for s in rule_substances)


def _in_category_scope(product: dict, rule: dict) -> bool:
    """Check whether the product's category is covered by the rule scope."""
    cats = rule["scope"].get("categories", "all")
    if cats == "all":
        return True
    return product.get("category") in cats


def _matches_red_cybersecurity(product: dict, rule: dict) -> bool:
    """Internet-connected smart_home consumer radio -> must document EN 18031 conformity.

    Only smart_home devices are flagged -- they are inherently internet-connected.
    Bluetooth-only audio/wearable devices are not in scope for EN 18031-2.
    Known gap: P022 KidVision LittleView Baby Monitor (smart_home, has_radio).
    """
    if not rule["scope"].get("red_cybersecurity"):
        return False
    if not product.get("has_radio"):
        return False
    if product.get("intended_use") in ("medical", "industrial"):
        return False
    if product.get("category") != "smart_home":
        return False
    return True


def _product_matches_rule(product: dict, rule: dict) -> bool:
    """Return True if this product triggers the given rule."""
    scope = rule["scope"]

    if scope.get("battery_type") == "lmt":
        return _matches_battery_passport(product, rule)

    if scope.get("connector") == "micro_usb":
        return _matches_common_charger(product, rule)

    if scope.get("red_cybersecurity"):
        return _matches_red_cybersecurity(product, rule)

    if scope.get("substances"):
        if not _in_category_scope(product, rule):
            return False
        if "DEHP" in scope["substances"] and scope.get("categories") != "all":
            return (
                product.get("category") == "toy_electronic"
                and "DEHP" in product.get("substances", [])
            )
        return _matches_substance(product, rule)

    return False


# -----------------------------------------------------------------------------
# Gap description builders
# -----------------------------------------------------------------------------

_GAP_TEMPLATES = {
    "lmt": (
        "{product} is an LMT battery sold in the EU with no digital battery passport "
        "or QR/data carrier, as required by Art. 77 of Reg (EU) 2023/1542."
    ),
    "micro_usb": (
        "{product} is a radio-enabled consumer device with a micro-USB charging port; "
        "USB-C is mandatory since 28 Dec 2024 under RED Del. Reg (EU) 2022/2380."
    ),
    "PFAS_PFHxA": (
        "{product} contains the PFAS/PFHxA group substance above 0.1% w/w, "
        "which is restricted under the REACH SVHC Candidate List."
    ),
    "mercury": (
        "{product} contains mercury above the 0.1% w/w RoHS threshold; "
        "no current exemption covers this use."
    ),
    "DEHP_toy": (
        "{product} is a toy_electronic containing DEHP above 0.1% w/w, "
        "in violation of Toy Safety Directive 2009/48/EC Annex II Part III "
        "and REACH Annex XVII toy restrictions."
    ),
    "red_cybersecurity": (
        "{product} is an internet-connected consumer radio device with no documented "
        "EN 18031 cybersecurity conformity, as required under RED Del. Reg. (EU) 2022/30 "
        "from 1 August 2025."
    ),
}

_ACTION_TEMPLATES = {
    "lmt": (
        "Create the EU battery passport (QR + data carrier) and link it before the 2027-02-18 deadline."
    ),
    "micro_usb": (
        "Redesign the charging port to USB-C and re-certify under RED before placing "
        "new stock on the EU market."
    ),
    "PFAS_PFHxA": (
        "Remove the PFHxA-based coating or reformulate below 0.1% w/w and notify ECHA."
    ),
    "mercury": (
        "Reformulate or discontinue the product; no new EEE containing mercury above "
        "threshold may be placed on the EU market."
    ),
    "DEHP_toy": (
        "Reformulate soft plastics to remove DEHP below 0.1% w/w and re-test before "
        "next production run."
    ),
    "red_cybersecurity": (
        "Commission a conformity assessment against EN 18031-1/-2/-3, update the technical "
        "file, and affix/renew the CE mark before 1 Aug 2025."
    ),
}


def _gap_key(rule: dict) -> str:
    """Derive a template key from the rule scope."""
    scope = rule["scope"]
    if scope.get("battery_type") == "lmt":
        return "lmt"
    if scope.get("connector") == "micro_usb":
        return "micro_usb"
    if scope.get("red_cybersecurity"):
        return "red_cybersecurity"
    substances = scope.get("substances", [])
    if "PFAS_PFHxA" in substances:
        return "PFAS_PFHxA"
    if "mercury" in substances:
        return "mercury"
    if "DEHP" in substances:
        return "DEHP_toy"
    return "unknown"


def _build_finding(partner: dict, product: dict, rule: dict) -> dict:
    """Build a finding dict matching sample_expected_output.json."""
    key         = _gap_key(rule)
    gap_text    = _GAP_TEMPLATES.get(key, "Compliance gap detected.").format(product=product["name"])
    action_text = _ACTION_TEMPLATES.get(key, "Review and remediate before the deadline.")
    alert_to    = os.environ.get("TWILIO_TO_TEST") or "<your-test-number>"

    finding = {
        "company":            partner["company"],
        "partner_id":         partner["partner_id"],
        "product_id":         product["product_id"],
        "product":            product["name"],
        "regulation":         rule["regulation"],
        "requirement":        rule["requirement"],
        "source_url":         rule["source_url"],
        "gap":                gap_text,
        "deadline":           rule["deadline"],
        "severity":           "high",
        "recommended_action": action_text,
        "alert": {
            "channel": partner["contact"]["preferred_channel"],
            "to":      alert_to,
            "message": "",
        },
    }
    finding["alert"]["message"] = format_sms_message(finding)
    return finding


# -----------------------------------------------------------------------------
# Public entry point
# -----------------------------------------------------------------------------

def assess_portfolio(partners: list[dict], rules: list[dict]) -> list[dict]:
    """Return one finding dict per gap found across all 22 companies."""
    findings = []
    for partner in partners:
        for product in partner["products"]:
            for rule in rules:
                if _product_matches_rule(product, rule):
                    findings.append(_build_finding(partner, product, rule))
    return findings
