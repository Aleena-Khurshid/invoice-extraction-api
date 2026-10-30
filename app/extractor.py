"""Rule-based extraction: find labelled fields in invoice text with regular expressions.

How a regex works here:
  "Subtotal: Rs. 1,25,000.00"
  - sub\\s*-?\\s*total   matches the label "Subtotal" (spaces and hyphen allowed)
  - [:\\-]?              an optional colon
  - (PKR|Rs\\.?)?         an optional currency prefix
  - ([0-9][0-9,]*...)    the amount, captured in a group
Then we remove the commas and convert the text to a float.

Pakistani amounts often use lakh grouping (1,25,000 = 125000). Removing all
commas handles both lakh and western (125,000) formats.

Limitation: rules only work for labels we planned for. A label they do not
cover ("Net Amount" instead of "Subtotal") is missed. The evaluation measures
exactly this, and it is the reason an LLM-based extractor is the next step.
"""

import re
from datetime import date, datetime

AMOUNT = r"([0-9][0-9,]*(?:\.[0-9]{1,2})?)"
CURRENCY_PREFIX = r"(?:PKR|Rs\.?|USD|\$)?"

# Labels. The lookbehinds stop "total" from matching inside "Subtotal" / "Sub Total".
SUBTOTAL_LABEL = r"sub\s*-?\s*total"
TOTAL_LABEL = r"(?<!sub)(?<!sub )(?<!sub-)(?:grand\s+total|total(?:\s+amount)?|amount\s+payable)"
# "Tax ID" is not a tax amount, so the lookahead skips it.
TAX_LABEL = r"(?:sales\s+tax|gst|tax)(?!\s*(?:id|no\b|number))(?:\s*\(\d+(?:\.\d+)?%\))?"

DATE_TOKEN = (
    r"\d{1,2}[/.-]\d{1,2}[/.-]\d{4}"          # 05/03/2026, 05-03-2026
    r"|\d{4}-\d{2}-\d{2}"                     # 2026-03-05
    r"|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}"       # 05 Mar 2026
    r"|[A-Za-z]{3,9}\s+\d{1,2},\s*\d{4}"      # Mar 05, 2026
)
DATE_FORMATS = [
    "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%Y-%m-%d",
    "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y",
]


def _search(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else None


def _amount(label: str, text: str) -> float | None:
    raw = _search(rf"(?:{label})\s*[:\-]?\s*{CURRENCY_PREFIX}\s*{AMOUNT}", text)
    return float(raw.replace(",", "")) if raw else None


def _parse_date(text: str | None) -> date | None:
    """Find a date-looking token in the captured text and parse it."""
    if not text:
        return None
    token = re.search(DATE_TOKEN, text, re.IGNORECASE)
    if not token:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(token.group(0), fmt).date()
        except ValueError:
            continue
    return None


def _currency(text: str) -> str | None:
    if re.search(r"\bPKR\b|\bRs\.?(?=\s*\d)", text, re.IGNORECASE):
        return "PKR"
    if re.search(r"USD|\$", text):
        return "USD"
    return None


def extract_fields(text: str) -> dict:
    """Return a dict with every invoice field. Missing fields are None."""
    return {
        "invoice_number": _search(
            r"(?:invoice|inv|bill)\s*(?:no\.?|number|#)\s*[:\-]?\s*([A-Za-z0-9][A-Za-z0-9\-/]*)",
            text,
        ),
        "invoice_date": _parse_date(_search(r"(?<!due )date\s*[:\-]\s*([^\n]+)", text)),
        "currency": _currency(text),
        "vendor_name": _search(r"^[ \t]*(?:from|seller|vendor)\s*[:\-]\s*(.+)$", text),
        "buyer_name": _search(r"^[ \t]*(?:bill\s+to|buyer|customer|to)\s*[:\-]\s*(.+)$", text),
        "subtotal": _amount(SUBTOTAL_LABEL, text),
        "tax_amount": _amount(TAX_LABEL, text),
        "total": _amount(TOTAL_LABEL, text),
    }
