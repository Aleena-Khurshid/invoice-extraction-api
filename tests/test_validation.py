from app.validation import validate


def _full(**overrides):
    base = {"invoice_number": "A-1", "invoice_date": "2026-03-05",
            "subtotal": 1000.0, "tax_amount": 170.0, "total": 1170.0}
    base.update(overrides)
    return base


def test_consistent_invoice_has_no_warnings():
    assert validate(_full()) == []


def test_arithmetic_mismatch_is_flagged():
    warnings = validate(_full(total=1260.0))
    assert any("does not match" in w for w in warnings)


def test_small_rounding_difference_is_allowed():
    assert validate(_full(total=1170.4)) == []


def test_missing_required_fields_are_flagged():
    warnings = validate({"invoice_number": None, "total": None, "invoice_date": None})
    assert "invoice number not found" in warnings
    assert "total not found" in warnings


def test_negative_total_is_flagged():
    assert "total is negative" in validate({"total": -5.0, "invoice_number": "A", "invoice_date": "x"})
