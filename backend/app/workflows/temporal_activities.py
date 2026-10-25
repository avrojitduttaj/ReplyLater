import os
import json
import logging
from datetime import timedelta
from typing import Dict, Any, List
from temporalio import activity
from temporalio.common import RetryPolicy

from app.db.database import AsyncSessionLocal
from app.db.models import Thread, Draft, ThreadStatus, DraftStatus
from app.services.parser_service import parser_service
from app.services.vector_service import vector_service
from app.services.gemma_service import gemma_service

logger = logging.getLogger("replylater.activities")

# Default activity retry policy to survive local LLM spikes
DEFAULT_RETRY_POLICY = RetryPolicy(
    maximum_attempts=3,
    initial_interval=timedelta(seconds=2),
    backoff_coefficient=2.0,
)
DEFAULT_TIMEOUT = timedelta(minutes=5)


@activity.defn(name="parse_and_store_eml_activity")
async def parse_and_store_eml_activity(input_data: str) -> str:
    """Parse .eml file or raw email content and persist the initial Thread in database.
    
    Returns the generated thread_id.
    """
    logger.info(f"Executing parse_and_store_eml_activity with input preview: {input_data[:80]}")

    # Check if input is a valid file path, JSON payload, or raw text
    if os.path.exists(input_data):
        parsed = parser_service.parse_file(input_data)
    else:
        try:
            # Check if JSON encoded dictionary
            data = json.loads(input_data)
            parsed = {
                "sender": data.get("sender", "unknown@sender.com"),
                "subject": data.get("subject", "(No Subject)"),
                "body": data.get("body", ""),
            }
        except Exception:
            parsed = parser_service.parse_raw_eml(input_data)

    async with AsyncSessionLocal() as session:
        thread = Thread(
            sender=parsed["sender"],
            subject=parsed["subject"],
            raw_body=parsed["body"],
            status=ThreadStatus.PENDING,
        )
        session.add(thread)
        await session.commit()
        await session.refresh(thread)
        logger.info(f"Persisted thread {thread.id} for sender {thread.sender}")
        return thread.id


@activity.defn(name="retrieve_style_context_activity")
async def retrieve_style_context_activity(thread_id: str) -> List[str]:
    """Retrieve top-k user style samples from pgvector/vector memory matching thread body."""
    async with AsyncSessionLocal() as session:
        thread = await session.get(Thread, thread_id)
        if thread is None:
            raise ValueError(f"Thread {thread_id} not found")
        logger.info(
            "Executing retrieve_style_context_activity for body length %s",
            len(thread.raw_body),
        )
        samples = await vector_service.retrieve_style_context(
            session,
            thread.raw_body,
            top_k=2,
        )
        logger.info(f"Found {len(samples)} style context samples")
        return samples


@activity.defn(name="classify_and_draft_activity")
async def classify_and_draft_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    """Classify email via Gemma, extract commitments/uncertainty, and generate reply draft."""
    thread_id = params.get("thread_id")
    style_samples = params.get("style_samples", [])

    logger.info(f"Executing classify_and_draft_activity for thread {thread_id}")

    async with AsyncSessionLocal() as session:
        thread = await session.get(Thread, thread_id)
        if not thread:
            raise ValueError(f"Thread {thread_id} not found")

        # 1. Analyze incoming email with Gemma
        analysis = await gemma_service.analyze_incoming_email(thread.subject, thread.raw_body)
        logger.info(f"Gemma analysis for {thread_id}: {analysis}")

        needs_reply = analysis.get("needs_reply", True)
        suggested_weekday = analysis.get("suggested_weekday", "Monday")
        detected_deadline = analysis.get("detected_deadline")
        commitments = analysis.get("commitments", [])
        has_uncertainty = analysis.get("has_uncertainty", False)
        missing_question = analysis.get("missing_question")

        # 2. Case A: Non-actionable or automated info (Archive immediately)
        if not needs_reply:
            thread.status = ThreadStatus.ARCHIVED
            await session.commit()
            return {
                "thread_id": thread_id,
                "status": "ARCHIVED",
                "draft_id": None,
                "details": "Classified as informational/closed",
            }

        # 3. Case B: Ambiguous / Missing user decision (Channel sloth ethos: do not hallucinate)
        if has_uncertainty and missing_question:
            thread.status = ThreadStatus.NEEDS_INPUT
            draft = Draft(
                thread_id=thread.id,
                status=DraftStatus.NEEDS_INPUT,
                suggested_weekday=suggested_weekday,
                detected_deadline=detected_deadline,
                commitments_found=commitments,
                missing_info_question=missing_question,
                proposed_reply="",
            )
            session.add(draft)
            await session.commit()
            await session.refresh(draft)
            return {
                "thread_id": thread_id,
                "status": "NEEDS_INPUT",
                "draft_id": draft.id,
                "question": missing_question,
            }

        # 4. Case C: Clear action items (Draft ready for week schedule)
        draft_reply = await gemma_service.generate_draft_reply(
            subject=thread.subject,
            body=thread.raw_body,
            context_samples=style_samples,
        )

        thread.status = ThreadStatus.SCHEDULED
        draft = Draft(
            thread_id=thread.id,
            status=DraftStatus.SCHEDULED,
            suggested_weekday=suggested_weekday,
            detected_deadline=detected_deadline,
            commitments_found=commitments,
            missing_info_question=None,
            proposed_reply=draft_reply,
        )
        session.add(draft)
        await session.commit()
        await session.refresh(draft)

        return {
            "thread_id": thread_id,
            "status": "SCHEDULED",
            "draft_id": draft.id,
            "suggested_weekday": suggested_weekday,
        }
