# Library Management Module Review Notes

Date: 2026-03-01

## Findings

- Critical: Borrow flow will crash due to field mismatch. Model defines `customr_id` but code uses `customer_id` in `write()`.
  - `models/book.py:17`
  - `models/book.py:57`
  - `models/book.py:71`
- Critical: `write()` returns inside the loop, so only the first record in batch writes is processed.
  - `models/book.py:49`
  - `models/book.py:81`
- Critical: Module uses `account.move` but `account` is missing from dependencies.
  - `models/book.py:20`
  - `__manifest__.py:5`
- High: Any write on a borrowed record can create duplicate picking and invoice records.
  - `models/book.py:51`
- High: Created picking/invoice are not linked back to `delivery_id` and `invoice_id`.
  - `models/book.py:19`
  - `models/book.py:20`
  - `models/book.py:56`
  - `models/book.py:69`
- High: Stored computed counters are missing `@api.depends(...)`, which can cause stale values.
  - `models/book.py:21`
  - `models/book.py:22`
  - `models/book.py:25`
- High: Access rights are too broad (full CRUD with no group restriction).
  - `security/ir.model.access.csv:2`
- Medium: Validation is incomplete (`quantity` can be zero/negative; required borrow fields not enforced).
  - `models/book.py:14`
  - `models/book.py:40`
- Medium: Action methods should enforce singleton and handle missing linked records safely.
  - `models/book.py:85`
  - `models/book.py:95`

## Instructions And Improvements

- Rename `customr_id` to `customer_id` everywhere.
- Add `'account'` to `depends` in `__manifest__.py`.
- Move borrow logic from `write()` into an explicit action method like `action_borrow()`.
- If using `write()` for state automation, run logic only when state transitions to `borrowed`.
- Move `return res` outside the `for record in self` loop in `write()`.
- Assign generated records to `delivery_id` and `invoice_id` after creation.
- Add `@api.depends('delivery_id', 'invoice_id')` to `_compute_counts` (or make counters non-stored).
- Add a constraint that `quantity > 0`.
- Enforce required values (`product_id`, `customer_id`) before borrow.
- Add `self.ensure_one()` in action methods and handle missing `delivery_id`/`invoice_id`.
- Restrict ACLs by groups (for example: librarian and manager) instead of global full access.
- Standardize naming and formatting for readability and maintainability.
- Add automated tests for:
  - Borrow success path.
  - Insufficient stock error.
  - No duplicate picking/invoice when editing non-state fields.

