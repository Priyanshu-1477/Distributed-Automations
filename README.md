# Distributed Automation Platform

A distributed, fault-tolerant task execution platform built with **FastAPI**, **Celery**, **Redis**, and **PostgreSQL**.

The platform is designed to decouple synchronous HTTP client interactions from compute-heavy, delayed, or failure-prone asynchronous background tasks, providing persistent state tracking, bounded retry policies, and crash resilience.

---

## 1. System Architecture

The platform separates **Ingress & Coordination** from **Operational Messaging** and **Asynchronous Execution**, with PostgreSQL serving as the single source of truth for durable application state.

```
                          +-------------------------+
                          |   HTTP Client / Caller  |
                          +------------+------------+
                                       |
                                       | HTTP Requests (/api/v1/tasks)
                                       v
                    +------------------------------------+
                    |        FastAPI Orchestrator        |
                    |  - Ingress API & Validation        |
                    |  - Domain State Machine            |
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
                            |    Record Attempts   |    (Prefetch = 1)
                            |                      v
                    +-------+-----------------------------+
                    |          Celery Worker Tier         |
                    |  - Worker 1 (Acks Late, Prefetch=1) |
                    |  - Worker 2 (Acks Late, Prefetch=1) |
                    |  - Decoupled Task Logic Handlers    |
                    |  - Worker Liveness Heartbeat Daemon |
                    +-------------------------------------+
```

### Component Breakdown

* **FastAPI Orchestrator**: The public API boundary. Receives client submissions, enforces Pydantic schema validation, manages the task state machine, and monitors application-level worker health.
* **TaskDispatcher Abstraction**: A strict interface isolating the orchestrator from queue internals. In the current implementation (Option A), `CeleryQueueDispatcher` routes jobs to Redis queues. The abstraction guarantees future custom schedulers (Option B) can be plugged in without modifying route handlers, database models, or task business logic.
* **Redis 7 (Operational Broker)**: Ephemeral, in-memory transport layer carrying execution payloads between the producer and the worker processes.
* **Celery Worker Tier**: Independent worker processes consuming tasks from Redis queues. Workers apply bounded retry policies, record execution attempt metrics, and run decoupled business logic.
* **PostgreSQL 16 (Authoritative Store)**: The durable single source of truth. Stores task definitions, JSON payloads and outputs, retry counts, execution attempt histories (`task_execution_attempts`), and worker registration records.

---

## 2. End-to-End Execution Dry Run

Here is the exact lifecycle of a task from initial client submission to final execution, outcome persistence, and acknowledgement:

```
[Client]                [FastAPI]               [PostgreSQL]             [Redis]                 [Worker 1]
   |                        |                        |                      |                        |
   |--- 1. POST /tasks ---->|                        |                      |                        |
   |                        |--- 2. INSERT Task ---->|                      |                        |
   |                        |    (QUEUED, v=1)       |                      |                        |
   |                        |<-- 3. Commit OK -------|                      |                        |
   |                        |                                               |                        |
   |                        |--- 4. TaskDispatcher.dispatch() ------------->|                        |
   |                        |    (Publish celery task message)              |                        |
   |                        |<-- 5. Broker Publish ACK ---------------------|                        |
   |<-- 6. 202 Accepted ----|                                               |                        |
   |    (task_id, QUEUED)   |                                               |                        |
   |                        |                                               |--- 7. Deliver Task --->|
   |                        |                                               |                        |
   |                        |                        |                      |   [Phase 1: Claim Tx]  |
   |                        |                        |<-- 8. Claim & UPDATE status=RUNNING, v=2 -----|
   |                        |                        |<-- 9. INSERT Attempt #1 (RUNNING) ------------|
   |                        |                        |--- 10. Commit Claim OK ---------------------->|
   |                        |                                                                        |
   |                        |                                                   [Phase 2: Execution] |
   |                        |                                                   Execute pure task    |
   |                        |                                                   (e.g., computation)  |
   |                        |                                                                        |
   |                        |                        |                      |   [Phase 3: Outcome Tx]|
   |                        |                        |<-- 11. UPDATE Attempt #1 (SUCCEEDED) ---------|
   |                        |                        |<-- 12. UPDATE Task (SUCCEEDED, result) -------|
   |                        |                        |--- 13. Commit Outcome OK -------------------->|
   |                        |                                               |                        |
   |                        |                                               |   [Phase 4: ACK]       |
   |                        |                                               |<-- 14. Celery ACK -----|
   |                        |                                               |    (Late ACK)          |
```

### Detailed Execution Steps

#### Step 1: Ingress & Schema Validation
The client sends an HTTP request (`POST /api/v1/tasks`) with a payload specifying the task type and input arguments. FastAPI validates the payload against Pydantic models. If invalid, the request is rejected immediately with HTTP 422 before reaching any database or broker.

#### Step 2: Authoritative Database Commit (Postgres First)
The orchestrator creates a `TaskRecord` in PostgreSQL with `status = 'QUEUED'`, `version = 1`, and `retry_count = 0`. The database transaction commits **before** publishing to Redis, guaranteeing that no task can execute on a worker without a persistent record existing in PostgreSQL.

