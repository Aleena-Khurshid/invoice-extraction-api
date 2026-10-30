"""Business checks. Extraction can be wrong, so we check the numbers agree.

The most useful check: subtotal + tax must equal total. If an OCR error turns
"1,250" into "1,260", this check catches it, and the API returns a warning
instead of silently saving a wrong number.
"""

TOLERANCE = 0.5  # rupees; allows for rounding on the invoice


def validate(fields: dict) -> list[str]:
    warnings = []
    if not fields.get("invoice_number"):
        warnings.append("invoice number not found")
    if fields.get("total") is None:
        warnings.append("total not found")
    if fields.get("invoice_date") is None:
        warnings.append("date not found or not recognised")

    subtotal, tax, total = fields.get("subtotal"), fields.get("tax_amount"), fields.get("total")
    if None not in (subtotal, tax, total):
        expected = subtotal + tax
        if abs(expected - total) > TOLERANCE:
            warnings.append(
                f"subtotal + tax ({expected:.2f}) does not match total ({total:.2f})"
            )
    if total is not None and total < 0:
        warnings.append("total is negative")
    return warnings
