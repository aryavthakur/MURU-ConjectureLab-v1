# CE interface adjudication, Design B: scope-closure record

Date: 2026-09-19. Status: CANCELLED, NEVER EXECUTED.

This is a project-scope constraint, not a scientific result. Nothing here says anything about K1, K2 or K3.

## What is preserved

- Freeze ref `refs/muru-freeze/muru-ce-interface-adjudication-design-b` stays at `4d4a492` (local and origin), unchanged.
- Every historical Design B file (plan, sourcing screen, preregistration, eligible universe, ordered queues, freeze
  manifest, code, tests) stays in the tree. Nothing was deleted or rewritten.

## Execution ledger at cancellation

| Item | Count |
|---|---|
| Procurement decisions (rows in `design_b/procurement/verification_log.csv`, which was never created) | 0 |
| Compounds ordered | 0 |
| Vendors contacted | 0 |
| Physical samples received | 0 |
| Design B spectra acquired or read | 0 |
| Design B predictions generated | 0 |
| Later refs created (`refs/muru-procurement/`, `refs/muru-spectra/`, `refs/muru-predictions/` for this study) | 0 |

The sourcing screen's `vendor_spot_check.csv` was read from public catalogue web pages; it was not a vendor contact.

## Why it is cancelled

From 2026-09-19 MURU is computational and online/public-data only: no wet-lab experiment, no compound purchasing,
no vendor outreach, no physical samples, no new mass-spectrometer acquisition. Design B needs all of these, so it
cannot run under the project's scope. Procurement must not be resumed under any circumstance.

## Gate

`scripts/ce_interface_adjudication/design_b/_scope_gate.py` defines `refuse()`, and it is now the first statement
of `main()` in steps 10, 20, 30, 35, 40, 45, 50, 60 and 90. It raises unconditionally; there is no override
variable. Step 01 (a read-only audit of committed metadata) is left as is. The Design B unit tests still pass
because they exercise pure functions, not `main()`. These edits change the script hashes relative to the Design B
freeze manifest by design: the manifest at `4d4a492` remains the record of what was frozen.

## Standing of the adjudication

Design A (freeze `518190b`, result `de3a1c2`) remains formally INTERFACE UNRESOLVED. PR #8 stays CLOSED and
EXPOSED and is never recomputed under any convention. The public-data follow-up is the C02 high-mass replication
(`MURU_CE_INTERFACE_ADJUDICATION_HIGH_MASS_REPLICATION_*`), which is not a replacement for Design B.
