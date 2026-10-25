import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.db.models import Thread, Draft, ThreadStatus, DraftStatus
from app.services.gemma_service import gemma_service
from app.services.vector_service import vector_service
from app.core.config import settings

logger = logging.getLogger("replylater.api")

router = APIRouter()


class ResolveInputRequest(BaseModel):
    draft_id: str
    clarification: str


class UpdateDraftRequest(BaseModel):
    proposed_reply: str


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ReplyLater API",
        "privacy": "0 KB cloud egress (Local-First)",
        "model": settings.GEMMA_MODEL,
        "temporal_queue": settings.TEMPORAL_TASK_QUEUE,
    }


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Summary metrics for the top bar badges."""
    threads_res = await db.execute(select(Thread))
    all_threads = threads_res.scalars().all()

    drafts_res = await db.execute(select(Draft))
    all_drafts = drafts_res.scalars().all()

    needs_input_count = sum(1 for d in all_drafts if d.status == DraftStatus.NEEDS_INPUT)
    scheduled_count = sum(1 for d in all_drafts if d.status == DraftStatus.SCHEDULED)
    approved_count = sum(1 for d in all_drafts if d.status == DraftStatus.APPROVED)
    archived_count = sum(1 for t in all_threads if t.status == ThreadStatus.ARCHIVED)

    return {
        "open_source_core": f"Gemma 2B via Ollama ({settings.GEMMA_MODEL})",
        "cloud_egress": "0 KB (Local-First)",
        "orchestrator": "Temporal Durable Engine",
        "traces": "Sentry AI Agent Telemetry",
        "counts": {
            "total_threads": len(all_threads),
            "needs_input": needs_input_count,
            "scheduled": scheduled_count,
            "approved": approved_count,
            "archived": archived_count,
        },
    }


@router.get("/board")
async def get_board(db: AsyncSession = Depends(get_db)):
    """Returns the 3-bucket review board data:
    
    1. needs_input: Drafts where Gemma refused to hallucinate and requested user call.
    2. week_queue: Drafts grouped into Monday through Friday with deadlines & commitments.
    3. archived: Auto-archived newsletters, receipts, and FYIs.
    """
    # 1. Fetch Needs Input Drafts
    needs_input_stmt = (
        select(Draft)
        .options(selectinload(Draft.thread))
        .where(Draft.status == DraftStatus.NEEDS_INPUT)
        .order_by(Draft.created_at.desc())
    )
    needs_input_res = await db.execute(needs_input_stmt)
    needs_input_drafts = [d.to_dict() for d in needs_input_res.scalars().all()]

    # 2. Fetch Week-Ahead Queue (SCHEDULED or APPROVED)
    week_stmt = (
        select(Draft)
        .options(selectinload(Draft.thread))
        .where(Draft.status.in_([DraftStatus.SCHEDULED, DraftStatus.APPROVED]))
        .order_by(Draft.created_at.desc())
    )
    week_res = await db.execute(week_stmt)
    week_drafts = week_res.scalars().all()

    week_queue: Dict[str, List[Dict[str, Any]]] = {
        "Monday": [],
        "Tuesday": [],
        "Wednesday": [],
        "Thursday": [],
        "Friday": [],
    }

    for d in week_drafts:
        day = d.suggested_weekday if d.suggested_weekday in week_queue else "Monday"
        week_queue[day].append(d.to_dict())

    # 3. Fetch Archived Threads (Informational / Closed)
    archived_stmt = (
        select(Thread)
        .where(Thread.status == ThreadStatus.ARCHIVED)
        .order_by(Thread.received_at.desc())
    )
    archived_res = await db.execute(archived_stmt)
    archived_threads = [t.to_dict() for t in archived_res.scalars().all()]

    return {
        "needs_input": needs_input_drafts,
        "week_queue": week_queue,
        "archived": archived_threads,
    }


@router.post("/resolve-input")
async def resolve_input(payload: ResolveInputRequest, db: AsyncSession = Depends(get_db)):
    """Accepts user clarification for a draft, regenerates draft with Gemma, shifts status to SCHEDULED."""
    draft = await db.get(Draft, payload.draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    thread = await db.get(Thread, draft.thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Associated thread not found")

    # Retrieve style context
    style_samples = await vector_service.retrieve_style_context(db, thread.raw_body, top_k=2)

    # Generate complete draft incorporating clarification
    new_reply = await gemma_service.generate_draft_reply(
        subject=thread.subject,
        body=thread.raw_body,
        context_samples=style_samples,
        user_clarification=payload.clarification,
    )

    # Update draft
    draft.user_clarification = payload.clarification
    draft.proposed_reply = new_reply
    draft.status = DraftStatus.SCHEDULED
    draft.missing_info_question = None

    # Update thread status
    thread.status = ThreadStatus.SCHEDULED

    await db.commit()
    await db.refresh(draft)

    return {
        "message": "Draft successfully regenerated and scheduled.",
        "draft": draft.to_dict(),
    }


@router.post("/approve-draft/{draft_id}")
async def approve_draft(draft_id: str, db: AsyncSession = Depends(get_db)):
    """Marks a scheduled draft as APPROVED ready for delivery."""
    draft = await db.get(Draft, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    draft.status = DraftStatus.APPROVED
    await db.commit()
    await db.refresh(draft)

    return {
        "message": "Draft approved.",
        "draft": draft.to_dict(),
    }


@router.put("/drafts/{draft_id}")
async def update_draft(draft_id: str, payload: UpdateDraftRequest, db: AsyncSession = Depends(get_db)):
    """Allows user to manually tweak or edit the proposed reply text."""
    draft = await db.get(Draft, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    draft.proposed_reply = payload.proposed_reply
    await db.commit()
    await db.refresh(draft)

    return {
        "message": "Draft updated.",
        "draft": draft.to_dict(),
    }


@router.post("/trigger-seed-batch")
async def trigger_seed_batch():
    """Ingests 5 built-in realistic mock emails immediately and runs the triage workflow."""
    from seed_samples import seed_demo_backlog
    results = await seed_demo_backlog()
    return {
        "message": f"Successfully ingested and triaged {len(results)} demo emails.",
        "processed_count": len(results),
        "results": results,
    }
