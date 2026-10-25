import logging
from datetime import timedelta
from typing import List, Dict, Any
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from app.workflows.temporal_activities import (
        parse_and_store_eml_activity,
        retrieve_style_context_activity,
        classify_and_draft_activity,
        DEFAULT_RETRY_POLICY,
        DEFAULT_TIMEOUT,
    )
    from app.db.database import AsyncSessionLocal
    from app.db.models import Thread
    from app.core.config import settings

logger = logging.getLogger("replylater.workflow")


@workflow.defn
class OvernightEmailPrepWorkflow:
    """Temporal durable workflow managing overnight batch email triage.
    
    Processes incoming emails sequentially to prevent local LLM/GPU saturation
    (channeling the sloth ethos: slow and steady).
    """

    @workflow.run
    async def run(self, email_items: List[str]) -> List[Dict[str, Any]]:
        workflow.logger.info(f"Starting OvernightEmailPrepWorkflow for {len(email_items)} emails")
        results = []

        for item in email_items:
            # 1. Parse and store raw email as Thread
            thread_id = await workflow.execute_activity(
                parse_and_store_eml_activity,
                item,
                start_to_close_timeout=DEFAULT_TIMEOUT,
                retry_policy=DEFAULT_RETRY_POLICY,
            )

            # Note: Fetch body or pass thread details
            # To preserve activity isolation, pass input or fetch in activity
            # 2. Retrieve style context from vector memory
            style_samples = await workflow.execute_activity(
                retrieve_style_context_activity,
                item[:500],
                start_to_close_timeout=DEFAULT_TIMEOUT,
                retry_policy=DEFAULT_RETRY_POLICY,
            )

            # 3. Classify, detect commitments, and generate draft
            outcome = await workflow.execute_activity(
                classify_and_draft_activity,
                {"thread_id": thread_id, "style_samples": style_samples},
                start_to_close_timeout=DEFAULT_TIMEOUT,
                retry_policy=DEFAULT_RETRY_POLICY,
            )

            results.append(outcome)

        workflow.logger.info(f"Completed OvernightEmailPrepWorkflow with {len(results)} items processed")
        return results


async def run_overnight_pipeline_direct(email_items: List[str]) -> List[Dict[str, Any]]:
    """Direct execution runner when Temporal server is not active in the local developer session.
    
    Runs identical sequential logic as the Temporal workflow to maintain parity.
    """
    results = []
    for item in email_items:
        # Step 1: Parse & Store
        thread_id = await parse_and_store_eml_activity(item)

        # Step 2: Retrieve Style Samples
        async with AsyncSessionLocal() as session:
            thread = await session.get(Thread, thread_id)
            body = thread.raw_body if thread else ""

        style_samples = await retrieve_style_context_activity(body)

        # Step 3: Classify & Draft
        outcome = await classify_and_draft_activity({"thread_id": thread_id, "style_samples": style_samples})
        results.append(outcome)

    return results


def is_temporal_available(host: str) -> bool:
    """Fast check whether Temporal server port is listening."""
    import socket
    try:
        parts = host.split(":")
        h = parts[0]
        p = int(parts[1]) if len(parts) > 1 else 7233
        with socket.create_connection((h, p), timeout=0.3):
            return True
    except Exception:
        return False


async def trigger_email_batch_workflow(email_items: List[str]) -> List[Dict[str, Any]]:
    """Dispatch email batch through Temporal if connected, or direct fallback runner."""
    if is_temporal_available(settings.TEMPORAL_HOST):
        try:
            from temporalio.client import Client
            client = await Client.connect(settings.TEMPORAL_HOST, namespace="default")
            handle = await client.start_workflow(
                OvernightEmailPrepWorkflow.run,
                email_items,
                id=f"overnight-prep-{int(timedelta().total_seconds())}",
                task_queue=settings.TEMPORAL_TASK_QUEUE,
            )
            logger.info(f"Triggered Temporal workflow with run id {handle.run_id}")
            result = await handle.result()
            return result
        except Exception as e:
            logger.warning(f"Temporal execution error ({e}). Executing pipeline locally.")
            return await run_overnight_pipeline_direct(email_items)

    logger.info(f"Temporal server not listening at {settings.TEMPORAL_HOST}. Executing pipeline directly.")
    return await run_overnight_pipeline_direct(email_items)
