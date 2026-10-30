"""FastAPI service.

Run:  uvicorn app.main:app --reload
Docs: http://127.0.0.1:8000/docs
"""

import os

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.extractor import extract_fields
from app.schemas import Invoice, TextRequest
from app.store import InvoiceStore
from app.validation import validate

MAX_UPLOAD_BYTES = 1_000_000


def process_text(text: str, store: InvoiceStore) -> Invoice:
    """The whole pipeline: extract -> validate -> save."""
    fields = extract_fields(text)
    invoice = Invoice(**fields, warnings=validate(fields))
    invoice_id = store.save(invoice)
    return invoice.model_copy(update={"id": invoice_id})


def create_app(db_path: str | None = None) -> FastAPI:
    store = InvoiceStore(db_path or os.getenv("DB_PATH", "data/invoices.db"))
    app = FastAPI(title="Invoice Extraction API", version="0.1.0")
    app.state.store = store

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/extract/text", status_code=201, response_model=Invoice)
    def extract_from_text(body: TextRequest):
        return process_text(body.text, app.state.store)

    @app.post("/extract/file", status_code=201, response_model=Invoice)
    async def extract_from_file(file: UploadFile = File(...)):
        if not (file.filename or "").lower().endswith(".txt"):
            raise HTTPException(status_code=400, detail="Only .txt files are supported")
        raw = await file.read()
        if len(raw) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="File is larger than 1 MB")
        return process_text(raw.decode("utf-8", errors="replace"), app.state.store)

    @app.get("/invoices", response_model=list[Invoice])
    def list_invoices(limit: int = 50):
        return app.state.store.list(limit=min(max(limit, 1), 200))

    @app.get("/invoices/{invoice_id}", response_model=Invoice)
    def get_invoice(invoice_id: int):
        invoice = app.state.store.get(invoice_id)
        if invoice is None:
            raise HTTPException(status_code=404, detail="Invoice not found")
        return invoice

    return app


app = create_app()
