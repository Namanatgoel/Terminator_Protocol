# Terminator Protocol - 5-Minute Video Script
**Razorpay Buildathon 2026 | Track 03: AI Revenue Recovery**

> **Recording note:** Screen-record `dashboard/index.html` in Chrome. Each section matches the navigation flow on the page. The dashboard is completely static and clean, aligned with Razorpay design standards.

---

## [0:00 – 0:30] Hook - The Problem

*[Screen: `dashboard/index.html` hero section - Overview]*

**Narration:**
"Every second, payments fail. Cards decline. Checkouts get abandoned mid-flow. Subscriptions lapse.
Most systems log this. Some retry blindly. None of them think.

The question we asked was: what if an AI agent could close the entire loop - detect the failure, diagnose the reason, pick the exact right intervention, and execute it - automatically?"

*[Scroll down slightly to the summary stats cards showing 50 failures, 71.6% recovery rate, and ₹8,91,200 recovered.]*

"This is the Terminator Protocol."

---

## [0:30 – 1:30] The Architecture - What It Is

*[Scroll to or click 'Architecture' in the nav]*

**Narration:**
"The system is built on four core Python modules, each with a strict single responsibility.

**db.py**: The database layer. Every failed transaction enters as `pending`. The executor locks batches atomically using SQLite's `BEGIN EXCLUSIVE`, ensuring zero double-execution.

**llm_engine.py**: The brain. We run Qwen-2.5-7B locally, GPU-accelerated. The model outputs a routing decision using Pydantic `Literal` constraints. If the LLM hallucinates an invalid action, Pydantic rejects it instantly.

**executor.py**: The orchestration loop. It fetches batches, calls the AI router, executes the action, and logs the outcome as structured JSON.

**message_queue.py**: Backs the delay queue. We use an outbox pattern where escalation events are enqueued *before* the database commit to prevent silent data loss on crashes."

---

## [1:30 – 2:30] The Four Tiers - AI Judgment

*[Scroll to or click 'Escalation' in the nav]*

**Narration:**
"The agent escalates through four tiers. This is where AI judgment matters most.

**Tier 1 - Silent Retry.** The LLM detects a transient failure: insufficient funds, a network blip. It schedules a quiet retry. No customer contact. No friction.

**Tier 2 - WhatsApp Ping.** Repeat failure signals an addressable user. A Razorpay UPI deep-link fires via WhatsApp. One tap to complete payment.

**Tier 3 - Voice Negotiation.** The LLM reads accumulated context. If price sensitivity was flagged in prior interactions - the user hesitated, mentioned EMI - the model authorises a 10% discount and triggers a Retell AI voice call. The AI negotiates on Razorpay's behalf, in real time.

**Tier 4 - Terminal Alert.** Last chance. An urgency-framed email and SMS hit simultaneously. After this, the transaction is marked `hard_failed` and counted as lost revenue."

---

## [2:30 – 3:30] The Dashboard & Audit Log

*[Scroll to or click 'Dashboard' in the nav]*

**Narration:**
"The dashboard is a single HTML file - no server, no build step, works on GitHub Pages. Drop in your `audit_export.csv` and it renders live KPIs: total at-risk, recovered, in-flight, and lost."

*[Hover over the Action Breakdown donut chart and Volume bar chart.]*

"The charts break down recovery volume by action type. Silent retry catches the most volume, but voice negotiation recovers the highest-value transactions."

*[Scroll down to the Audit Log table in the Dashboard section.]*

"Every decision the model made is traceable. Scroll the audit log and you see the exact AI reasoning produced for that decision, and whether an offer was authorised. Every rupee has an accountable rationale."

---

## [3:30 – 4:15] Execution Feed & Postmortem

*[Scroll to or click 'Action Feed' in the nav]*

**Narration:**
"Under the hood, the orchestrator emits real-time structured event logs."

*[Point to the warning log line: `Fallback Triggered`]*

"We designed for failure. Notice this warning line - `Fallback Triggered`. If the network partitions or Kafka goes down, the system does not advance the escalation tier. It executes a safe fallback. No revenue is incorrectly marked lost due to an infrastructure blip."

*[Briefly mention the postmortem]*

"We shipped bugs along the way - a silent data loss bug during refactoring, and a standard library shadowing issue that broke Torch. We documented all of this in our Postmortem. Honesty in engineering."

---

## [4:15 – 5:00] Close

*[Scroll back to the top hero section]*

**Narration:**
"The Terminator Protocol detects revenue at risk. Diagnoses the failure. Picks the right intervention. Executes it. Measures what came back.

That's the bar. We hit it."

*[Fade to black - 'Razorpay Buildathon 2026' title card.]*
