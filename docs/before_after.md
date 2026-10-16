# Before and After: Expense Claim Review

The manual process was a checklist in a spreadsheet, applied by a reviewer to each
claim. The prototype is one API call that applies the same nine checks. Values
marked **measured** come from this project. Values marked **to measure** need a time
study on the real team, because the operational improvement depends on them.

| Measure | Manual (before) | Prototype (after) | Status |
|---|---|---|---|
| Checks per claim | 9 (P1–P7, verdict, record) | 1 API call | Measured from requirements |
| Compute time per claim, policy only | not applicable | 0.016 ms | **Measured**, 2,000 claims |
| Round trip per claim, in-process HTTP | not applicable | 2.4 ms | **Measured**, same run |
| Reviewer time per claim | to measure | not applicable | **To measure** |
| Agreement with hand-labelled decisions | to measure | 40 of 40 | **Measured** on gold set |
| Errors on malformed input (HTTP 500) | not applicable | 0 after fixes, 3 before | **Measured** by probe |
| Verdict mix on the 2,000-claim batch | not applicable | approved 798, needs review 920, rejected 282 | **Measured** |

## What the numbers do and do not show

- The compute cost of the policy is negligible next to any human review time. The
  improvement that matters is reviewer time, which is not measured here.
- Agreement is measured against labels written from the same requirements. It shows
  the code follows the stated policy, not that the policy is correct, and nothing has
  been measured for the manual process's agreement.
- The 920 `needs_review` verdicts show how much work the prototype hands back to
  people. If most of them are approved on a human look, the time saved is smaller
  than it appears.

## To complete this comparison

1. Time 30 real claims through the manual checklist, recording minutes per claim.
2. Run the same 30 claims through the prototype and record the verdicts.
3. Have a reviewer check the prototype's verdicts for those 30 claims and record the
   disagreements.
4. Put the three figures in the table above in place of "to measure".
