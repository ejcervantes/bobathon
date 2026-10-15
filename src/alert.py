"""Send Twilio SMS alerts for compliance gap findings."""

import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# -- Twilio credentials (loaded from environment -- never hardcoded in source) --
_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
_AUTH_TOKEN  = os.environ.get("TWILIO_AUTH_TOKEN")
_FROM        = os.environ.get("TWILIO_FROM")
_TO          = os.environ.get("TWILIO_TO_TEST")


# -----------------------------------------------------------------------------
# Message formatter
# -----------------------------------------------------------------------------

def _fmt_date(iso: str) -> str:
    """Convert '2027-02-18' -> '18 Feb 2027' (cross-platform)."""
    from datetime import datetime
    try:
        dt = datetime.strptime(iso, "%Y-%m-%d")
        return dt.strftime("{day} %b %Y").replace("{day}", str(dt.day))
    except Exception:
        return iso


def format_sms_message(finding: dict) -> str:
    """Build a <160-char SMS message matching sample_expected_output.json format."""
    company_short = finding["company"].split()[0]
    product  = finding["product"]
    reg      = finding["regulation"].split(" - ")[0]
    deadline = _fmt_date(finding["deadline"])
    action   = finding.get("recommended_action", "").split(".")[0]
    host     = finding.get("source_url", "").replace("https://", "").split("/")[0]

    msg = f"{company_short}: your {product} needs {reg} by {deadline}. {action}. Source: {host}"
    if len(msg) <= 160:
        return msg

    # Drop action if still too long
    msg = f"{company_short}: your {product} needs {reg} by {deadline}. Source: {host}"
    return msg[:160]


# -----------------------------------------------------------------------------
# Alert sender
# -----------------------------------------------------------------------------

def send_alert(finding: dict) -> str | None:
    """Send an SMS for the given finding via Twilio.

    Returns the Twilio message SID on success, or None on any error.
    Never crashes the calling pipeline.
    """
    if not all([_ACCOUNT_SID, _AUTH_TOKEN, _FROM, _TO]):
        print(
            f"   [!] Twilio env vars not set. Skipping alert for {finding['company']}.\n"
            f"       Set TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN / TWILIO_FROM / TWILIO_TO_TEST"
        )
        return None

    body = format_sms_message(finding)

    try:
        client  = Client(_ACCOUNT_SID, _AUTH_TOKEN)
        message = client.messages.create(
            from_=_FROM,
            body=body,
            to=_TO,
        )
        print(f"   [OK] Alert sent | SID: {message.sid} | To: {_TO}")
        return message.sid
    except Exception:
        return None  # caller handles the None -- no raw stack traces in demo output
