from datetime import date

from app.extractor import extract_fields

STANDARD = """Invoice No: INV-2026-0042
Date: 05/03/2026
From: Hassan Traders
Bill To: Bright Future School
Subtotal: Rs. 1,25,000.00
GST (17%): Rs. 21,250.00
Grand Total: Rs. 1,46,250.00
"""

ALT = """Invoice #: BL/22/10
Invoice Date: 05 Mar 2026
Seller: Lahore Tech Hub
Buyer: Metro Cafe
Sub Total: PKR 1234.50
Sales Tax: PKR 209.87
Total Amount: PKR 1444.37
"""


def test_standard_layout_all_fields():
    f = extract_fields(STANDARD)
    assert f["invoice_number"] == "INV-2026-0042"
    assert f["invoice_date"] == date(2026, 3, 5)
    assert f["currency"] == "PKR"
    assert f["vendor_name"] == "Hassan Traders"
    assert f["buyer_name"] == "Bright Future School"
    assert f["subtotal"] == 125000.0      # lakh commas removed
    assert f["tax_amount"] == 21250.0
    assert f["total"] == 146250.0         # "Grand Total", not "Subtotal"


def test_alt_layout_western_commas_and_labels():
    f = extract_fields(ALT)
    assert f["invoice_number"] == "BL/22/10"
    assert f["invoice_date"] == date(2026, 3, 5)
    assert f["subtotal"] == 1234.5
    assert f["tax_amount"] == 209.87
    assert f["total"] == 1444.37


def test_total_does_not_match_subtotal_line():
    text = "Sub Total: Rs. 500.00\nSales Tax: Rs. 85.00"
    f = extract_fields(text)
    assert f["subtotal"] == 500.0
    assert f["total"] is None


def test_due_date_is_not_taken_as_invoice_date():
    text = "Due Date: 20/04/2026\nInvoice No: X-1"
    assert extract_fields(text)["invoice_date"] is None


def test_tax_id_is_not_taken_as_tax_amount():
    text = "Tax ID: 1234567\nTotal: Rs. 900.00"
    f = extract_fields(text)
    assert f["tax_amount"] is None
    assert f["total"] == 900.0


def test_usd_currency_detected():
    assert extract_fields("Total: $ 250.00")["currency"] == "USD"


def test_missing_fields_are_none():
    f = extract_fields("Just a note with no invoice details at all.")
    assert all(v is None for v in f.values())
