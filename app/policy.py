"""Expense claim policy rules. Each rule is labelled with its requirement ID (see requirements.md)."""

from datetime import date
from decimal import Decimal

CATEGORIES = {"travel", "meals", "lodging", "supplies"}
RECEIPT_THRESHOLD = Decimal("25.00")       # P1
MAX_AGE_DAYS = 60                          # P2
MEAL_DAILY_LIMIT = Decimal("75.00")        # P3
PRE_APPROVAL_LIMIT = Decimal("500.00")     # P4
CENT = Decimal("0.01")
MAX_AMOUNT = Decimal("1000000000")         # larger values are invalid input (also avoids Decimal overflow)


def amount_is_valid(amount: Decimal) -> bool:
    """P6. Checked before any other comparison: NaN and overflow raise when compared or quantized."""
    if not amount.is_finite() or amount <= 0 or amount >= MAX_AMOUNT:
        return False
    return amount == amount.quantize(CENT)


def check_claim(claim: dict, history: list[dict], today: date) -> dict:
    rejected: list[str] = []
    review: list[str] = []

    amount = claim["amount"]
    amount_ok = amount_is_valid(amount)
    if not amount_ok:
        rejected.append("P6: amount must be positive with at most 2 decimal places")

    if claim["category"] not in CATEGORIES:
        rejected.append("P5: category must be travel, meals, lodging or supplies")

    age = (today - claim["expense_date"]).days
    if age < 0 or age > MAX_AGE_DAYS:
        rejected.append("P2: claim must be dated within 60 days of today")

    if amount_ok:
        review.extend(_amount_rules(claim, history, amount))

    if rejected:
        verdict = "rejected"
    elif review:
        verdict = "needs_review"
    else:
        verdict = "approved"
    return {"verdict": verdict, "reasons": rejected + review}


def _amount_rules(claim: dict, history: list[dict], amount: Decimal) -> list[str]:
    """P1, P3, P4, P7. Only run for a valid amount."""
    review: list[str] = []

    if amount > RECEIPT_THRESHOLD and not claim["has_receipt"]:
        review.append("P1: receipt required for claims over 25.00")

    if claim["category"] == "meals":
        same_day = sum(
            h["amount"] for h in history
            if h["employee"] == claim["employee"]
            and h["expense_date"] == claim["expense_date"]
            and h["category"] == "meals"
        )
        if same_day + amount > MEAL_DAILY_LIMIT:
            review.append("P3: meal total for this day is over 75.00")

    if amount > PRE_APPROVAL_LIMIT:
        review.append("P4: claim over 500.00 needs pre-approval")

    for h in history:
        if (h["employee"] == claim["employee"] and h["merchant"] == claim["merchant"]
                and h["expense_date"] == claim["expense_date"] and h["amount"] == amount):
            review.append("P7: possible duplicate of an earlier claim")
            break
    return review
