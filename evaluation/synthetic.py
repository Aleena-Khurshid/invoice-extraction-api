"""Generate synthetic invoices WITH the correct answers (ground truth).

Three text layouts ("families"):
  standard : labels the rules were written for, lakh-style commas (1,25,000)
  alt      : different labels and western commas, also written for
  unseen   : different labels the rules were NOT written for (stress test)

The vendor and buyer names are invented. Nothing here is a real company's invoice.
"""

import random
from datetime import date, timedelta

VENDORS = ["Hassan Traders", "Indus Office Supplies", "Lahore Tech Hub",
           "Karachi Print House", "Multan Garments Co", "Peshawar Auto Parts"]
BUYERS = ["Bright Future School", "Northwind Clinic", "Falcon Logistics",
          "Green Valley Bakery", "Sunrise Textiles", "Metro Cafe"]
GST_RATE = 0.17


def lakh(amount: float) -> str:
    """125000.0 -> '1,25,000.00' (South Asian grouping)."""
    whole, frac = f"{amount:.2f}".split(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        whole = ",".join(groups + [tail])
    return f"{whole}.{frac}"


def western(amount: float) -> str:
    return f"{amount:,.2f}"


def make_truth(rng: random.Random, index: int) -> dict:
    subtotal = round(rng.uniform(500, 250_000), 2)
    tax = round(subtotal * GST_RATE, 2)
    return {
        "invoice_number": f"INV-2026-{index:04d}",
        "invoice_date": date(2026, 1, 1) + timedelta(days=rng.randint(0, 302)),
        "currency": "PKR",
        "vendor_name": rng.choice(VENDORS),
        "buyer_name": rng.choice(BUYERS),
        "subtotal": subtotal,
        "tax_amount": tax,
        "total": round(subtotal + tax, 2),
    }


def render_standard(t: dict) -> str:
    return (
        f"Invoice No: {t['invoice_number']}\n"
        f"Date: {t['invoice_date']:%d/%m/%Y}\n"
        f"From: {t['vendor_name']}\n"
        f"Bill To: {t['buyer_name']}\n"
        f"Subtotal: Rs. {lakh(t['subtotal'])}\n"
        f"GST (17%): Rs. {lakh(t['tax_amount'])}\n"
        f"Grand Total: Rs. {lakh(t['total'])}\n"
        "Thank you for your business.\n"
    )


def render_alt(t: dict) -> str:
    return (
        f"Invoice #: {t['invoice_number']}\n"
        f"Invoice Date: {t['invoice_date']:%d %b %Y}\n"
        f"Seller: {t['vendor_name']}\n"
        f"Buyer: {t['buyer_name']}\n"
        f"Sub Total: PKR {western(t['subtotal'])}\n"
        f"Sales Tax: PKR {western(t['tax_amount'])}\n"
        f"Total Amount: PKR {western(t['total'])}\n"
    )


def render_unseen(t: dict) -> str:
    return (
        f"Reference: {t['invoice_number']}\n"
        f"Dated: {t['invoice_date']:%Y-%m-%d}\n"
        f"From: {t['vendor_name']}\n"
        f"Customer: {t['buyer_name']}\n"
        f"Net Amount: {western(t['subtotal'])} PKR\n"
        f"VAT 17%: {western(t['tax_amount'])} PKR\n"
        f"Amount Payable: {western(t['total'])} PKR\n"
    )


RENDERERS = {"standard": render_standard, "alt": render_alt, "unseen": render_unseen}


def generate_dataset(per_family: int = 30, seed: int = 42) -> list[dict]:
    """Return a list of {family, text, truth} items. Same seed gives the same data."""
    rng = random.Random(seed)
    items = []
    index = 1
    for family, render in RENDERERS.items():
        for _ in range(per_family):
            truth = make_truth(rng, index)
            items.append({"family": family, "text": render(truth), "truth": truth})
            index += 1
    return items
