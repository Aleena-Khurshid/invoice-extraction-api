"""Data shapes for the API. Pydantic checks types and converts values for us."""

from datetime import date

from pydantic import BaseModel, Field


class Invoice(BaseModel):
    """One extracted invoice. Every field may be None if it was not found."""

    id: int | None = None
    invoice_number: str | None = None
    invoice_date: date | None = None
    currency: str | None = None
    vendor_name: str | None = None
    buyer_name: str | None = None
    subtotal: float | None = None
    tax_amount: float | None = None
    total: float | None = None
    warnings: list[str] = Field(default_factory=list)


class TextRequest(BaseModel):
    text: str = Field(min_length=10, max_length=200_000)
