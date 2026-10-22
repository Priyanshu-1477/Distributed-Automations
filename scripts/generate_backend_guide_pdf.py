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
                "The Backend Engineer's Guide — Working with Headless Distributed Systems",
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
            "Distributed Automation Platform — Developer Workflow & Hands-On Inspection Guide",
        )
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 32, page_str)
        self.restoreState()


def build_pdf(filename="docs/backend_developer_guide.pdf"):
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

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#4A5568"),
        spaceAfter=14,
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#1A365D"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=5,
    )

    callout_style = ParagraphStyle(
        "Callout",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=12,
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
        fontSize=8,
        leading=10,
        textColor=colors.white,
    )

    table_body_style = ParagraphStyle(
        "TableBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#2D3748"),
    )

    story = []

    # Title & Subtitle
    story.append(Paragraph("The Backend Engineer's Survival Guide", title_style))
    story.append(
        Paragraph(
            "<b>Mastering, Inspecting, and Debugging Headless Distributed Systems</b><br/>"
            "A Practical Manual for Developing with FastAPI, Celery, Redis, and PostgreSQL Without a Frontend",
            subtitle_style,
        )
    )

    # Executive Box
    banner_text = (
        "<b>Why 'Backend-First' is a Superpower:</b> In distributed systems engineering, building without a UI is standard practice. "
        "A frontend only reflects the state of the system; the actual reliability, consensus, state machine integrity, "
        "and concurrency guarantees happen strictly in the backend. This guide teaches you the exact tools, inspection techniques, "
        "and mental models senior engineers use to 'see' and control the entire distributed platform directly from your terminal and browser."
    )
    banner_table = Table([[Paragraph(banner_text, callout_style)]], colWidths=[504])
    banner_table.setStyle(
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
    story.append(banner_table)
    story.append(Spacer(1, 10))

    # Section 1: The 4 Lenses of Headless Development
    story.append(Paragraph("1. The 4 Lenses of Headless Backend Engineering", h1_style))
    story.append(
        Paragraph(
            "When you don't have a graphical user interface, you inspect the system through four distinct operational lenses:",
            body_style,
        )
    )

    lenses_data = [
        [
            Paragraph("Lens", table_header_style),
            Paragraph("Component", table_header_style),
            Paragraph("Primary Tool", table_header_style),
            Paragraph("What You Are Inspecting & Verifying", table_header_style),
        ],
        [
            Paragraph("<b>1. Ingress Lens</b>", table_body_style),
            Paragraph("FastAPI", table_body_style),
            Paragraph("Swagger UI (<code>/docs</code>)<br/>cURL / HTTPie", table_body_style),
            Paragraph(
                "Submitting requests, triggering validation errors, receiving status codes (200, 202, 404, 409, 503).",
                table_body_style,
            ),
        ],
        [
            Paragraph("<b>2. Broker Lens</b>", table_body_style),
            Paragraph("Redis 7", table_body_style),
            Paragraph("<code>redis-cli</code><br/>Redis Insight", table_body_style),
            Paragraph(
                "Verifying task messages enqueued, checking queue lengths, observing message consumption in real time.",
                table_body_style,
            ),
        ],
        [
            Paragraph("<b>3. Execution Lens</b>", table_body_style),
            Paragraph("Celery Workers", table_body_style),
            Paragraph("Terminal logs<br/><code>celery inspect</code>", table_body_style),
            Paragraph(
                "Watching workers claim jobs, run tasks, apply backoff countdowns, and report success or failure.",
                table_body_style,
            ),
        ],
        [
            Paragraph("<b>4. State Lens</b>", table_body_style),
            Paragraph("PostgreSQL 16", table_body_style),
            Paragraph("<code>psql</code> CLI<br/>DBeaver / TablePlus", table_body_style),
            Paragraph(
                "Checking the authoritative single source of truth: task state transitions, version counters, attempt history.",
                table_body_style,
            ),
        ],
    ]

    t_lenses = Table(lenses_data, colWidths=[80, 80, 110, 234])
    t_lenses.setStyle(
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
    story.append(t_lenses)
    story.append(Spacer(1, 10))

    # Section 2: Lens 1 - FastAPI Interactive Swagger UI
    story.append(Paragraph("2. Lens 1: FastAPI Swagger UI (Your Built-In Frontend)", h1_style))
    story.append(
        Paragraph(
            "FastAPI automatically generates an interactive graphical web interface. You do not need to wait for a custom frontend "
            "to test and interact with your backend:",
            body_style,
        )
    )

    story.append(
        Paragraph(
            "• <b>Access Swagger UI:</b> Start your server with <code>uvicorn src.main:app --reload</code> and visit <b><code>http://localhost:8000/docs</code></b> in any browser.<br/>"
            "• <b>One-Click Execution:</b> Click on any endpoint (e.g. <code>GET /health/ready</code>), click <b>'Try it out'</b>, then click <b>'Execute'</b>. You instantly see the exact HTTP response code, response headers, and formatted JSON output.<br/>"
            "• <b>Live Schema Documentation:</b> Swagger renders the Pydantic schema for every request body, showing required vs optional fields and type constraints.<br/>"
            "• <b>Alternative ReDoc View:</b> Visit <b><code>http://localhost:8000/redoc</code></b> for clean, publication-style documentation.",
            body_style,
        )
    )
    story.append(Spacer(1, 8))

    # Section 3: Lens 2 - Terminal cURL & HTTPie Recipes
    story.append(Paragraph("3. Lens 2: Terminal HTTP Testing Recipes", h1_style))
    story.append(
        Paragraph(
            "Senior backend engineers frequently test endpoints directly from the command line using <code>curl</code> or <code>httpie</code>:",
            body_style,
        )
    )

    curl_recipes = """
# 1. Check Liveness Probe (Returns HTTP 200 {"status": "alive"})
curl -i http://localhost:8000/health/live

# 2. Check Readiness Probe (Checks Postgres & Redis connectivity)
curl -i http://localhost:8000/health/ready

# 3. Submit a Computational Task (Prime Factorization)
curl -i -X POST http://localhost:8000/api/v1/tasks \\
  -H "Content-Type: application/json" \\
  -d '{"task_type": "compute.prime_factorization", "payload": {"n": 982451653}}'

# 4. Submit a Configurable Delayed Task (Simulated Sleep)
curl -i -X POST http://localhost:8000/api/v1/tasks \\
  -H "Content-Type: application/json" \\
  -d '{"task_type": "delayed.sleep_and_echo", "payload": {"delay_seconds": 5}}'

# 5. Poll Task Status and Attempt History
curl -i http://localhost:8000/api/v1/tasks/<TASK_UUID>

# 6. Request Task Cancellation
curl -i -X POST http://localhost:8000/api/v1/tasks/<TASK_UUID>/cancel
"""
    story.append(
        Table(
            [[Preformatted(curl_recipes.strip(), code_block_style)]],
            colWidths=[504],
            style=[
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ],
        )
    )
    story.append(Spacer(1, 10))

    story.append(PageBreak())

    # Section 4: Lens 3 - Inspecting Durable State in PostgreSQL
    story.append(Paragraph("4. Lens 3: Inspecting Authoritative State in PostgreSQL", h1_style))
    story.append(
        Paragraph(
            "PostgreSQL is where true state lives. When you want to verify what happened behind the scenes, "
            "you query the tables directly using the <code>psql</code> CLI or visual GUI clients:",
            body_style,
        )
    )

    psql_commands = """
# Connect to PostgreSQL container or local database
psql -h localhost -U postgres -d automation_db

# Inside psql prompt:
-- 1. List all tables and row counts
\\dt+

-- 2. Inspect the latest submitted tasks
SELECT id, task_type, status, version, retry_count, created_at, updated_at
FROM tasks
ORDER BY created_at DESC LIMIT 5;

-- 3. Inspect execution attempts (worker identity, duration, error trace)
SELECT attempt_number, worker_id, status, duration_seconds, error_message, started_at, completed_at
FROM task_execution_attempts
WHERE task_id = '<TASK_UUID>'
ORDER BY attempt_number ASC;

-- 4. Check registered workers and last heartbeat timestamps
SELECT worker_id, hostname, status, concurrency, last_heartbeat_at
FROM workers;
"""
    story.append(
        Table(
            [[Preformatted(psql_commands.strip(), code_block_style)]],
            colWidths=[504],
            style=[
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ],
        )
    )
    story.append(Spacer(1, 8))

    story.append(
        Paragraph(
            "<b>Recommended Visual Database Clients (Free & Cross-Platform):</b><br/>"
            "• <b>DBeaver:</b> Full-featured database management GUI with table inspection, query editor, and visual ER diagrams.<br/>"
            "• <b>TablePlus:</b> Modern, lightning-fast native client with inline row editing and real-time updates.<br/>"
            "• <b>VS Code Extension:</b> Install 'PostgreSQL' by Chris Kolkman to query tables directly inside your editor.",
            body_style,
        )
    )
    story.append(Spacer(1, 10))

    # Section 5: Lens 4 - Inspecting Ephemeral Messaging in Redis
    story.append(Paragraph("5. Lens 4: Inspecting Operational Messaging in Redis", h1_style))
    story.append(
        Paragraph(
            "Redis moves task messages between the orchestrator and Celery workers. You can watch tasks travel through Redis queues in real time:",
            body_style,
        )
    )

    redis_commands = """
# Connect to Redis CLI
redis-cli

# Inside redis-cli:
-- 1. Ping Redis server
PING                          # Returns PONG

-- 2. Inspect all active keys in the database
KEYS *

-- 3. Check how many tasks are waiting in the queue
LLEN celery                   # Returns queue depth (e.g. 0 if workers are fast)

-- 4. View task payloads waiting in queue (without removing them)
LRANGE celery 0 -1

-- 5. Monitor all Redis commands in real-time (live stream)
MONITOR                       # Shows RPUSH from FastAPI and BRPOP from Celery!
"""
    story.append(
        Table(
            [[Preformatted(redis_commands.strip(), code_block_style)]],
            colWidths=[504],
            style=[
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ],
        )
    )
    story.append(Spacer(1, 8))

    story.append(
        Paragraph(
            "<b>Visual Redis Tool: Redis Insight:</b> Official free visual tool from Redis Ltd. Provides visual key browsers, "
            "queue stream visualizers, and memory profiling. You can run it via Docker: <code>docker run -d -p 5540:5540 redis/redisinsight</code>.",
            body_style,
        )
    )
    story.append(Spacer(1, 10))

    # Section 6: Celery Worker Inspection & Flower Dashboard
    story.append(Paragraph("6. Celery Worker Inspection & Flower Web Dashboard", h1_style))
    story.append(
        Paragraph(
            "Celery provides built-in command-line inspection and a real-time web monitoring dashboard called <b>Flower</b>:",
            body_style,
        )
    )

    story.append(
        Paragraph(
            "• <b>Inspect Active Workers:</b> <code>celery -A src.worker.celery_app.celery_app status</code><br/>"
            "• <b>Inspect Running Tasks:</b> <code>celery -A src.worker.celery_app.celery_app inspect active</code><br/>"
            "• <b>Flower Web Dashboard:</b> Install Flower via <code>pip install flower</code> and start it with:<br/>"
            "  <code>celery -A src.worker.celery_app.celery_app flower --port=5555</code><br/>"
            "  Visit <b><code>http://localhost:5555</code></b> to view worker CPU load, task execution charts, failure rates, and retry counts graphically!",
            body_style,
        )
    )
    story.append(Spacer(1, 10))

    story.append(PageBreak())

    # Section 7: The Senior Backend Engineer's 4-Step Verification Cycle
    story.append(Paragraph("7. The 4-Step Backend Development Loop", h1_style))
    story.append(
        Paragraph(
            "When implementing or testing any new task type or feature, senior backend engineers use this 4-step verification loop:",
            body_style,
        )
    )

    loop_ascii = """
 [Step 1: Ingress]  ----->  [Step 2: Broker]  ----->  [Step 3: Worker]  ----->  [Step 4: State]
 Submit via Swagger         Watch queue depth         Watch terminal log       Query PostgreSQL
 or cURL (Get 202)          in redis-cli (LLEN)       for execution attempt    for SUCCEEDED & attempts
"""
    story.append(
        Table(
            [[Preformatted(loop_ascii.strip(), code_block_style)]],
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

    story.append(Paragraph("Step 1: Submit the Task via Swagger or cURL", h2_style))
    story.append(
        Paragraph(
            "Open <code>http://localhost:8000/docs</code> or run a cURL command. Submit the request. "
            "Verify you receive HTTP 202 Accepted with a JSON body containing the generated <code>id</code> and status <code>QUEUED</code>.",
            body_style,
        )
    )

    story.append(Paragraph("Step 2: Observe Operational Enqueueing in Redis", h2_style))
    story.append(
        Paragraph(
            "In a terminal running <code>redis-cli monitor</code>, verify that an <code>RPUSH celery</code> command was issued by the orchestrator.",
            body_style,
        )
    )

    story.append(Paragraph("Step 3: Watch Celery Worker Process Logs", h2_style))
    story.append(
        Paragraph(
            "In your Celery worker terminal, watch the structured logs. You will see:<br/>"
            "<code>[INFO] Received task: compute.prime_factorization[uuid]</code><br/>"
            "<code>[INFO] Task compute.prime_factorization[uuid] succeeded in 0.042s</code>",
            body_style,
        )
    )

    story.append(Paragraph("Step 4: Verify Final Persistent State in PostgreSQL", h2_style))
    story.append(
        Paragraph(
            "Run <code>SELECT status, version, result FROM tasks WHERE id = '<id>';</code> in <code>psql</code>. "
            "Verify the status is <code>SUCCEEDED</code>, the <code>version</code> incremented to <code>2</code>, and the output result is recorded. "
            "Query <code>task_execution_attempts</code> to verify duration and worker attribution.",
            body_style,
        )
    )
    story.append(Spacer(1, 10))

    # Section 8: Interactive Python REPL Testing
    story.append(Paragraph("8. Interactive Python REPL: Inspecting Code Without HTTP", h1_style))
    story.append(
        Paragraph(
            "You can test database queries and domain logic directly inside an interactive Python shell without running the web server:",
            body_style,
        )
    )

    repl_code = """
$ python
>>> from src.core.database import get_sync_session
>>> from src.models import TaskRecord, WorkerRecord
>>>
>>> with get_sync_session() as session:
...     tasks = session.query(TaskRecord).all()
...     print(f"Total tasks in database: {len(tasks)}")
...     for t in tasks:
...         print(f"Task {t.id}: status={t.status}, version={t.version}")
"""
    story.append(
        Table(
            [[Preformatted(repl_code.strip(), code_block_style)]],
            colWidths=[504],
            style=[
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ],
        )
    )
    story.append(Spacer(1, 10))

    # Section 9: Summary & Frontend Transition Roadmap
    story.append(Paragraph("9. Roadmap: When and How the Frontend Connects Later", h1_style))
    story.append(
        Paragraph(
            "Because we strictly adhere to clean REST principles and Pydantic schemas, when we are ready to build a frontend later "
            "(e.g. Next.js, React, or Vue), the frontend will simply be a presentation layer over these exact endpoints:<br/>"
            "• <b>Task Dashboard:</b> Calls <code>GET /api/v1/tasks</code> to display a paginated table of tasks with live badges.<br/>"
            "• <b>Submit Modal:</b> Calls <code>POST /api/v1/tasks</code> with user-selected parameters.<br/>"
            "• <b>Worker Fleet Monitor:</b> Calls <code>GET /api/v1/workers</code> to display a live server topology diagram with green/yellow/red health lights.<br/>"
            "• <b>Cancellation Button:</b> Calls <code>POST /api/v1/tasks/{id}/cancel</code>.<br/>"
            "Until then, you have full graphical control via Swagger UI, DBeaver, and Redis Insight!",
            body_style,
        )
    )

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated: {filename}")


if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "docs/backend_developer_guide.pdf"
    build_pdf(out_file)