#### Step 3: Message Dispatch via Abstraction
The orchestrator invokes `TaskDispatcher.dispatch(task)`. The Celery dispatcher resolves queue routing and publishes the task message to Redis.
* **Normal Path**: Message is published successfully, and the API returns HTTP 202 Accepted.
* **Ambiguous Timeout Handling**: If the publish operation to Redis times out, the database record is updated to `DISPATCH_FAILED` and the API returns HTTP 503. If Redis actually received the message before the client timeout, the claiming worker detects `DISPATCH_FAILED` during its claim transaction and reconciles it back to `RUNNING`.

#### Step 4: Worker Pickup & Claim Transaction (Phase 1)
An available Celery worker consumes the message from Redis. Before running any user code, the worker opens a short database transaction:
1. Executes an atomic conditional update:
   ```sql
   UPDATE tasks
   SET status = 'RUNNING', version = version + 1, updated_at = NOW()
   WHERE id = :task_id AND status IN ('QUEUED', 'RETRY_SCHEDULED', 'DISPATCH_FAILED') AND version = :current_version;
   ```
2. Inserts an immutable audit row into `task_execution_attempts` (`attempt_number = 1`, `worker_id = 'worker-1'`, `status = 'RUNNING'`).
3. Commits the transaction and **releases all database locks**.

#### Step 5: Pure Task Execution (Phase 2)
The worker executes the decoupled Python task business logic. Because database locks were released in Phase 1, long-running compute operations do not hold open database transactions or exhaust connection pools.

#### Step 6: Outcome Persistence (Phase 3)
When execution finishes, the worker opens a second database transaction:
1. Updates `task_execution_attempts` with `status = 'SUCCEEDED'`, `completed_at = NOW()`, and `duration_seconds`.
2. Updates `tasks` with `status = 'SUCCEEDED'`, the output `result` JSON, and increments `version = version + 1`.
3. Commits the outcome transaction.

#### Step 7: Late Message Acknowledgement (Phase 4)
Because workers are configured with `task_acks_late = True`, Celery acknowledges the message to the Redis broker **only after Step 6 commits**.

---

## 3. Distributed Guarantees & Fault-Tolerance Invariants

* **PostgreSQL-First Dispatch**: Tasks are committed to PostgreSQL before message publishing to prevent "orphan executions" where a task runs on a worker without an authoritative database record.
* **Late Acknowledgement & Worker Crash Recovery**: Celery runs with `task_acks_late = True` and `task_reject_on_worker_lost = True`. If a worker container crashes or is abruptly terminated (`kill -9`) mid-task, the unacknowledged message is rejected back to Redis and redelivered to an active worker.
* **Idempotency Guard**: Workers check the database in Phase 1 before running user code. If the task is already in a terminal state (`SUCCEEDED` or `FAILED`), the worker immediately acknowledges the message to Redis and skips execution, preventing duplicate side effects.
* **Optimistic Concurrency Control**: Every `TaskRecord` contains a `version: int` column. All state transitions execute conditional SQL updates (`WHERE status = :current AND version = :expected`), preventing stale or out-of-order updates from overwriting newer states.
* **The Non-Reassignment Invariant**: A worker heartbeat timeout (marked `STALE` after 30s) **never triggers automatic task reassignment by the orchestrator**. A missing heartbeat indicates only a telemetry disruption; the worker may still be executing. Task redelivery is governed strictly by broker visibility timeouts and acknowledgements to prevent split-brain dual execution.
* **Visibility Timeout Safety**: Redis `visibility_timeout` (3600s) is configured strictly higher than `task_time_limit` (1800s), ensuring Redis never redelivers a task while an active worker is still executing it.

---

## 4. Setup & Running Guide

### Prerequisites
* Python 3.12 or compatible version
* Docker and Docker Compose
* Git

### Step 1: Clone the Repository

```bash
git clone https://github.com/Priyanshu-1477/Distributed-Automations.git
cd Distributed-Automations
```

### Step 2: Local Python Environment

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies in editable development mode:

```bash
pip install -e ".[dev]"
```

Configure your local environment variables:

```bash
cp .env.example .env
```

### Step 3: Start Backing Services (Docker Compose)

Start PostgreSQL 16 and Redis 7 in the background:

```bash
docker compose up -d postgres redis
```

Verify that the containers are healthy:

```bash
docker compose ps
```

### Step 4: Apply Database Migrations

Apply Alembic migrations to create tables (`tasks`, `task_execution_attempts`, and `workers`), indexes, and constraints in PostgreSQL:

```bash
alembic upgrade head
```

To view the generated SQL DDL without executing it:

```bash
alembic upgrade base:head --sql
```

### Step 5: Start the FastAPI Orchestrator

Run the application locally:

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Verify service liveness and readiness:

```bash
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
```

Interactive OpenAPI documentation is available in your browser at:
`http://localhost:8000/docs`

### Step 6: Run Automated Tests

Execute the unit and integration test suite:

```bash
pytest -v
```

