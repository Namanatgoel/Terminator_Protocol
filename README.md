# The Terminator Protocol — AI Revenue Recovery

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![Razorpay Buildathon](https://img.shields.io/badge/Razorpay-Buildathon_2026-blueviolet.svg)](https://razorpay.com/buildathon/)

**Track 03: AI Revenue Recovery** — Find revenue that's slipping away and win it back.

---

## What It Does

The Terminator Protocol is an AI-driven revenue recovery agent that detects failed transactions, diagnoses the root cause, and executes a compliant escalation workflow until money is recovered or a hard terminal decision is made.

Each failed transaction moves through four tiers of escalation, with an LLM routing every step:

| Tier | Action | Trigger |
|------|--------|---------|
| 1 | Silent retry via Redpanda | Transient network/funds failure |
| 2 | Razorpay UPI deep-link via WhatsApp | Repeated failure, user reachable |
| 3 | Retell AI voice negotiation | High-value or price-sensitive user |
| 4 | FOMO email/SMS | All soft channels exhausted |

Every decision, amount, and AI reasoning is written to an immutable audit log. A recovery report quantifies **₹ recovered vs ₹ at-risk** across the batch.

---

## Architecture

Seven modules, each with a single responsibility:

| File | Responsibility |
|------|---------------|
| `db.py` | `DatabaseRepository` — state machine, atomic batch locking, audit log, recovery metrics |
| `llm_engine.py` | `LLMRouter` + `ActionDecision` — GPU-accelerated routing with Pydantic validation and 3-retry resilience |
| `message_queue.py` | `MessageQueue` — Redpanda/Kafka delay queue with lazy producer init and structured error logging |
| `executor.py` | `ExecutorService` — orchestration loop with dependency injection and JSON-structured logs |
| `test.py` | Synthetic data seeder and audit log exporter |
| `report.py` | CLI recovery summary (₹ recovered vs ₹ at-risk) |
| `dashboard/index.html` | Standalone browser dashboard — load `audit_export.csv` to see live metrics |

**Local execution note:** SQLite replaces PostgreSQL for zero-dependency local evaluation. `BEGIN EXCLUSIVE` transactions simulate `FOR UPDATE SKIP LOCKED`. The upgrade path to PostgreSQL is documented in `db.py`.

---

## Setup

### Prerequisites
- [Conda](https://docs.conda.io/en/latest/miniconda.html)
- *(Optional, for real LLM routing)* vLLM with `Qwen/Qwen2.5-7B-Instruct-AWQ`. Without it, the system runs in **safe fallback mode** (all transactions route to `silent_retry`) and still demonstrates the full recovery workflow with audit trail and metrics.

### 1. Create the environment

```bash
conda env create -f environment.yml
conda activate RzpyBuild
```

### 2. Seed the database

```bash
python test.py
```

Inserts 50 synthetic failed transactions: `insufficient_funds`, `checkout_abandoned`, `card_declined`.

### 3. Run the recovery engine

```bash
python executor.py
```

Structured JSON logs stream to stdout. Each line records `txn_id`, `action`, `next_tier`, `amount`, and `is_fallback`.

> **Without vLLM running:** The LLM router retries 3 times then returns a conservative `silent_retry` fallback. Escalation tiers are **not advanced** on fallback — no revenue is incorrectly marked lost due to a connectivity issue. This behaviour is intentional and tested.

### 4. View the recovery report

```bash
python report.py
```

Prints ₹ recovered, ₹ at-risk, recovery rate %, and per-action volume breakdown.

### 5. Export the audit log

```bash
python -c "from test import export_audit_log; from db import DatabaseRepository; export_audit_log(DatabaseRepository())"
```

Writes `audit_export.csv` — load it in `dashboard/index.html` to visualise results.

### 6. Open the dashboard

Open `dashboard/index.html` in any browser. Click **Load audit_export.csv** to render live KPI cards, action distribution chart, and the full audit table with AI reasoning per row. No server required.

---

## Key Design Decisions

- **LLM on GPU, not CPU.** vLLM runs `Qwen-2.5-7B-Instruct-AWQ` with AWQ quantisation on RTX 5050. Temperature 0.0 for deterministic routing.
- **Pydantic `Literal` types on LLM output.** Any hallucinated action string fails at parse time and enters the retry loop — the state machine only accepts valid transitions.
- **Fallback does not advance tiers.** An `is_fallback: bool` field prevents network errors from burning escalation budget.
- **Audit trail stores AI reasoning.** `ai_reasoning` is written to `audit_logs` per decision — every rupee has an accountable rationale.
- **Kafka push before DB commit.** Enqueue-then-update ordering prevents silent task drops on mid-crash, at the cost of potential duplicates (documented as Transactional Outbox upgrade path).

---

## Security

All external service calls (Razorpay API, Twilio WhatsApp, Retell AI) are execution stubs. No real API keys exist in this repository. The LLM endpoint is `localhost:8000` — no network egress.

