"""Rule-level tests. One or more tests per requirement in requirements.md."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.policy import check_claim

TODAY = date(2026, 10, 15)


def claim(**overrides):
    base = {
        "employee": "E1", "merchant": "Shop", "category": "supplies",
        "amount": Decimal("10.00"), "expense_date": TODAY, "has_receipt": True,
    }
    base.update(overrides)
    return base


def rule_ids(result):
    return {r.split(":")[0] for r in result["reasons"]}


def test_clean_claim_is_approved():
    assert check_claim(claim(), [], TODAY) == {"verdict": "approved", "reasons": []}


# P1
def test_p1_receipt_required_over_25():
    assert rule_ids(check_claim(claim(amount=Decimal("25.01"), has_receipt=False), [], TODAY)) == {"P1"}


def test_p1_exactly_25_needs_no_receipt():
    assert check_claim(claim(amount=Decimal("25.00"), has_receipt=False), [], TODAY)["verdict"] == "approved"


# P2
def test_p2_60_days_old_is_allowed():
    assert check_claim(claim(expense_date=TODAY - timedelta(days=60)), [], TODAY)["verdict"] == "approved"


def test_p2_61_days_old_is_rejected():
    result = check_claim(claim(expense_date=TODAY - timedelta(days=61)), [], TODAY)
    assert result["verdict"] == "rejected" and rule_ids(result) == {"P2"}


def test_p2_future_date_is_rejected():
    assert check_claim(claim(expense_date=TODAY + timedelta(days=1)), [], TODAY)["verdict"] == "rejected"


# P3
def meal(amount, day=TODAY, employee="E1"):
    return claim(employee=employee, category="meals", amount=Decimal(amount), expense_date=day,
                 merchant="earlier")


def test_p3_meal_total_of_exactly_75_is_allowed():
    result = check_claim(meal("25.00"), [meal("50.00")], TODAY)
    assert result["verdict"] == "approved"


def test_p3_meal_total_over_75_needs_review():
    result = check_claim(meal("25.01"), [meal("50.00")], TODAY)
    assert result["verdict"] == "needs_review" and rule_ids(result) == {"P3"}


def test_p3_ignores_other_employees_and_other_days():
    history = [meal("70.00", employee="E2"), meal("70.00", day=TODAY - timedelta(days=1))]
    assert check_claim(meal("20.00"), history, TODAY)["verdict"] == "approved"


# P4
def test_p4_exactly_500_is_allowed_and_500_01_needs_review():
    assert check_claim(claim(amount=Decimal("500.00")), [], TODAY)["verdict"] == "approved"
    result = check_claim(claim(amount=Decimal("500.01")), [], TODAY)
    assert result["verdict"] == "needs_review" and rule_ids(result) == {"P4"}


# P5
@pytest.mark.parametrize("category", ["Meals", "fitness", "", "travel "])
def test_p5_unknown_category_is_rejected(category):
    result = check_claim(claim(category=category), [], TODAY)
    assert result["verdict"] == "rejected" and "P5" in rule_ids(result)


# P6
@pytest.mark.parametrize("amount", [Decimal("0"), Decimal("-0.01"), Decimal("10.005"),
                                    Decimal("NaN"), Decimal("Infinity"), Decimal("1e30")])
def test_p6_invalid_amounts_are_rejected_without_crashing(amount):
    result = check_claim(claim(amount=amount), [], TODAY)
    assert result["verdict"] == "rejected" and rule_ids(result) == {"P6"}


# P7
def test_p7_duplicate_needs_review():
    result = check_claim(claim(), [claim()], TODAY)
    assert result["verdict"] == "needs_review" and rule_ids(result) == {"P7"}


def test_p7_different_merchant_is_not_a_duplicate():
    assert check_claim(claim(), [claim(merchant="Other")], TODAY)["verdict"] == "approved"


# Verdict precedence
def test_rejected_beats_needs_review_and_both_reasons_are_reported():
    result = check_claim(claim(amount=Decimal("600.00"), category="fitness"), [], TODAY)
    assert result["verdict"] == "rejected"
    assert rule_ids(result) == {"P4", "P5"}
