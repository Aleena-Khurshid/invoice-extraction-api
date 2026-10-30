"""Field-level extraction evaluation.

Metrics:
  Field accuracy : share of (invoice, field) pairs where the extracted value
                   equals the true value. Values are normalised first
                   (amounts rounded to 2 dp, dates as ISO, text trimmed and case-folded).
  Exact match    : share of invoices where ALL 8 fields are correct.

Run:  python -m evaluation.evaluate
      python -m evaluation.evaluate --min-accuracy 0.90   (exit 1 if standard+alt is below)
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

from app.extractor import extract_fields
from evaluation.synthetic import generate_dataset

FIELDS = ["invoice_number", "invoice_date", "currency", "vendor_name",
          "buyer_name", "subtotal", "tax_amount", "total"]
RESULTS_DIR = Path(__file__).parent / "results"
IN_SCOPE = {"standard", "alt"}  # layouts the rules were written for


def normalise(value):
    if value is None:
        return None
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float):
        return round(value, 2)
    if isinstance(value, str):
        return value.strip().casefold()
    return value


def evaluate(items: list[dict]) -> dict:
    correct = defaultdict(lambda: defaultdict(int))  # family -> field -> count
    totals = defaultdict(int)                        # family -> invoice count
    exact = defaultdict(int)                         # family -> all-fields-correct count
    for item in items:
        family = item["family"]
        predicted = extract_fields(item["text"])
        totals[family] += 1
        all_ok = True
        for field in FIELDS:
            ok = normalise(predicted.get(field)) == normalise(item["truth"][field])
            correct[family][field] += ok
            all_ok &= ok
        exact[family] += all_ok
    return {"correct": correct, "totals": totals, "exact": exact}


def report(result: dict) -> tuple[str, dict]:
    families = list(result["totals"])
    header = "| Field | " + " | ".join(families) + " |\n|---|" + "---|" * len(families) + "\n"
    rows = ""
    for field in FIELDS:
        cells = [f"{result['correct'][f][field] / result['totals'][f]:.2f}" for f in families]
        rows += f"| {field} | " + " | ".join(cells) + " |\n"
    exact_cells = [f"{result['exact'][f] / result['totals'][f]:.2f}" for f in families]
    rows += "| **All fields (exact match)** | " + " | ".join(exact_cells) + " |\n"

    summary = {}
    for family in families:
        n = result["totals"][family]
        summary[family] = {
            "invoices": n,
            "field_accuracy": sum(result["correct"][family][f] for f in FIELDS) / (n * len(FIELDS)),
            "exact_match": result["exact"][family] / n,
        }
    return header + rows, summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate invoice field extraction")
    parser.add_argument("--min-accuracy", type=float, default=None,
                        help="Fail if field accuracy on in-scope layouts is below this")
    args = parser.parse_args(argv)

    items = generate_dataset(per_family=30, seed=42)
    result = evaluate(items)
    table, summary = report(result)

    print(f"Invoices: {len(items)} across {len(result['totals'])} layouts\n")
    print(table)
    for family, s in summary.items():
        print(f"{family:9s} field accuracy {s['field_accuracy']:.3f} | "
              f"exact match {s['exact_match']:.3f} | n={s['invoices']}")

    in_scope = [s["field_accuracy"] for f, s in summary.items() if f in IN_SCOPE]
    in_scope_accuracy = sum(in_scope) / len(in_scope)
    print(f"\nIn-scope layouts (standard + alt) mean field accuracy: {in_scope_accuracy:.3f}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "results.md").write_text(table, encoding="utf-8")
    (RESULTS_DIR / "results.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    if args.min_accuracy is not None and in_scope_accuracy < args.min_accuracy:
        print(f"FAIL: {in_scope_accuracy:.3f} < {args.min_accuracy:.2f}")
        return 1
    if args.min_accuracy is not None:
        print(f"PASS: {in_scope_accuracy:.3f} >= {args.min_accuracy:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
