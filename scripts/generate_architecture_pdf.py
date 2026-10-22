import os
import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute total page count."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#718096"))

        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(
                54,
                750,
                "Distributed Automation Platform — Technical Architecture & Implementation Manual",
            )
            self.setStrokeColor(colors.HexColor("#CBD5E0"))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)

        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#CBD5E0"))
        self.setLineWidth(0.5)
        self.line(54, 45, 558, 45)
        self.drawString(
            54,
            32,
            "Confidential — Distributed Systems Portfolio Project (FastAPI, Celery, Redis, PostgreSQL)",
        )
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 32, page_str)
        self.restoreState()


def build_pdf(filename="docs/distributed_automation_architecture_manual.pdf"):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#4A5568"),
        spaceAfter=15,
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=colors.HexColor("#1A365D"),
        spaceBefore=12,
        spaceAfter=8,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=6,
    )

    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4,
    )

    callout_style = ParagraphStyle(
        "Callout",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#2C5282"),
    )

    code_block_style = ParagraphStyle(
        "CodeBlock",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#1A202C"),
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
    )

    table_body_style = ParagraphStyle(
        "TableBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#2D3748"),
    )

    story = []

    # Title & Metadata Banner
    story.append(Paragraph("Distributed Automation Platform", title_style))
    story.append(
        Paragraph(
            "Complete Architecture Blueprint, Implementation Inventory & End-to-End Execution Walkthrough<br/>"
            "<b>Runtime:</b> Python 3.12 | FastAPI | Celery 5 | Redis 7 | PostgreSQL 16 | Docker Compose",
            subtitle_style,
        )
    )

    # Executive Overview Box
    overview_text = (
        "<b>Project Purpose:</b> Rebuilt from architectural baseline <code>01_distributed_automation_platform.tex</code>. "
        "This platform solves the problem of slow, failure-prone, and bursty task execution in modern web backends. "
        "It decouples synchronous HTTP client interactions from asynchronous, compute-heavy, and distributed background workers. "
        "PostgreSQL acts as the single source of truth for durable state and attempt history, Redis acts as the operational broker, "
        "and FastAPI acts as the ingress orchestrator."
    )
    overview_table = Table(
        [[Paragraph(overview_text, callout_style)]],
        colWidths=[504],
    )
    overview_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EBF8FF")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#BEE3F8")),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    story.append(overview_table)
    story.append(Spacer(1, 10))

    # Section 1: Architecture Topology & Component Interaction
    story.append(Paragraph("1. System Architecture & Topology", h1_style))
    story.append(
        Paragraph(
            "The architecture cleanly separates <b>Ingress & Coordination</b>, <b>Operational Messaging</b>, "
            "<b>Execution</b>, and <b>Authoritative Persistence</b>. Below is the full component layout:",
            body_style,
        )
    )

    topology_ascii = """
 +-----------------------------------------------------------------------------------+
 |                             CLIENTS & CALLERS (HTTP)                              |
 +-----------------------------------------+-----------------------------------------+
                                           | HTTP Requests (/api/v1/tasks)
                                           v
 +-----------------------------------------------------------------------------------+
 |                         FASTAPI ORCHESTRATOR SERVICE                              |
 |  - Ingress API: Validation, pagination, cancellation, health probes              |
 |  - Domain Services: Task state machine & worker registry coordination            |
 |  - TaskDispatcher Interface: Strict abstraction decoupling Celery internals       |
 +-------------------+-------------------------------------------+-------------------+
                     |                                           |
      1. Commit Task | (status: QUEUED)           2. Queue Task  | (Option A: Celery)
         Optimistic  | (version: 1)                  Via broker  |
                     v                                           v
 +---------------------------------------+   +---------------------------------------+
 |        POSTGRESQL 16 (DURABLE)        |   |         REDIS 7 (MESSAGE BROKER)      |
 |  - tasks: Authoritative state & result|   |  - Ephemeral task delivery queues     |
 |  - task_execution_attempts: History   |   |  - Celery transport broker            |
 |  - workers: Application registry      |   |  - Late ACK & visibility timeout      |
 +-------------------+-------------------+   +-------------------+-------------------+
                     ^                                           |
                     | 3. Claim Transaction (RUNNING, v=v+1)     | 4. Pull Task
                     |    Insert Attempt #1                      |    (Prefetch = 1)
                     |                                           v
 +-------------------+---------------------------------------------------------------+
 |                              CELERY WORKER TIER                                   |
 |  - Worker 1 & Worker 2: Concurrent process execution pool                        |
 |  - Decoupled Task Logic: Pure Python functions (compute, delayed, chaos retry)   |
 |  - Crash Recovery: task_acks_late=True, task_reject_on_worker_lost=True            |
 |  - Worker Liveness Agent: Periodic background HTTP heartbeats to Orchestrator     |
 +-----------------------------------------------------------------------------------+
"""
    topology_table = Table(
        [[Preformatted(topology_ascii.strip(), code_block_style)]],
        colWidths=[504],
    )
    topology_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(topology_table)
    story.append(Spacer(1, 10))

    # Section 2: Complete File-by-File Inventory
    story.append(Paragraph("2. Inventory of Implemented Files (Milestone 1)", h1_style))
    story.append(
        Paragraph(
            "Every file created in the workspace serves a strictly bounded responsibility without circular dependencies:",
            body_style,
        )
    )

    files_data = [
        [
            Paragraph("File / Module", table_header_style),
            Paragraph("Subsystem", table_header_style),
            Paragraph("Exact Architectural Function & Invariants", table_header_style),
        ],
        [
            Paragraph("<code>pyproject.toml</code>", table_body_style),
            Paragraph("Build & Meta", table_body_style),
            Paragraph(
                "Defines pinned dependencies (Python 3.12 target, FastAPI, Celery 5.x, Redis, SQLAlchemy 2, Alembic, Pydantic v2, Ruff, Pytest).",
                table_body_style,
            ),
        ],
        [
            Paragraph("<code>.env.example</code>", table_body_style),
            Paragraph("Config", table_body_style),
            Paragraph(
                "Complete template of environment settings with production-safe defaults; prevents credentials from entering git.",
                table_body_style,
            ),
        ],
        [
            Paragraph("<code>src/core/config.py</code>", table_body_style),
            Paragraph("Foundation", table_body_style),
            Paragraph(
                "Pydantic Settings class parsing environment. Enforces invariant: <code>visibility_timeout &gt; task_time_limit</code>.",
                table_body_style,
            ),
        ],
        [
            Paragraph("<code>src/core/logging.py</code>", table_body_style),
            Paragraph("Foundation", table_body_style),
            Paragraph(
                "Structured logging formatter with correlation support, ISO timestamps, and suppression of chatty dependencies.",
                table_body_style,
            ),
        ],
        [
            Paragraph("<code>src/core/exceptions.py</code>", table_body_style),
            Paragraph("Domain", table_body_style),
            Paragraph(
                "Domain exception hierarchy: <code>EntityNotFoundError</code>, <code>InvalidStateTransitionError</code>, <code>OptimisticLockError</code>, <code>DispatchError</code>.",
                table_body_style,
            ),
        ],
        [
            Paragraph("<code>src/core/database.py</code>", table_body_style),
            Paragraph("Persistence", table_body_style),
            Paragraph(
                "Dual-engine architecture: Async engine/session for FastAPI; Sync engine/session for Celery & Alembic; health check probe.",
                table_body_style,
            ),
        ],
        [
            Paragraph("<code>src/core/redis.py</code>", table_body_style),
            Paragraph("Broker", table_body_style),
            Paragraph(
                "Asynchronous Redis connection client with ping probe and graceful connection pool teardown.",
                table_body_style,
            ),
        ],
        [
            Paragraph("<code>src/models/base.py</code>", table_body_style),
            Paragraph("Persistence", table_body_style),
            Paragraph(
                "SQLAlchemy 2.0 <code>DeclarativeBase</code>, <code>TimestampMixin</code> (UTC tracking), and <code>VersionMixin</code> (optimistic locking counter).",
                table_body_style,
            ),
        ],
        [
            Paragraph("<code>src/models/task.py</code>", table_body_style),
            Paragraph("Persistence", table_body_style),
            Paragraph(
                "<code>TaskRecord</code> (authoritative state, payload, result, version) and <code>TaskExecutionAttempt</code> (audit log with unique attempt constraint).",
                table_body_style,
            ),
        ],
        [
            Paragraph("<code>src/models/worker.py</code>", table_body_style),
            Paragraph("Persistence", table_body_style),
            Paragraph(
                "<code>WorkerRecord</code> storing worker ID, hostname, PID, capabilities list, concurrency, and last heartbeat timestamp.",
                table_body_style,
            ),
        ],
        [
            Paragraph("<code>alembic/versions/0001_...</code>", table_body_style),
            Paragraph("Migrations", table_body_style),
            Paragraph(
                "DDL script creating tables <code>tasks</code>, <code>task_execution_attempts</code>, <code>workers</code>, foreign keys, and indexes.",
                table_body_style,
            ),
        ],
        [
            Paragraph("<code>src/api/v1/health.py</code>", table_body_style),
            Paragraph("Ingress API", table_body_style),
            Paragraph(
                "Liveness probe (<code>/health/live</code>) and readiness probe (<code>/health/ready</code>) returning 503 if DB or Redis is unavailable.",
                table_body_style,
            ),
        ],
        [
            Paragraph("<code>src/main.py</code>", table_body_style),
            Paragraph("Application", table_body_style),
            Paragraph(
                "FastAPI factory, lifespan lifecycle manager, and global exception mappers translating domain errors into HTTP 404, 409, and 503.",
                table_body_style,
            ),
        ],
        [
            Paragraph("<code>docker-compose.yml</code>", table_body_style),
            Paragraph("Deployment", table_body_style),
            Paragraph(
                "Orchestrates PostgreSQL 16 (with persistent volume), Redis 7, and FastAPI with health checks and service dependencies.",
                table_body_style,
            ),
        ],
    ]

    files_table = Table(files_data, colWidths=[120, 75, 309])
    files_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A365D")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(files_table)
    story.append(Spacer(1, 14))

    story.append(PageBreak())

    # Section 3: Complete End-to-End Execution Dry Run
    story.append(Paragraph("3. End-to-End Execution Dry Run: How Data Travels", h1_style))
    story.append(
        Paragraph(
            "Below is the exact execution dry run demonstrating how data flows from HTTP submission to worker execution, "
            "outcome persistence, and acknowledgement:",
            body_style,
        )
    )

    dry_run_ascii = """
[1. Client POST] ----> [2. Validate & Insert QUEUED] ----> [3. Dispatch to Redis Broker]
                             (PostgreSQL, v=1)                       (Celery send_task)
                                                                             |
[6. Late ACK]    <---- [5. Persist Outcome]         <---- [4. Claim & Start Attempt #1]
  (task_acks_late=True)   (status=SUCCEEDED, v=2)               (status=RUNNING, DB lock released)
"""
    story.append(
        Table(
            [[Preformatted(dry_run_ascii.strip(), code_block_style)]],
            colWidths=[504],
            style=[
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EDF2F7")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ],
        )
    )
    story.append(Spacer(1, 8))

    story.append(Paragraph("Step 1: Ingress & Validation (FastAPI)", h2_style))
    story.append(
        Paragraph(
            'The client sends <code>POST /api/v1/tasks</code> with payload <code>{"task_type": "compute.prime_factorization", "payload": {"n": 104729}}</code>. '
            "Pydantic schemas validate types. If validation fails, HTTP 422 is returned immediately with error details.",
            body_style,
        )
    )

    story.append(Paragraph("Step 2: Authoritative Persistence (PostgreSQL First)", h2_style))
    story.append(
        Paragraph(
            "The orchestrator persists a new <code>TaskRecord</code> in PostgreSQL inside an ACID transaction: "
            "<code>id = UUID</code>, <code>status = 'QUEUED'</code>, <code>version = 1</code>, <code>retry_count = 0</code>. "
            "<b>Dual-Write Invariant:</b> The record is committed to PostgreSQL <i>before</i> publishing to Redis. "
            "This guarantees no worker can ever process a task that does not exist in the database.",
            body_style,
        )
    )

    story.append(Paragraph("Step 3: Dispatch via Abstraction (Option A)", h2_style))
    story.append(
        Paragraph(
            "The orchestrator invokes <code>TaskDispatcher.dispatch(task)</code>. <code>CeleryQueueDispatcher</code> routes the message "
            "to Redis queue <code>celery</code>. If Redis times out or fails: the task is marked <code>DISPATCH_FAILED</code> and HTTP 503 is returned. "
            "<b>Ambiguous Publish Handling:</b> If Redis accepted the message before timing out, a worker will still pull it. "
            "When the worker detects status <code>DISPATCH_FAILED</code>, its claim reconciliation handler transitions it to <code>RUNNING</code> safely.",
            body_style,
        )
    )

    story.append(Paragraph("Step 4: Worker Pickup & Concurrency-Safe Claim (Phase 1)", h2_style))
    story.append(
        Paragraph(
            "An idle Celery worker consumes the message. Before running task logic, it opens a short Claim Transaction in PostgreSQL:<br/>"
            "• Executes conditional update: <code>UPDATE tasks SET status='RUNNING', version=version+1 WHERE id=:id AND status='QUEUED' AND version=:v</code>.<br/>"
            "• Inserts <code>TaskExecutionAttempt</code> with <code>attempt_number = 1</code>, <code>worker_id = 'worker-1'</code>, <code>status = 'RUNNING'</code>.<br/>"
            "• Commits the transaction and releases all database locks before executing user code.",
            body_style,
        )
    )

    story.append(Paragraph("Step 5: Pure Task Execution (Phase 2)", h2_style))
    story.append(
        Paragraph(
            "The worker executes decoupled Python business logic (e.g. prime factorization). "
            "Because database locks were released in Phase 1, long-running compute tasks never exhaust database connection pools.",
            body_style,
        )
    )

    story.append(Paragraph("Step 6: Outcome Persistence (Phase 3)", h2_style))
    story.append(
        Paragraph(
            "Upon completion, the worker opens a second transaction:<br/>"
            "• Updates <code>task_execution_attempts</code> (<code>status = 'SUCCEEDED'</code>, <code>completed_at = NOW()</code>, <code>duration_seconds = 0.042</code>).<br/>"
            "• Updates <code>tasks</code> (<code>status = 'SUCCEEDED'</code>, <code>result = {...}</code>, <code>version = version + 1</code>).<br/>"
            "• Commits the outcome transaction.",
            body_style,
        )
    )

    story.append(Paragraph("Step 7: Late Message Acknowledgement (Phase 4)", h2_style))
    story.append(
        Paragraph(
            "Because <code>task_acks_late = True</code>, Celery sends the message ACK to Redis <b>only after Phase 3 commits</b>.",
            body_style,
        )
    )

    story.append(Spacer(1, 10))

    # Section 4: Fault Tolerance & Distributed System Invariants
    story.append(Paragraph("4. Distributed Fault Tolerance & System Invariants", h1_style))

    fault_items = [
        "<b>Worker Crash During Execution (Phase 2):</b> The Redis message was never acknowledged. "
        "Because <code>task_reject_on_worker_lost = True</code>, the supervisor rejects the message upon child crash, and Redis requeues it. "
        "Worker 2 claims the task, sees attempt #1 was interrupted, logs attempt #2, and completes the work safely.",
        "<b>Worker Crash Between Phase 3 and Phase 4:</b> The task is committed as <code>SUCCEEDED</code> in PostgreSQL, but the worker dies before ACKing Redis. "
        "Redis redelivers the message. Worker 2 inspects PostgreSQL, discovers <code>status == 'SUCCEEDED'</code>, "
        "immediately sends ACK to Redis, and skips execution (<b>Idempotency Guard</b>).",
        "<b>The Non-Reassignment Invariant:</b> A worker heartbeat timeout (marked <code>STALE</code> after 30s) "
        "<b>must NEVER trigger automatic task reassignment by the orchestrator</b>. A missing heartbeat only reflects telemetry failure. "
        "Reassigning tasks based on heartbeats causes split-brain duplicate execution. Redelivery is governed solely by broker acknowledgements.",
        "<b>Visibility Timeout & Task Limits:</b> Redis <code>visibility_timeout</code> (3600s) strictly exceeds <code>task_time_limit</code> (1800s), "
        "guaranteeing Redis never redelivers a task while an active worker is still executing it.",
    ]

    for item in fault_items:
        story.append(Paragraph(f"• {item}", bullet_style))

    story.append(Spacer(1, 10))

    # Section 5: Verification Evidence
    story.append(Paragraph("5. Verification Evidence & Quality Metrics", h1_style))
    verif_text = (
        "<b>1. Automated Tests:</b> 13 tests passed in 0.60s covering config validation, domain exceptions, "
        "model creation, unique attempt constraints, and liveness/readiness health probes.<br/>"
        "<b>2. Code Standards:</b> 100% compliant with Ruff linting and formatting across all 19 files.<br/>"
        "<b>3. Database Schema:</b> Verified via <code>alembic upgrade base:head --sql</code>, generating clean transactional PostgreSQL DDL.<br/>"
        "<b>4. Git Versioning:</b> Committed as <code>dc9b2e7</code> on branch <code>main</code>."
    )
    story.append(Paragraph(verif_text, body_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF manual: {filename}")


if __name__ == "__main__":
    out_path = (
        sys.argv[1] if len(sys.argv) > 1 else "docs/distributed_automation_architecture_manual.pdf"
    )
    build_pdf(out_path)
