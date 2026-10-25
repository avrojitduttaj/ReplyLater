# 🦥 ReplyLater — Overnight Email Co-Pilot

> **"Go to sleep with an inbox full of obligations. Wake up with next week's replies ready."**  
> *Built for the Hacktoberfest DEV Challenge: "Slow and Steady: Channel Your Inner Sloth"*

---

## 🔒 The Privacy Core: 0 KB Cloud Egress

Traditional email AI tools upload your sensitive emails, attachments, and client conversations to external LLM providers. **ReplyLater** guarantees **0 KB external cloud egress for email bodies**.

- **All LLM Inference runs 100% locally** via Ollama targeting `gemma2:2b`.
- **Durable Overnight Orchestration** is managed by Temporal to triage at a calm, steady pace, preventing local GPU spikes.
- **Style Memory** stores vectors in SQLite locally or PostgreSQL + pgvector in Docker. A compatible local embedding model is required for semantic matching; the deterministic offline fallback keeps the demo running but is not semantic.
- **Content-free Telemetry** is tracked through **Sentry AI Agent Tracing** (`_experiments={"enable_ai_agent_tracing": True}`); spans record model, step, character/token counts, latency, and error type, never email or draft text.

---

## 🏆 Partner Targets & Architecture

| Partner | Target Role in ReplyLater |
|---|---|
| **Google Gemma ($200)** | Local inference (`gemma2:2b`) for classification, extracted commitments, deadline detection, and style-conditioned drafting. |
| **Temporal ($100)** | Long-running durable workflow (`OvernightEmailPrepWorkflow`) managing sequential batch triage, retry policies, and overnight step orchestration. |
| **Sentry Agent Tracing ($100)** | Content-free LLM spans (`gen_ai.gemma`) recording model, step, character/token counts, latency, and sanitized error type via `sentry-sdk`. |
| **Tiger Data / PostgreSQL + pgvector ($100)** | Persistent storage for style vectors; semantic matching depends on a compatible local embedding model. |

---

## 📁 Repository Layout

```text
replylater/
├── docker-compose.yml              # Multi-container stack (Postgres/pgvector, Temporal, Backend, Worker)
├── backend/
│   ├── requirements.txt            # Python dependencies (FastAPI, SQLAlchemy, Temporal, Sentry, pgvector)
│   ├── main.py                     # FastAPI server entry point & lifespan manager
│   ├── worker.py                   # Temporal worker for `email-triage-queue`
│   ├── seed_samples.py             # 5 realistic demo scenarios & style memory seeder
│   └── app/
│       ├── core/
│       │   ├── config.py           # Pydantic settings & environment configuration
│       │   └── sentry.py           # Sentry AI Agent tracing span decorator & telemetry
│       ├── db/
│       │   ├── database.py         # Async SQLAlchemy engine with SQLite & pgvector support
│       │   └── models.py           # Thread, StyleSample, and Draft models
│       ├── services/
│       │   ├── gemma_service.py    # Local Ollama client with deterministic offline fallback
│       │   ├── parser_service.py   # RFC-822 .eml parser extracting sender, subject & clean body
│       │   └── vector_service.py   # pgvector semantic memory & cosine similarity retrieval
│       ├── workflows/
│       │   ├── temporal_workflow.py   # OvernightEmailPrepWorkflow implementation
│       │   └── temporal_activities.py # Ingestion, Vector retrieval, Classification & Drafting activities
│       └── api/
│           └── routes.py           # /board, /resolve-input, /approve-draft, /trigger-seed-batch
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.js
    └── src/
        ├── App.tsx                 # Main application dashboard & state
        ├── main.tsx                # React root mount
        └── components/
            ├── Header.tsx          # Top metrics bar with partner badges & trigger button
            ├── KanbanBoard.tsx     # 3-Bucket Review Board (Needs Call, Week Queue, Closed)
            ├── NeedsInputCard.tsx  # Anti-hallucination card with inline decision input
            ├── DraftCard.tsx       # Scheduled draft with commitment pills & editable text
            └── SeedBanner.tsx      # Sloth ethos introductory hero banner
```

---

## ⚡ Quickstart

### Option A: Complete Docker Compose Stack

Start all services (PostgreSQL with pgvector, Temporal server, FastAPI backend, and Temporal worker):

```bash
docker compose up --build
```

- **FastAPI API & Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Temporal Web UI**: [http://localhost:8233](http://localhost:8233)
- **PostgreSQL / pgvector**: `localhost:5432`

---

### Option B: Local Zero-Config Development (No Docker Required)

ReplyLater is built with graceful fallbacks (SQLite local vector storage and deterministic offline model resilience) so anyone can clone and run it instantly.

#### 1. Start the Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate | macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

*The backend starts at `http://localhost:8000`.*

On Windows, if more than one virtual environment exists, run commands through the project environment explicitly from `backend`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

#### 2. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

*The dashboard will be live at `http://localhost:5173`.*

---

## 📋 The 3-Bucket Review Board

1. **"Needs Your Call" (Amber)**: Shows cards where Gemma refused to hallucinate personal decisions (e.g., freelance hourly rate or start availability). Includes an inline prompt and a "Complete Draft" button that regenerates the reply and shifts it to the week schedule.
2. **"Week-Ahead Queue" (Emerald)**: Organizes replies by Monday–Friday. Displays detected deadlines, extracted commitments in pill badges, editable drafts, and a one-click "Approve & Schedule" button.
3. **"Info / Closed" (Slate)**: Auto-archived newsletters, receipts, and FYIs requiring zero human effort.

---

## 🧪 5 Realistic Demo Scenarios

Click **"Load Demo Backlog (5 Emails)"** in the top bar or run `python backend/seed_samples.py` to ingest:

1. **Urgent Client Bug** (*Monday Morning*): Production checkout 500 error requiring immediate update. Extracted commitment: *"Investigate checkout crash logs and update by 11 AM"*.
2. **Ambiguous Freelance Scope** (*Needs Your Call*): Client asking for hourly rate and availability. Gemma refuses to guess and triggers the anti-hallucination prompt.
3. **Weekly Newsletter** (*Auto-Archived*): `DEV Digest` weekly community newsletter routed to Info/Closed.
4. **Colleague Coordination** (*Wednesday 4 PM*): Q4 roadmap review sync with detected calendar commitment.
5. **Hosting Receipt** (*Auto-Archived*): Paid invoice confirmation requiring zero action.

---

## 🛡️ License

MIT License. Open-source for the Hacktoberfest DEV Challenge.
