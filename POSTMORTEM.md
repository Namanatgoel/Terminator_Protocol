# Post-Mortem: Terminator Protocol - What Broke & Why

## Overview
This document is an honest audit of every defect discovered during senior code review of the Razorpay Buildathon submission. It follows the standard Razorpay incident format: **What happened → Root cause → Fix → Prevention**.

---

## [P0] Silent data loss on synthetic seed

### What happened
Running `python test.py` appeared to succeed (printed "Generated 50 synthetic failed transactions"), but `SELECT COUNT(*) FROM failed_transactions` returned 0. The executor had nothing to process.

### Root cause
`db.get_connection()` returns a raw `sqlite3.connect()`. The Python `sqlite3` documentation states:

> If the body of the `with` statement finishes without exceptions, the transaction is committed. **If this commit fails, or if the body of the with statement raises an uncaught exception, the transaction is rolled back.**

The critical subtlety: the context manager calls `conn.commit()` on **exit if no exception** - but **only if a transaction was started by the connection**. A batch of `conn.execute(INSERT ...)` statements called through the context manager (not through `conn.cursor().execute`) will use SQLite's implicit transaction, and the auto-commit on `__exit__` only fires if the connection object initiated the transaction. When `DatabaseRepository.get_connection()` is called from external code (test.py, not from within the class itself), the auto-commit was not triggered.

The Phase 2 refactor of `test.py` stripped the explicit `cur.commit()` call while switching from `cur.execute()` to `conn.execute()`, introducing this silent bug.

### Fix
Added `conn.commit()` explicitly after the insert loop in `test.py::generate_synthetic_data`. The fix is a single line and is documented with an inline comment explaining _why_.

### Prevention
Any function that mutates data through a raw `get_connection()` reference must own its commit. The `DatabaseRepository` methods are safe because they use `with conn` which triggers auto-commit inside the class. External callers cannot rely on that.

---

## [P0] Goal divergence - no recovery metric

### What happened
The hackathon bar explicitly requires: *"Show measured money recovered across a batch."* The codebase had no concept of ₹ recovered vs ₹ at-risk. Judges would have had zero quantitative evidence of recovery.

### Root cause
The `amount` column was stored in `failed_transactions` but was never propagated to `audit_logs`. The executor only logged `action` and `outcome` strings. There was no `recovery_report()` function.

### Fix
- `audit_logs` now stores `amount`, `ai_reasoning`, and `offer_authorized`.
- `DatabaseRepository.recovery_report()` computes total at-risk, recovered, in-flight, and lost from DB state.
- `report.py` surfaces this as a human-readable CLI report.
- `dashboard/index.html` renders it visually.

---

## [P1] LLM hallucination accepted silently

### What happened
`ActionDecision.action` was typed as `str`. A hallucinating LLM returning `action="escalate_to_human"` would pass Pydantic validation. The executor would silently log "Unknown action triggered" and still advance the tier - burning a recovery opportunity.

### Root cause
`str` is the wrong constraint for an enumerated finite state machine. This is a type-system design error.

### Fix
Changed to `Literal["silent_retry", "whatsapp_ping", "voice_call", "fomo_alert"]`. Pydantic v2 now rejects invalid values at parse time, which triggers the retry loop and eventually the `ActionDecision.fallback()` path.

---

## [P1] Network failure consumed escalation tiers

### What happened
If the vLLM server was unreachable (chaos test scenario), all 3 retry attempts failed, the fallback `ActionDecision` was returned, and the executor still incremented `tier += 1`. After 4 failures the transaction was marked `hard_failed` - revenue declared lost due to a connectivity issue, not an actual business decision.

### Root cause
`next_tier = tier + 1` was unconditional. The executor had no concept of whether the decision came from the LLM or from an error fallback.

### Fix
Added `is_fallback: bool` field to `ActionDecision`. The fallback factory `ActionDecision.fallback()` sets it to `True`. The executor now uses:
```python
next_tier = tier + (0 if decision.is_fallback else 1)
```
Network blips no longer burn escalation tiers.

---

## [P2] `message_queue.py` blocked startup

### What happened
`MessageQueue.__init__` eagerly instantiated `Producer({'bootstrap.servers': ...})`. When Redpanda was not running (the standard local-demo case), the constructor attempted a broker connection and hung for ~5 seconds, polluting startup logs and confusing observers into thinking the executor was hung.

### Root cause
Eager initialization of an external resource dependency in `__init__`.

### Fix
Lazy-initialized the producer via a `@property` that creates it on first `enqueue()` call. The `MessageQueue` object now constructs instantly, and connection errors are caught and logged as structured JSON warnings - not crashes.

---

## [P2] `queue.py` shadowed Python stdlib

### What happened
The file `queue.py` in the project root shadowed Python's standard library `queue` module. When `torch` attempted to import `dataloader.py` (which imports `import queue`), it resolved to the project file, which tried to import `confluent_kafka` - crashing `torch` with `ModuleNotFoundError`. This made it impossible to check CUDA availability.

### Root cause
A filename collision between a project module and a Python stdlib module.

### Fix
Renamed to `message_queue.py` and updated all import sites.
