import asyncio
import logging
import signal
from temporalio.client import Client
from temporalio.worker import Worker

from app.core.config import settings
from app.workflows.temporal_activities import (
    parse_and_store_eml_activity,
    retrieve_style_context_activity,
    classify_and_draft_activity,
)
from app.workflows.temporal_workflow import OvernightEmailPrepWorkflow
from app.db.database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [Temporal Worker] %(message)s",
)
logger = logging.getLogger("replylater.worker")


async def run_worker():
    logger.info("Initializing database connection...")
    await init_db()

    logger.info(f"Connecting to Temporal server at {settings.TEMPORAL_HOST}...")
    try:
        client = await Client.connect(settings.TEMPORAL_HOST, namespace="default")
        logger.info(f"Connected to Temporal server. Listening on queue: {settings.TEMPORAL_TASK_QUEUE}")

        worker = Worker(
            client,
            task_queue=settings.TEMPORAL_TASK_QUEUE,
            workflows=[OvernightEmailPrepWorkflow],
            activities=[
                parse_and_store_eml_activity,
                retrieve_style_context_activity,
                classify_and_draft_activity,
            ],
            max_concurrent_activities=2,  # Slow and steady: prevent GPU spikes on local Gemma
        )

        logger.info("Temporal worker running. Press Ctrl+C to stop.")
        await worker.run()

    except Exception:
        logger.exception("Failed to start Temporal worker.")
        logger.info("Note: Ensure Temporal server is running (e.g., via docker compose or 'temporal server start-dev').")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user.")
