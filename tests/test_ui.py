from pathlib import Path

from streamlit.testing.v1 import AppTest

UI_FILE = str(Path(__file__).resolve().parents[1] / "app" / "ui.py")

SAMPLE = (
    "Invoice No: INV-9\nDate: 10/04/2026\nFrom: Indus Office Supplies\n"
    "Bill To: Northwind Clinic\nSubtotal: Rs. 2,000.00\nGST (17%): Rs. 340.00\n"
    "Grand Total: Rs. 2,340.00\n"
)


def test_ui_starts_without_errors(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "ui.db"))
    at = AppTest.from_file(UI_FILE, default_timeout=30).run()
    assert not at.exception


def test_extract_button_saves_and_shows_success(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "ui.db"))
    at = AppTest.from_file(UI_FILE, default_timeout=30).run()
    at.text_area[0].input(SAMPLE).run()
    extract = next(b for b in at.button if b.label == "Extract")
    extract.click().run()
    assert not at.exception
    assert any("All checks passed" in s.value for s in at.success)
