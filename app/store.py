"""Save extracted invoices in SQLite (a file-based database built into Python)."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.schemas import Invoice

SCHEMA = """
CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    invoice_number TEXT,
    total REAL,
    payload TEXT NOT NULL
)
"""


class InvoiceStore:
    def __init__(self, path: str):
        self.path = path
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        conn = self._connect()
        try:
            with conn:
                conn.execute(SCHEMA)
        finally:
            conn.close()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def save(self, invoice: Invoice) -> int:
        conn = self._connect()
        try:
            with conn:  # commits on success, rolls back on error
                cur = conn.execute(
                    "INSERT INTO invoices (created_at, invoice_number, total, payload) VALUES (?, ?, ?, ?)",
                    (
                        datetime.now(timezone.utc).isoformat(),
                        invoice.invoice_number,
                        invoice.total,
                        invoice.model_dump_json(exclude={"id"}),
                    ),
                )
                return cur.lastrowid
        finally:
            conn.close()

    def get(self, invoice_id: int) -> Invoice | None:
        conn = self._connect()
        try:
            row = conn.execute("SELECT id, payload FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
        finally:
            conn.close()
        if row is None:
            return None
        return Invoice.model_validate_json(row["payload"]).model_copy(update={"id": row["id"]})

    def list(self, limit: int = 50) -> list[Invoice]:
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT id, payload FROM invoices ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        finally:
            conn.close()
        return [
            Invoice.model_validate_json(r["payload"]).model_copy(update={"id": r["id"]}) for r in rows
        ]
