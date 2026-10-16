# AI Prototype: Expense Claim Policy Check

A FastAPI service that replaces a manual nine-step checklist for expense claims with
one API call. It is a point solution: one process, one rule set, one endpoint.

The first implementation was drafted by an AI assistant from `requirements.md`. Each
artifact was then checked against its requirement before it was treated as done. The
checks, the defects they found, and the fixes are in `docs/verification_log.md`.

## Files

```
requirements.md             Policy rules P1–P7 and the verdict logic (written before the code)
app/policy.py               The rules, each labelled with its requirement ID
app/main.py                 FastAPI app: POST /claims/check, GET /health
data/gold_claims.csv        40 hand-labelled claims, written before the code
scripts/verify_gold.py      Checks the policy against the gold labels
scripts/benchmark.py        Time per claim on a fixed 2,000-claim batch
tests/test_policy.py        Rule-level tests for each requirement
tests/test_api.py           API tests, including regression tests for two defects
docs/verification_log.md    What each verification step found
docs/before_after.md        Measured results, and the comparison still to measure
```

## Run

```bash
pip install fastapi uvicorn httpx pytest
python3 -m pytest
python3 scripts/verify_gold.py
python3 scripts/benchmark.py
uvicorn app.main:app --reload     # then POST to /claims/check
```

Example request:

```json
{
  "claim": {"employee": "E1", "merchant": "Cafe", "category": "meals",
            "amount": "30.00", "expense_date": "2026-10-15", "has_receipt": true},
  "history": []
}
```

## Results

- 32 tests pass.
- 40 of 40 hand-labelled claims match, on both verdict and triggered rules.
- Verification found two defects (NaN and overflow amounts returned HTTP 500). Both are
  fixed, and regression tests fail if either fix is reverted.
- About 0.016 ms per claim for the policy and 2.4 ms per claim over HTTP, in-process.

The reviewer-time and manual-agreement comparison has not been measured. It is listed
as "to measure" in `docs/before_after.md`, with the steps to complete it.

## Limits

- The policy is invented for this project. Real expense policies have more exceptions.
- The history passed in the request is the only source of duplicate and daily-total
  checks. A real system would query its own store.
- Category matching is case-sensitive, as the requirement is written. This is an open
  decision for the process owner.
