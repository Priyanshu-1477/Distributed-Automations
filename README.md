# Distributed Automation Platform

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Celery](https://img.shields.io/badge/Celery-5.4+-37814A.svg)](https://docs.celeryq.dev/)
[![Redis](https://img.shields.io/badge/Redis-7.0+-DC382D.svg)](https://redis.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-336791.svg)](https://www.postgresql.org/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

A distributed task execution platform featuring a **FastAPI** orchestrator, **Celery** workers, **Redis** operational message brokering, and **PostgreSQL** authoritative state persistence.

---

## Architecture Overview

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

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Priyanshu-1477/Distributed-Automations.git
cd Distributed-Automations
```

### 2. Environment Setup

Create and activate a Python virtual environment (Python 3.12+ recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the package in editable mode along with development dependencies:

```bash
pip install -e ".[dev]"
```

Initialize your local environment variables:

```bash
cp .env.example .env
```

### 3. Start Local Infrastructure

Launch the PostgreSQL 16 and Redis 7 services using Docker Compose:

```bash
docker compose up -d postgres redis
```

Verify that the containers are healthy:

```bash
docker compose ps
```

### 4. Apply Database Migrations

Run Alembic migrations to create tables, indexes, and constraints:

```bash
alembic upgrade head
```

To inspect the raw SQL DDL without applying it:

```bash
alembic upgrade base:head --sql
```

### 5. Run the Application

Start the FastAPI orchestrator service locally:

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Verify service liveness and readiness:

```bash
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
```

Interactive OpenAPI documentation is available at:
`http://localhost:8000/docs`

---

## Development & Testing

### Run Automated Tests

Execute the unit and integration test suite:

```bash
pytest -v
```

### Linting & Formatting

Check code quality and formatting with Ruff:

```bash
ruff check .
ruff format --check .
```

To automatically apply fixes and format code:

```bash
ruff check --fix .
ruff format .
```
