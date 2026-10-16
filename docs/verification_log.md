# Verification Log

Each AI-drafted artifact was checked against the requirement it was meant to meet,
before it was treated as done. This log records what each check found, including
the failures.

## Artifact 1: policy rules (`app/policy.py`)

Drafted by the AI assistant from `requirements.md`.

| Step | Check | Result |
|---|---|---|
| 1 | Gold labels written from `requirements.md` before the code existed (40 claims) | Labels written first, so they are not derived from the code |
| 2 | Draft run against the gold labels (verdict and rule IDs both must match) | 40/40 match |
| 3 | Found by hand: gold case G34 was labelled wrong (55.00 + 20.00 = 75.00, which P3 allows) | Label corrected; the code was right |
| 4 | Edge-case probe the gold set did not cover: `NaN`, `Infinity`, `1e30` | **Defect:** `NaN` and `Infinity` returned HTTP 500 |
| 5 | Cause: amount comparisons and `quantize` raise on NaN; `1e30` overflows Decimal's quantize | Fixed: amount validated before any comparison; values at or above 10^9 treated as P6 |
| 6 | Probe again | `1e30` now returns a P6 rejection; `NaN` still returned 500 |
| 7 | Cause of the remaining 500: FastAPI's 422 error body echoes the bad input, and NaN cannot be encoded as JSON | Fixed: `Field(allow_inf_nan=False)` plus an error handler that omits the echoed input |
| 8 | Probe again | All malformed amounts return 422 or a P6 rejection; no 500s |

## Regression tests and the mutation check

Each defect has a regression test in `tests/test_api.py`. To confirm the tests catch
the defects, both fixes were reverted on a copy of the project. The regression tests
failed on exactly the cases they cover: `NaN`, `Infinity`, `-Infinity`, and `1e30`.

## What the checks did not cover

- The gold set uses clean inputs, which is why it passed before the probe found the
  NaN and overflow defects. Probing for bad input found what the labels missed.
- The category check is case-sensitive, so `Meals` is rejected. This follows the
  requirement as written, but the process owner may want case-insensitive matching.
  That decision is open.
- Pydantic handles type and format errors (`"abc"` gives 422). The policy handles
  business errors (`0.00` gives P6). Some inputs, such as a non-ASCII employee ID,
  were not checked.

## Limits of this verification

The same author wrote the requirements, the gold labels, and the code. The gold set
can only catch a disagreement between the labels and the code. A misreading of the
policy that is shared by both would not be caught.
