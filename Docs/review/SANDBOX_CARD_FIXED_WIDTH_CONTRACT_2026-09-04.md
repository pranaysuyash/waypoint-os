# Sandbox Card Fixed-Width Contract — 2026-09-04

## Finding

The full backend gate exposed a probabilistic sandbox defect in
`spine_api/providers/stripe_issuing_adapter.py`: converting a random
hexadecimal nibble to decimal and slicing the string could yield a one-, two-,
or three-character `last4` value. The contract requires exactly four decimal
digits.

## Implementation

`last4` now uses a bounded decimal value with explicit zero-padding:

```python
f"{int(uuid.uuid4().hex[:4], 16) % 10000:04d}"
```

The same invariant is propagated into the sandbox `ephemeral_pan`. No live
Stripe call, credential, or production-card claim is made; this is a local
simulator shape contract only.

## Verification

- `PYTHONPATH=. .venv/bin/pytest -q tests/test_sandbox_provider_adapters.py`
  → **14 passed**.
- The regression pins a low-value UUID (`0001`) and verifies `last4 == "0001"`
  and the PAN suffix.
- Ruff passes for the adapter and test.
- The full backend gate was rerun after this correction and is green at
  **3,710 passed, 44 skipped, 0 failed** (eight known Python 3.13 fork
  warnings).

## Boundary

This closes the deterministic sandbox formatting defect. It does not prove
Stripe Issuing API compatibility, PCI compliance, live authorization,
treasury settlement, or any external provider behavior.
