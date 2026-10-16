"""API tests. Includes regression tests for two defects found during verification."""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, raise_server_exceptions=True)
TODAY = date.today()


def body(amount_json="10.00", expense_date=None):
    """Raw JSON text, so tests can send values json.dumps would refuse (NaN, Infinity)."""
    day = expense_date or TODAY.isoformat()
    return ('{"claim": {"employee": "E1", "merchant": "Shop", "category": "supplies", '
            '"amount": ' + amount_json + ', "expense_date": "' + day + '", "has_receipt": true}, '
            '"history": []}')


def post_raw(raw):
    return client.post("/claims/check", content=raw, headers={"content-type": "application/json"})


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_approved_claim_over_api():
    resp = post_raw(body("10.00"))
    assert resp.status_code == 200
    assert resp.json() == {"verdict": "approved", "reasons": []}


def test_needs_review_claim_over_api_with_history():
    raw = ('{"claim": {"employee":"E1","merchant":"Shop","category":"meals","amount":"30.00",'
           '"expense_date":"%s","has_receipt":true},'
           ' "history": [{"employee":"E1","merchant":"Other","category":"meals","amount":"50.00",'
           '"expense_date":"%s","has_receipt":true}]}') % (TODAY.isoformat(), TODAY.isoformat())
    resp = post_raw(raw)
    assert resp.json()["verdict"] == "needs_review"
    assert resp.json()["reasons"][0].startswith("P3")


def test_claim_older_than_60_days_is_rejected_over_api():
    old = (TODAY - timedelta(days=61)).isoformat()
    raw = body("10.00", expense_date=old)  # keyword form of the helper
    assert post_raw(raw).json()["verdict"] == "rejected"


# Regression: NaN made the error response itself fail to encode, returning HTTP 500.
@pytest.mark.parametrize("amount_json", ["NaN", "Infinity", "-Infinity"])
def test_regression_non_finite_amount_returns_422_not_500(amount_json):
    resp = post_raw(body(amount_json))
    assert resp.status_code == 422


# Regression: 1e30 overflowed Decimal's quantize, returning HTTP 500.
def test_regression_huge_amount_is_rejected_as_p6_not_500():
    resp = post_raw(body("1e30"))
    assert resp.status_code == 200
    assert resp.json()["verdict"] == "rejected"
    assert resp.json()["reasons"][0].startswith("P6")


def test_non_numeric_amount_is_422():
    assert post_raw(body('"abc"')).status_code == 422
