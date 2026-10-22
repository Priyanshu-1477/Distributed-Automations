# Distributed Automation Platform: Architecture, Implementation & Execution Dry Run

> **Document Version:** 1.0.0 (Post-Milestone 1)  
> **Source Baseline:** `01_distributed_automation_platform.tex`  
> **Status:** Milestone 0 (Planning) & Milestone 1 (Foundation) Complete & Verified  

---

## 1. System Architecture & High-Level Design

The **Distributed Automation Platform** is an enterprise-grade distributed task execution engine that decouples HTTP client interactions from asynchronous, compute-heavy, or failure-prone background workloads.

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

### Core Design Philosophy
1. **Decoupled Orchestration vs. Execution**: The API/orchestrator handles validation, state persistence, and worker health tracking. Workers perform the actual business logic.
2. **PostgreSQL as Single Source of Truth**: Redis is an ephemeral message transport broker; PostgreSQL stores durable task states, per-attempt execution history, and worker registration records.
3. **Dispatch Abstraction**: The orchestrator talks only to the `TaskDispatcher` protocol. Option A implements queue dispatch via Celery. Option B (custom capability/load-aware scheduling) can be swapped in without modifying domain models or route handlers.

---

## 2. Inventory of Implemented Files & Responsibilities

| File Path | Component | Detailed Responsibility |
| :--- | :--- | :--- |
| [`pyproject.toml`](file:///home/priyanshu_grd/Distributed%20Automations/pyproject.toml) | Build & Config | Declares project metadata, pinned dependencies (FastAPI, Celery 5.x, Redis, SQLAlchemy 2, Alembic, Pydantic v2, Ruff, Pytest), and tool configurations. |
| [`.env.example`](file:///home/priyanshu_grd/Distributed%20Automations/.env.example) | Environment | Template for all configuration variables with production-ready defaults (no credentials committed). |
| [`.gitignore`](file:///home/priyanshu_grd/Distributed%20Automations/.gitignore) | Version Control | Prevents virtual environments, bytecode, temporary test artifacts, and secret files from being committed. |
| [`src/core/config.py`](file:///home/priyanshu_grd/Distributed%20Automations/src/core/config.py) | Foundation | Pydantic Settings class parsing environment variables. Validates timing invariants (`visibility_timeout > task_time_limit`). |
| [`src/core/logging.py`](file:///home/priyanshu_grd/Distributed%20Automations/src/core/logging.py) | Foundation | Structured logging setup with custom timestamps, log levels, and third-party logger filtering. |
| [`src/core/exceptions.py`](file:///home/priyanshu_grd/Distributed%20Automations/src/core/exceptions.py) | Domain | Clean hierarchy of domain exceptions: `EntityNotFoundError`, `InvalidStateTransitionError`, `OptimisticLockError`, `DispatchError`. |
| [`src/core/database.py`](file:///home/priyanshu_grd/Distributed%20Automations/src/core/database.py) | Persistence | Dual-engine setup: Asynchronous engine/session for FastAPI; Synchronous engine/session for Celery workers & Alembic; DB health probe. |
| [`src/core/redis.py`](file:///home/priyanshu_grd/Distributed%20Automations/src/core/redis.py) | Broker / Cache | Asynchronous Redis connection management and ping-based health check. |
| [`src/models/base.py`](file:///home/priyanshu_grd/Distributed%20Automations/src/models/base.py) | Persistence | `Base(DeclarativeBase)`, `TimestampMixin` (automatic UTC tracking), and `VersionMixin` (optimistic locking counter). |
| [`src/models/task.py`](file:///home/priyanshu_grd/Distributed%20Automations/src/models/task.py) | Persistence | `TaskRecord` (authoritative task model with version, status, payloads) and `TaskExecutionAttempt` (immutable per-retry attempt audit log with unique constraint). |
| [`src/models/worker.py`](file:///home/priyanshu_grd/Distributed%20Automations/src/models/worker.py) | Persistence | `WorkerRecord` storing application-level worker registration, capabilities list, concurrency, and last heartbeat timestamp. |
| [`alembic/env.py`](file:///home/priyanshu_grd/Distributed%20Automations/alembic/env.py) | Migrations | Injects Pydantic database settings into Alembic context and binds `Base.metadata` for autogenerate support. |
| [`alembic/versions/0001_initial_schema.py`](file:///home/priyanshu_grd/Distributed%20Automations/alembic/versions/0001_initial_schema.py) | Migrations | DDL migration script creating tables `tasks`, `task_execution_attempts`, `workers`, foreign keys, and indexes. |
| [`src/api/v1/health.py`](file:///home/priyanshu_grd/Distributed%20Automations/src/api/v1/health.py) | Ingress API | Liveness probe (`/health/live`) and readiness probe (`/health/ready`) verifying PostgreSQL and Redis health. |
| [`src/api/router.py`](file:///home/priyanshu_grd/Distributed%20Automations/src/api/router.py) | Ingress API | Aggregator router for API version 1. |
| [`src/main.py`](file:///home/priyanshu_grd/Distributed%20Automations/src/main.py) | Application | FastAPI application factory, lifespan startup/shutdown management, and domain exception handlers mapping to HTTP 404, 409, and 503. |
| [`docker/Dockerfile.api`](file:///home/priyanshu_grd/Distributed%20Automations/docker/Dockerfile.api) | Deployment | Multi-stage, Python 3.12-slim container image for the FastAPI orchestrator service. |
| [`docker/Dockerfile.worker`](file:///home/priyanshu_grd/Distributed%20Automations/docker/Dockerfile.worker) | Deployment | Container image for running independent Celery worker processes. |
| [`docker-compose.yml`](file:///home/priyanshu_grd/Distributed%20Automations/docker-compose.yml) | Local Stack | Docker Compose orchestrating PostgreSQL 16 (with persistent volume), Redis 7, and FastAPI with health checks. |
| [`tests/conftest.py`](file:///home/priyanshu_grd/Distributed%20Automations/tests/conftest.py) | Testing | Shared Pytest fixtures: async in-memory SQLite engine, isolated sessions, and HTTPX AsyncClient. |
| [`tests/unit/test_config.py`](file:///home/priyanshu_grd/Distributed%20Automations/tests/unit/test_config.py) | Testing | Unit tests verifying configuration validation, default values, and timing constraints. |
| [`tests/unit/test_exceptions.py`](file:///home/priyanshu_grd/Distributed%20Automations/tests/unit/test_exceptions.py) | Testing | Unit tests verifying domain exception messages and structured error details. |
| [`tests/unit/test_models.py`](file:///home/priyanshu_grd/Distributed%20Automations/tests/unit/test_models.py) | Testing | Unit tests verifying model persistence, default attributes, foreign keys, and unique attempt constraints. |
| [`tests/integration/test_health_probes.py`](file:///home/priyanshu_grd/Distributed%20Automations/tests/integration/test_health_probes.py) | Testing | Integration tests verifying `/health/live` and `/health/ready` under healthy and degraded dependency states. |

---

## 3. End-to-End Execution Dry Run: How Data Travels

To understand how the entire system functions, here is a complete, step-by-step dry run of a task lifecycle from HTTP request to background completion and audit persistence.

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
   |                        |                                                   (prime factorization)|
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

### Step-by-Step Breakdown

#### 1. Ingress & Validation (FastAPI)
- **Action**: An external client issues `POST /api/v1/tasks` with JSON payload `{"task_type": "compute.prime_factorization", "payload": {"n": 104729}}`.
- **Validation**: Pydantic schema parses and validates the payload. If invalid, FastAPI returns HTTP 422 immediately without touching downstream stores.

#### 2. Durable Persistence (PostgreSQL First)
- **Action**: The orchestrator creates a `TaskRecord`:
  - `id = uuid4()`
  - `status = TaskStatus.QUEUED`
  - `version = 1`
  - `payload = {"n": 104729}`
  - `retry_count = 0`
- **Guaranteed Consistency**: The record is committed to PostgreSQL **before** publishing to Redis. This prevents "orphan execution" where a task runs on a worker without any persistent trace in the database.

#### 3. Dispatch via Abstraction (`TaskDispatcher`)
- **Action**: The domain service passes the persistent record to `TaskDispatcher.dispatch(task)`.
- **Decoupling**: The orchestrator does not invoke Celery directly. In Option A, `CeleryQueueDispatcher` resolves queue routing based on `task_type` and calls `celery_app.send_task(...)`.
- **Ambiguous Publish Handling**:
  - If Redis is healthy: Message is published, and the API returns HTTP 202 Accepted.
  - If Redis times out or drops the connection: The orchestrator catches the exception, updates the record in PostgreSQL to `DISPATCH_FAILED`, and returns HTTP 503.
  - **Reconciliation**: If Redis actually accepted the message before timing out, the message will still reach a worker. When the worker claims the task, it sees `DISPATCH_FAILED`, triggers its reconciliation handler, transitions the task to `RUNNING`, and proceeds safely.

#### 4. Worker Pickup & Concurrency-Safe Claim (Phase 1)
- **Action**: An idle Celery worker consumes the message from Redis.
- **Claim Transaction**: Before running any user code, the worker opens an isolated database transaction:
  1. Executes optimistic update:
     ```sql
     UPDATE tasks
     SET status = 'RUNNING', version = version + 1, updated_at = NOW()
     WHERE id = :task_id AND status IN ('QUEUED', 'RETRY_SCHEDULED', 'DISPATCH_FAILED') AND version = :current_version;
     ```
  2. If 0 rows updated: Another process or cancel request already modified the task. The worker aborts to prevent a race condition.
  3. Inserts an immutable row into `task_execution_attempts`:
     - `task_id = task.id`
     - `attempt_number = task.retry_count + 1` (e.g. 1)
     - `worker_id = "worker-prod-1"`
     - `status = AttemptStatus.RUNNING`
     - `started_at = NOW()`
  4. Commits Claim Transaction (releasing DB locks immediately).

#### 5. Pure Task Execution (Phase 2)
- **Action**: The worker runs the decoupled Python task function (`compute.py`).
- **No Database Locks Held**: Business logic runs entirely outside the database transaction, preventing database connection exhaustion during long compute cycles.

#### 6. Outcome Persistence (Phase 3)
- **Action**: The user function returns successfully with result `{"factors": [104729]}`.
- **Outcome Transaction**: The worker opens a second database transaction:
  1. Updates `task_execution_attempts`:
     - `status = AttemptStatus.SUCCEEDED`
     - `completed_at = NOW()`
     - `duration_seconds = 0.042`
  2. Updates `tasks`:
     - `status = TaskStatus.SUCCEEDED`
     - `result = {"factors": [104729]}`
     - `version = version + 1`
  3. Commits Outcome Transaction.

#### 7. Late Message Acknowledgement (Phase 4)
- **Action**: Because `task_acks_late = True`, Celery acknowledges the message to Redis **only after Phase 3 commits**.
- **Crash Recovery Guard**:
  - If the worker crashes during Phase 2 (Execution): The message was never acknowledged. Celery supervisor (`task_reject_on_worker_lost=True`) rejects the message back to Redis. Another worker picks up the job, sees attempt #1 was interrupted, creates attempt #2, and executes.
  - If the worker crashes after Phase 3 but before Phase 4: Redis redelivers the message. The second worker inspects the database in Phase 1, sees `status == SUCCEEDED`, immediately ACKs Redis, and skips execution (**Idempotency Guard**).

#### 8. Worker Liveness & The Non-Reassignment Invariant
- **Worker Heartbeat**: Every 10 seconds, a background daemon inside each worker container invokes `POST /api/v1/workers/{worker_id}/heartbeat`.
- **Stale Detection**: The orchestrator sweeper checks: if `now - last_heartbeat_at > 30s`, worker status is marked `STALE`. If `> 90s`, marked `OFFLINE`.
- **Critical Invariant**: A stale heartbeat **never triggers task reassignment**. Task reassignment is governed strictly by Redis visibility timeouts and Celery broker acknowledgements, preventing split-brain dual execution.

---

## 4. Verification Evidence & Quality Assurance

1. **Automated Unit & Integration Tests**:
   - `pytest -v` executes 13 automated tests covering settings validation, domain exceptions, declarative model constraints, unique attempt constraints, and health probes. All passed in 0.60 seconds.
2. **Static Analysis & Formatting**:
   - `ruff check .` and `ruff format --check .` verify 100% compliance with modern Python 3.12 syntax and formatting standards.
3. **Alembic Database Migration Verification**:
   - Generated static transactional DDL via `alembic upgrade base:head --sql`, confirming correct PostgreSQL schema creation.

