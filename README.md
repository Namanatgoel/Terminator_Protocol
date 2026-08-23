# The "Terminator" Protocol: AI Revenue Recovery 🦾

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![Razorpay Buildathon](https://img.shields.io/badge/Razorpay-Buildathon_2026-blueviolet.svg)](https://razorpay.com/buildathon/)

*Track 03: AI Revenue Recovery* 
*Find revenue that’s slipping away and win it back.*

## 📌 The Concept
The **Terminator Protocol** is an ultra-aggressive, multi-agent revenue recovery engine designed to capture slipping revenue through a relentless omnichannel saturation loop. 

Instead of simple static retries, our AI Diagnostic Router (powered by Qwen-2.5-7B) intelligently triages failed transactions, authorizes micro-discounts (EMIs) mid-flight, and orchestrates actions across WhatsApp, SMS, and Retell AI Voice agents until the capital is recovered or a hard terminal failure is reached. 

No-shot misses are unacceptable.

## 🏗️ Architecture

The system is built on a highly modular, lean architecture utilizing only 5 core python modules:

1. **`db.py`**: State machine, strict locking, and immutable audit logs.
2. **`llm_engine.py`**: The GPU-accelerated routing brain. Uses prompt-engineering to dynamically authorize offers or fallback to standard retries based on prior agent context.
3. **`queue.py`**: Redpanda/Kafka delay queue wrappers.
4. **`executor.py`**: The relentless state-machine loop orchestrator.
5. **`test.py`**: Checkpoint validation for synthetic data and chaos testing.

> **Note on Local Execution:** 
> For the purpose of immediate hackathon evaluation without requiring heavy OS-level services, the repository uses **SQLite** (acting as a local ceiling for development) instead of the originally planned PostgreSQL. Atomic locking is handled natively by SQLite's `BEGIN EXCLUSIVE` transactions to simulate `SKIP LOCKED` behavior.

## 🚀 Getting Started

### 1. Environment Setup
We use `conda` to ensure reproducible execution environments.

```bash
conda env create -f environment.yml -n RzpyBuild
conda activate RzpyBuild
```

### 2. Generate Synthetic Data
Populate the database with 50 synthetic degraded transactions (insufficient funds, abandoned checkouts, card declines).

```bash
python test.py
```

### 3. Unleash the Terminator
Run the main execution loop. It will simulate atomic fetching, passing the transaction context to the local LLM, escalating tiers (Silent Retry -> WhatsApp Ping -> AI Voice Negotiation -> FOMO Email), and safely storing context for cross-agent memory.

```bash
python executor.py
```

### 4. Review the Audit Log
To extract the exact, immutable financial log of actions taken, outcomes, and LLM rationale:

```bash
python -c "from test import export_audit_log; export_audit_log()"
```
This will generate `audit_export.csv` containing the complete trace.

## 🛡️ Security & Scalability
- **No API Leaks:** All API endpoints inside the local scripts are heavily stubbed or use mock local `localhost:8000` identifiers to prevent data/key leaks during submission.
- **Resilient Fallbacks:** If the vLLM engine drops connection (Chaos Test Checkpoint 2), the system catches the `openai.APIConnectionError` and routes gracefully to a conservative silent retry loop, ensuring zero lost capital even under heavy network partition.
