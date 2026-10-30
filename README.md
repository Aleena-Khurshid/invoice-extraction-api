# Invoice Extraction API

Send invoice text to the API and get back structured JSON: invoice number, date, vendor, buyer, subtotal, tax, total, and warnings when the numbers do not add up. Built for small businesses that re-type paper and PDF invoices into spreadsheets.

## Pipeline

```
invoice text ──► extract_fields()  ──►  validate()  ──►  SQLite store  ──►  JSON response
                 (regex rules)          (sub + tax = total?)
```

| File | Responsibility |
|---|---|
| `app/extractor.py` | Regex rules that find labelled fields and parse amounts and dates |
| `app/validation.py` | Business checks: required fields, arithmetic, negative totals |
| `app/schemas.py` | Pydantic models for the request and the invoice |
| `app/store.py` | Saves invoices to SQLite |
| `app/main.py` | FastAPI endpoints |
| `evaluation/synthetic.py` | Generates invoices with the correct answers |
| `evaluation/evaluate.py` | Field-level accuracy and exact-match metrics |

## Setup

Requires Python 3.12 (3.10+ works for local runs).

```bash
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload      # docs at http://127.0.0.1:8000/docs
```

Examples:
```bash
curl -H "Content-Type: application/json" \
     -d '{"text":"Invoice No: INV-9\nDate: 10/04/2026\nFrom: Indus Office Supplies\nBill To: Northwind Clinic\nSubtotal: Rs. 2,000.00\nGST (17%): Rs. 340.00\nGrand Total: Rs. 2,340.00"}' \
     http://127.0.0.1:8000/extract/text

curl -F "file=@invoice.txt" http://127.0.0.1:8000/extract/file
curl http://127.0.0.1:8000/invoices
```

## Tests and evaluation

```bash
pytest -q                                        # 19 tests
python -m evaluation.evaluate                    # prints the accuracy table
python -m evaluation.evaluate --min-accuracy 0.90   # fails if in-scope accuracy drops
```

## Evaluation

### Dataset
90 synthetic invoices, 30 per layout, generated with a fixed seed (`evaluation/synthetic.py`). Vendor and buyer names are invented. Each invoice has its true values stored, so every prediction can be checked.

| Layout | What it is | Why it is in the test |
|---|---|---|
| `standard` | Labels like "Invoice No", "Grand Total", lakh commas (1,25,000) | Typical Pakistani format |
| `alt` | Labels like "Invoice #", "Total Amount", western commas | Different wording, same meaning |
| `unseen` | Labels like "Reference", "Net Amount", "VAT", "Dated" | Labels the rules were NOT written for |

### Metrics
- **Field accuracy:** share of (invoice, field) pairs extracted correctly. Amounts are compared to 2 decimal places, dates as ISO dates, text ignoring case and spaces at the edges.
- **Exact match:** share of invoices where all 8 fields are correct.

### Results

| Field | standard | alt | unseen |
|---|---|---|---|
| invoice_number | 1.00 | 1.00 | 0.00 |
| invoice_date | 1.00 | 1.00 | 0.00 |
| currency | 1.00 | 1.00 | 1.00 |
| vendor_name | 1.00 | 1.00 | 1.00 |
| buyer_name | 1.00 | 1.00 | 1.00 |
| subtotal | 1.00 | 1.00 | 0.00 |
| tax_amount | 1.00 | 1.00 | 0.00 |
| total | 1.00 | 1.00 | 1.00 |
| **Exact match** | 1.00 | 1.00 | 0.00 |

Field accuracy: standard 1.00, alt 1.00, unseen 0.50.

### How to read these numbers honestly
- **The 1.00 on standard and alt is not a real-world score.** I wrote the rules while looking at those two layouts, so they fit them by design. Real invoices will have labels, line breaks and OCR noise I have not seen.
- **The 0.50 on unseen is the more honest number.** It shows the weakness of rule-based extraction: a label you did not plan for is silently missed (the invoice number, date, subtotal and tax become None). The validation step flags the missing values as warnings, so the API does not hide them.
- **Next measurement:** collect 30 to 50 real or realistic invoices from different layouts, label them yourself, and measure before and after adding an LLM extractor.

## Validation: why it matters
The arithmetic check (`subtotal + tax = total`) catches errors that the regex cannot see. For example, an OCR error that turns 1,250 into 1,260 gives a warning instead of a wrong number saved silently. Tests cover this in `tests/test_validation.py` and `tests/test_api.py`.

## Design decisions
- **Regex first, LLM later.** Rules are fast, free, and easy to explain. Their limits are measured above.
- **Lakh-aware amounts.** Removing all commas handles both 1,25,000 and 125,000.
- **Lookbehinds in the total pattern.** `(?<!sub)` stops "Subtotal" from being read as the total.
- **SQLite.** No server to install, and enough for this scale. A production system would use PostgreSQL.
- **Store the result even with warnings.** The user can review and correct it later.

## Limitations
- Only English labels. Urdu labels and Urdu text are not supported.
- Only `.txt` input for the file endpoint. Scanned images or PDFs need OCR first (for example Tesseract), which is not included in this version.
- No line-item extraction (product rows). Only header fields and totals.
- GST is set at 17% in the test data. Check the current FBR rates before using the numbers for real tax.
- Rules fail on unseen labels (see the table above).

## Roadmap
1. Add OCR for scanned images (Tesseract via pytesseract, or Gemini vision).
2. Add an LLM extractor with Pydantic structured output, and compare it to the rules on the same test set.
3. Extract line items.
4. Deploy with Docker (`Dockerfile` included) and move SQLite to PostgreSQL.
