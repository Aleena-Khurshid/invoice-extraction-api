import pytest
from fastapi.testclient import TestClient

from app.main import create_app

SAMPLE = """Invoice No: INV-9
Date: 10/04/2026
From: Indus Office Supplies
Bill To: Northwind Clinic
Subtotal: Rs. 2,000.00
GST (17%): Rs. 340.00
Grand Total: Rs. 2,340.00
"""


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(db_path=str(tmp_path / "test.db")))


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_extract_text_saves_and_returns_invoice(client):
    response = client.post("/extract/text", json={"text": SAMPLE})
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["invoice_number"] == "INV-9"
    assert body["total"] == 2340.0
    assert body["warnings"] == []


def test_extract_file_accepts_txt(client):
    response = client.post(
        "/extract/file",
        files={"file": ("invoice.txt", SAMPLE.encode(), "text/plain")},
    )
    assert response.status_code == 201
    assert response.json()["vendor_name"] == "Indus Office Supplies"


def test_extract_file_rejects_other_types(client):
    response = client.post("/extract/file", files={"file": ("scan.pdf", b"%PDF", "application/pdf")})
    assert response.status_code == 400


def test_get_and_list_invoices(client):
    client.post("/extract/text", json={"text": SAMPLE})
    assert client.get("/invoices/1").json()["invoice_number"] == "INV-9"
    assert len(client.get("/invoices").json()) == 1
    assert client.get("/invoices/999").status_code == 404


def test_short_text_is_rejected(client):
    assert client.post("/extract/text", json={"text": "hi"}).status_code == 422


def test_bad_arithmetic_returns_warning(client):
    bad = SAMPLE.replace("2,340.00", "2,999.00")
    body = client.post("/extract/text", json={"text": bad}).json()
    assert any("does not match" in w for w in body["warnings"])
