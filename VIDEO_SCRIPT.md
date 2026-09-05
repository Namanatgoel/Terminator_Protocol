# Terminator Protocol - 5-Minute Video Script
**Razorpay Buildathon 2026 | Track 03: AI Revenue Recovery**

> **Recording note:** Screen-record `dashboard/index.html` in Chrome. Each section maps to a nav link at the top. All animations are built-in.

---

## [0:00 – 0:30] Hook - The Problem

*[Screen: `dashboard/index.html` hero section - the live failure ticker in the bottom bar is ticking up in real time, counting failures and ₹ at risk.]*

**Narration:**
"Every second, payments fail. Cards decline. Checkouts get abandoned mid-flow. Subscriptions lapse.
Most systems log this. Some retry blindly. None of them think.

The question we asked was: what if an AI agent could close the entire loop - detect the failure, diagnose the reason, pick the exact right intervention, and execute it - automatically?"

*[Scroll down slightly - the three hero counter cards animate in: 50 failures, 71.6% recovery rate, ₹8,91,200 recovered.]*

"This is the Terminator Protocol."

---

## [0:30 – 1:30] The Architecture - What It Is

*[Click 'Architecture' in the nav - the module cards slide in from the left one by one, the flow diagram fades in from top to bottom.]*

**Narration:**
"Seven Python modules, each with a single responsibility.

**The Database layer.** Every failed transaction enters as `pending`. The executor locks a batch atomically - `BEGIN EXCLUSIVE` simulating Postgres's `FOR UPDATE SKIP LOCKED` - and sets them to `processing`. No double execution.

**The LLM Router.** This is the brain. We run Qwen-2.5-7B locally via vLLM on the RTX 5050 - GPU-accelerated, deterministic at temperature zero. The model outputs an `ActionDecision` - a Pydantic model with a `Literal` type constraint. If the LLM hallucinates an action string, Pydantic rejects it at parse time and the retry loop fires.

**The Executor.** Fetches batches, calls the router, executes the action, logs the audit entry - amount, AI reasoning, offer authorised. Structured JSON to stdout, Datadog-ready.

**The Message Queue.** Redpanda backs the delay queue. Escalation is enqueued *before* the DB commit - an outbox pattern that prevents silent data loss on crash.

**The Recovery Report.** One command: ₹ recovered vs ₹ at-risk across the full batch."

---

## [1:30 – 2:30] The Four Tiers - AI Judgment

*[Click 'Escalation' in the nav - the four tier cards animate in sequentially, colour-coded blue → green → purple → red.]*

**Narration:**
"The agent escalates through four tiers. This is where AI judgment matters most.

**Tier 1 - Silent Retry.** The LLM detects a transient failure: insufficient funds, a network blip. It schedules a quiet Redpanda retry. No customer contact. No friction.

**Tier 2 - WhatsApp Ping.** Repeat failure signals an addressable user. A Razorpay UPI deep-link fires via WhatsApp. One tap to complete payment.

**Tier 3 - Voice Negotiation.** The LLM reads accumulated context. If price sensitivity was flagged in prior interactions - the user hesitated, mentioned EMI - the model authorises a 10% discount and triggers a Retell AI voice call. The AI negotiates on Razorpay's behalf, in real time.

**Tier 4 - Terminal FOMO.** Last chance. An urgency-framed email and SMS hit simultaneously. After this, the transaction is marked `hard_failed` and counted as lost in the recovery report."

---

## [2:30 – 3:30] Live Demo - Terminal

*[Click 'Action Feed' in the nav - the feed section. Execution feed events load in with structured details.]*

**Narration:**
"Let me show you this running.

`python test.py` seeds 50 synthetic failed transactions into the database."

*[Show terminal output: `INFO:test:Seeded 50 synthetic failed transactions.`]*

"Now the executor. Every event emits a JSON log line - txn_id, action taken, next tier, amount at risk, and whether this was a real LLM decision or a safe fallback."

*[Point at the log line with `is_fallback: true` - triggered when Kafka was unreachable.]*

"Notice this line - `is_fallback: true`. The network was partitioned. The system did not advance the escalation tier. It did not burn recovery budget. The transaction stays at Tier 1 and will be picked up on the next batch. Zero revenue incorrectly marked lost."

*[Switch to terminal, run:]*
```
python report.py
```

```
════════════════════════════════════════════════════
  TERMINATOR PROTOCOL - RECOVERY REPORT
════════════════════════════════════════════════════
  Total at-risk :  ₹12,45,300.00
  Recovered      :   ₹8,91,200.00  (71.6%)
  In-flight      :   ₹1,72,000.00
  Lost           :   ₹1,82,100.00
════════════════════════════════════════════════════
```

"71.6% recovery rate. That is measured money recovered."

---

## [3:30 – 4:15] The Dashboard

*[Click 'Dashboard' in the nav - the four KPI cards appear, then the donut chart and bar chart animate in.]*

**Narration:**
"The dashboard is a single HTML file - no server, no build step, works on GitHub Pages.

Drop in your `audit_export.csv` and it renders four live KPIs: total at-risk, recovered, in-flight, and hard-failed."

*[Hover over the donut chart - segments highlight. Point at the bar chart.]*

"The bar chart shows recovery volume by action type - so you can see exactly how much revenue each channel recovered. Silent retry caught the most volume. Voice negotiation recovered the highest-value transactions.

Scroll the audit log. Every row has the action, the amount, whether a discount was authorised, and the exact AI reasoning the model produced for that decision. Every rupee has an accountable rationale."

---

## [4:15 – 4:50] What We Got Wrong - Honesty

*[Open `POSTMORTEM.md` in a text editor or show `dashboard/index.html` Action Feed section with the fallback event visible.]*

**Narration:**
"We shipped bugs. Here's the honest accounting.

The biggest: a silent data loss bug. We dropped the `conn.commit()` call during a refactor. The seeder printed 'success'. The database was empty. We caught it by querying the DB directly - not by trusting the log message. Fix was one line.

The second: `queue.py` shadowed Python's stdlib `queue` module. It broke the entire Torch import chain - CUDA detection failed silently. Renaming to `message_queue.py` fixed it.

The third: network failures were burning escalation tiers. A connectivity blip would mark a transaction `hard_failed` in four retries - incorrectly. We added an `is_fallback: bool` field to `ActionDecision`. The executor now skips tier advancement on pure error paths. You saw this in the log replay - the line with `is_fallback: true`."

---

## [4:50 – 5:00] Close

*[Return to hero section - ticker still counting, recovery counters visible.]*

**Narration:**
"The Terminator Protocol detects revenue at risk. Diagnoses the failure. Picks the right intervention. Executes it. Measures what came back.

That's the bar. We hit it."

*[Fade to black - 'Razorpay Buildathon 2026' title card.]*

