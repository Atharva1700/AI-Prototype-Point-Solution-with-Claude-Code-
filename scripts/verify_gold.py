"""Checks the policy against the hand-labelled gold claims in data/gold_claims.csv.

A claim passes only if the verdict AND the set of triggered rule IDs both match.
Exit code is non-zero on any mismatch.
"""

import csv
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.policy import check_claim  # noqa: E402

GOLD = ROOT / "data" / "gold_claims.csv"


def build(row, today):
    expense_date = today - timedelta(days=int(row["days_before_today"]))
    claim = {
        "employee": row["employee"],
        "merchant": row["merchant"],
        "category": row["category"],
        "amount": Decimal(row["amount"]),
        "expense_date": expense_date,
        "has_receipt": row["has_receipt"] == "yes",
    }
    history = []
    same_day_meals = Decimal(row["history_meals_same_day"])
    if same_day_meals > 0:
        history.append({**claim, "merchant": "earlier meal", "category": "meals",
                        "amount": same_day_meals, "has_receipt": True})
    if row["history_duplicate"] == "yes":
        history.append({**claim, "has_receipt": True})
    return claim, history


def rule_ids(reasons):
    return {r.split(":")[0] for r in reasons}


def main():
    today = date.today()
    with open(GOLD, newline="") as f:
        rows = list(csv.DictReader(f))

    mismatches = 0
    for row in rows:
        claim, history = build(row, today)
        got = check_claim(claim, history, today)
        expected_rules = set(filter(None, row["expected_rules"].split(",")))
        ok = got["verdict"] == row["expected_verdict"] and rule_ids(got["reasons"]) == expected_rules
        if not ok:
            mismatches += 1
            print(f"MISMATCH {row['case_id']}: expected {row['expected_verdict']} {sorted(expected_rules)}, "
                  f"got {got['verdict']} {sorted(rule_ids(got['reasons']))}")

    print(f"{len(rows) - mismatches}/{len(rows)} gold claims match")
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
