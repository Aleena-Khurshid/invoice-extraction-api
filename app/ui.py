"""Streamlit UI for the invoice extractor.

Run:  python -m streamlit run app/ui.py
Then open http://localhost:8501
"""

import os
import sys

# Put the project root on the import path (needed when Streamlit runs this file directly).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from app.extractor import extract_fields
from app.schemas import Invoice
from app.store import InvoiceStore
from app.validation import validate

SAMPLE = (
    "Invoice No: INV-9\n"
    "Date: 10/04/2026\n"
    "From: Indus Office Supplies\n"
    "Bill To: Northwind Clinic\n"
    "Subtotal: Rs. 2,000.00\n"
    "GST (17%): Rs. 340.00\n"
    "Grand Total: Rs. 2,340.00\n"
)

st.set_page_config(page_title="Invoice Extractor")


@st.cache_resource
def get_store() -> InvoiceStore:
    return InvoiceStore(os.getenv("DB_PATH", "data/invoices.db"))


store = get_store()

st.title("Invoice Extractor")
st.caption(
    "Paste invoice text or upload a .txt file. The app finds the fields, "
    "checks the numbers, and saves the result."
)

if st.button("Load sample invoice"):
    st.session_state["text"] = SAMPLE

text = st.text_area("Invoice text", height=220, key="text", placeholder="Paste invoice text here...")
uploaded = st.file_uploader("Or upload a .txt file", type=["txt"])
if uploaded is not None:
    text = uploaded.getvalue().decode("utf-8", errors="replace")

if st.button("Extract", type="primary"):
    if len(text.strip()) < 10:
        st.error("Please give at least 10 characters of invoice text.")
    else:
        fields = extract_fields(text)
        warnings = validate(fields)
        invoice = Invoice(**fields, warnings=warnings)
        saved_id = store.save(invoice)

        if warnings:
            for warning in warnings:
                st.warning(warning)
        else:
            st.success(f"Saved as invoice #{saved_id}. All checks passed.")

        st.subheader("Extracted fields")
        st.table([
            {"Field": name, "Value": "not found" if value is None else str(value)}
            for name, value in fields.items()
        ])

st.subheader("Saved invoices")
saved = store.list(limit=20)
if saved:
    st.table([inv.model_dump(exclude={"warnings"}) for inv in saved])
else:
    st.info("No invoices saved yet.")
