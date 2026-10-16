# Expense claim policy check: requirements

The manual process: a reviewer opens each claim, checks it against a nine-item
checklist in a spreadsheet, and records a verdict by hand. This prototype replaces
that checklist with an API call.

Money is in dollars, to two decimal places.

**P1 Receipt.** A claim over 25.00 needs a receipt. Without one it is `needs_review`.

**P2 Age.** A claim must be dated no more than 60 days before today. Older claims are
`rejected`. A date in the future is also `rejected`.

**P3 Meal limit.** Meal claims by one employee on one date may total at most 75.00.
If the total with this claim is over 75.00, the claim is `needs_review`.

**P4 Pre-approval.** A single claim over 500.00 needs pre-approval. It is `needs_review`.

**P5 Category.** The category must be one of: travel, meals, lodging, supplies.
Anything else is `rejected`.

**P6 Amount.** The amount must be positive and have at most two decimal places.
Otherwise it is `rejected`.

**P7 Duplicate.** A claim with the same employee, merchant, date, and amount as an
earlier claim in the history is `needs_review`.

**Verdict.** Any `rejected` rule makes the verdict `rejected`. Otherwise any
`needs_review` rule makes it `needs_review`. Otherwise it is `approved`. Every
triggered rule appears in `reasons`, prefixed with its rule ID.
