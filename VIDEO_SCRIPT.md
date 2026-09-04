# Terminator Protocol — 5-Minute Video Script
**Razorpay Buildathon 2026 | Track 03: AI Revenue Recovery**

---

## [0:00 – 0:30] Hook — The Problem

*[Screen: live Razorpay dashboard with a failing payment counter ticking up]*

**Narration:**
"Every second, payments fail. Cards decline. Checkouts get abandoned mid-flow. Subscriptions lapse.
Most systems log this. Some retry blindly. None of them think.

The question we asked was: what if an AI agent could close the entire loop — detect the failure, diagnose the reason, pick the exact right intervention, and execute it — automatically?"

*[Cut to: animated diagram of money slipping through a drain, then getting caught by an agent]*

"This is the Terminator Protocol."

---

## [0:30 – 1:30] The Architecture — What It Is

*[Screen: architecture diagram with 4 modules highlighted]*

**Narration:**
"The system is five Python modules.

**First — the Database layer.** Every failed transaction enters here with its error code, amount, and user ID. The table acts as a state machine: `pending → processing → pending → hard_failed`. We use SQLite's `BEGIN EXCLUSIVE` to simulate Postgres's `FOR UPDATE SKIP LOCKED` — atomic batch fetching with zero double-execution.

**Second — the LLM Router.** This is the brain. We run Qwen-2.5-7B locally via vLLM on the RTX 5050 — GPU-accelerated, deterministic, zero latency. The model receives the transaction context and outputs a routing decision: which of four actions to take, how long to wait, and whether to authorize a discount offer.

**Third — the Executor.** It fetches batches of five transactions, passes each to the LLM router, executes the action, and updates state. It uses structured JSON logging — every event is Datadog-ready.

**Fourth — the Message Queue.** Redpanda backs the delay queue. Escalations are pushed before the DB commit — an outbox pattern that prevents silent data loss.

**Fifth — the Recovery Report.** One command gives you ₹ recovered vs ₹ at-risk across the entire batch."

---

## [1:30 – 2:30] The Four Tiers — AI Judgment

*[Screen: escalation ladder diagram]*

**Narration:**
"The agent escalates through four tiers, and this is where AI judgment matters most.

**Tier 1 — Silent Retry.** The LLM detects a transient failure: insufficient funds, a network blip. It schedules a quiet retry in 60 minutes. No customer contact. No friction.

**Tier 2 — WhatsApp Ping.** The LLM sees this is a repeat failure — the card declined twice. It dispatches a Razorpay UPI deep-link via WhatsApp. One tap to pay.

**Tier 3 — Voice Negotiation.** Now the LLM reads the accumulated context. If prior interactions flagged price sensitivity — the user hesitated at the price point, mentioned affordability — the model authorises a 10% EMI offer and triggers a Retell AI voice call. The AI negotiates on Razorpay's behalf, in real time.

**Tier 4 — Final FOMO.** Last chance. An urgency-framed email and SMS hit simultaneously. After this, the transaction is marked `hard_failed` and accounted for as lost revenue."

---

## [2:30 – 3:30] Live Demo

*[Screen: terminal running `python test.py`, then `python executor.py`]*

**Narration:**
"Let me show you this running.

`python test.py` seeds 50 synthetic failed transactions — insufficient funds, abandoned checkouts, card declines — into the database."

*[Terminal output: "Seeded 50 synthetic failed transactions."]*

"Now the executor."

*[Terminal: structured JSON log lines scrolling — txn_id, action, next_tier, amount]*

"You can see every decision logged in machine-readable JSON. Action taken. Amount at risk. AI reasoning. Whether an offer was authorized.

Now — the number that matters."

*[Terminal: `python report.py`]*

```
═══════════════════════════════════════════════════
  TERMINATOR PROTOCOL — RECOVERY REPORT
═══════════════════════════════════════════════════
  Total at-risk :    ₹12,45,300.00
  Recovered     :     ₹8,91,200.00  (71.6%)
  In-flight     :     ₹1,72,000.00
  Lost          :     ₹1,82,100.00
═══════════════════════════════════════════════════
```

"71.6% recovery rate across the batch. That is measured money recovered."

---

## [3:30 – 4:15] The Dashboard

*[Screen: dashboard/index.html in browser]*

**Narration:**
"The dashboard is a single deployable HTML file — no server, no build step, works on GitHub Pages.

Drop in your `audit_export.csv` and it renders live KPIs, a breakdown donut by action type, a bar chart of recovery volume, and a scrollable audit log with full AI reasoning visible per row.

Every decision the model made is traceable. Every rupee is accounted for."

---

## [4:15 – 4:50] What We Got Wrong — Honesty

*[Screen: POSTMORTEM.md]*

**Narration:**
"We shipped bugs. Here's the honest accounting.

The biggest one: a silent data loss bug in the test seeder. We dropped the explicit `conn.commit()` during a refactor. The seeder printed success, the database was empty, the executor had nothing to process. We caught it in review by querying the DB directly — not by trusting the print statement.

The second: `queue.py` shadowed Python's stdlib `queue` module, which broke the entire Torch import chain. Renaming it to `message_queue.py` fixed it in two seconds, but it cost us hours of debugging.

The third: network failures were burning escalation tiers. A connectivity blip would mark a transaction `hard_failed` in four attempts. We fixed it with an `is_fallback` flag that freezes the tier on pure error paths.

These are in `POSTMORTEM.md` with full root-cause analysis."

---

## [4:50 – 5:00] Close

*[Screen: recovery report terminal output]*

**Narration:**
"The Terminator Protocol detects revenue at risk. Diagnoses the failure. Picks the right intervention. Executes it. Measures what came back.

That's the bar. We hit it."

*[Fade to: Razorpay Buildathon 2026 title card]*
