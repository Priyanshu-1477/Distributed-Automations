# Distributed Automation Platform

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Celery](https://img.shields.io/badge/Celery-5.4+-37814A.svg)](https://docs.celeryq.dev/)
[![Redis](https://img.shields.io/badge/Redis-7.0+-DC382D.svg)](https://redis.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-336791.svg)](https://www.postgresql.org/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

A distributed task execution platform featuring a **FastAPI** orchestrator, **Celery** workers, **Redis** operational message brokering, and **PostgreSQL** authoritative state persistence.

Rebuilt and modernized from the original architectural study baseline in `01_distributed_automation_platform.tex`.

---

## Documentation & Architecture Manual

- 📄 **[Detailed Architecture & Execution Dry Run (Markdown)](docs/ARCHITECTURE_AND_EXECUTION_FLOW.md)**: File-by-file breakdown, sequence diagrams, failure recovery mechanics, and data flow walkthrough.
- 📕 **[Technical Architecture & Implementation Manual (PDF)](docs/distributed_automation_architecture_manual.pdf)**: Complete 4-page printable architectural study guide.
- 📋 **[Milestone 0: Architecture Specification & Roadmap](file:///home/priyanshu_grd/.gemini/antigravity/brain/9b42113f-8af6-4620-bf36-d5521dd61e71/milestone_0_architecture_and_plan.md)**: Foundational specification with requirements matrix, dual-write strategy, and state machine transition rules.

---

## System Architecture

```
                          +-------------------------+
                          |   HTTP Client / Caller  |
                          +------------+------------+
                                       |
                                       | HTTP POST /tasks
                                       v
                    +------------------------------------+
                    |        FastAPI Orchestrator        |
                    |  - Ingress API & Validation        |
                    |  - Task & Worker Orchestrator      |
                    |  - TaskDispatcher Abstraction      |
                    +---------+----------------+---------+
                              |                |
             1. ACID Commit   |                | 2. Queue Message
             (Status: QUEUED) |                | (Option A: Celery)
                              v                v
                   +------------------+  +--------------------+
                   |  PostgreSQL 16   |  |   Redis 7 Broker   |
                   | Authoritative DB |  | Message Queues     |
                   +--------+---------+  +---------+----------+
                            ^                      |
                            | 3. Claim, Update &   | 4. Pull Task
                            |    Record Attempts   |
                            |                      v
                    +-------+-----------------------------+
                    |          Celery Worker Tier         |
                    |  - Worker 1 (Prefetch=1, Acks Late) |
                    |  - Worker 2 (Prefetch=1, Acks Late) |
                    |  - Decoupled Task Handlers          |
                    |  - Liveness Heartbeat Daemon        |
                    +-------------------------------------+
```

---

## Core Guarantees & Invariants

1. **PostgreSQL-First Dispatch**: Task records are committed with status `QUEUED` in PostgreSQL before publishing to Redis, preventing orphan executions.
2. **Ambiguous Dispatch Reconciliation**: If Redis publish times out ambiguously, the record is set to `DISPATCH_FAILED`. If the message was enqueued, the claiming worker detects this race and reconciles the task to `RUNNING`.
3. **Late Acknowledgements & Crash Recovery**: Celery workers run with `task_acks_late=True` and `task_reject_on_worker_lost=True`. If a worker dies mid-task (`kill -9`), Redis redelivers the message to an active worker.
4. **Idempotency Guard**: Workers check PostgreSQL in Phase 1 before running user code. If the task is already `SUCCEEDED`, the worker immediately ACKs the message to Redis and skips execution.
5. **Optimistic Locking**: Every `TaskRecord` contains a `version: int` column. Transitions execute conditional updates (`WHERE status = :current AND version = :v`), rejecting concurrent or out-of-order writes.
6. **The Non-Reassignment Invariant**: A worker heartbeat timeout (marked `STALE` after 30s) **never triggers automatic task reassignment**. Reassignment is governed exclusively by broker acknowledgements and visibility timeouts.

---

## Quickstart

### 1. Setup Local Environment

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies in editable mode with dev tools
pip install -e ".[dev]"
```

### 2. Run Tests & Linter

```bash
# Run automated test suite
pytest -v

# Run linter and formatter checks
ruff check .
ruff format --check .
```

### 3. Generate Architecture PDF Manual

```bash
python scripts/generate_architecture_pdf.py docs/distributed_automation_architecture_manual.pdf
```

### 4. Run Local Infrastructure via Docker Compose

```bash
docker compose up -d postgres redis
```

