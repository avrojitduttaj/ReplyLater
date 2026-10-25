import asyncio
import json
import logging
from typing import List, Dict, Any
from app.db.database import AsyncSessionLocal, init_db
from app.services.vector_service import vector_service
from app.workflows.temporal_workflow import trigger_email_batch_workflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("replylater.seed")

# The 5 realistic scenarios specified for ReplyLater
DEMO_EMAIL_SCENARIOS: List[Dict[str, str]] = [
    {
        "sender": "david.chen@acmeretail.io",
        "subject": "URGENT: App crashing on checkout in production",
        "body": (
            "Hi Alex,\n\n"
            "We are seeing a sudden spike in 500 errors on the checkout payment gateway since 8:00 AM. "
            "Users cannot finalize credit card transactions. App is crashing on checkout, can you investigate today?\n\n"
            "We really need an update or hotfix as soon as possible.\n\n"
            "Thanks,\nDavid Chen\nVP Engineering, AcmeRetail"
        ),
    },
    {
        "sender": "sarah.miller@venturestudio.co",
        "subject": "New React + Python Project - Scope & Availability",
        "body": (
            "Hey Alex,\n\n"
            "We love your work on previous open source tools and would love to partner on our new client dashboard! "
            "Can you send your hourly quote and when you can kick off?\n\n"
            "We have a wireframe ready and are eager to lock in a partner this week.\n\n"
            "Warmly,\nSarah Miller\nFounder & Design Lead"
        ),
    },
    {
        "sender": "digest@dev.to",
        "subject": "DEV Digest: Top posts this week & Hacktoberfest Highlights",
        "body": (
            "Here are the top trending community discussions on DEV this week:\n"
            "1. Slow and Steady: Channel Your Inner Sloth with Python & Temporal\n"
            "2. Running Gemma 2B locally with zero cloud egress\n"
            "3. Vector search benchmarks with pgvector\n\n"
            "Click here to unsubscribe or update notification preferences."
        ),
    },
    {
        "sender": "morgan.blake@techcollaborative.org",
        "subject": "Q4 Roadmap Review sync",
        "body": (
            "Hey Alex,\n\n"
            "We are finalizing team targets for Q4 and need to align on backend milestones. "
            "Can we review the Q4 roadmap on Wednesday at 4 PM?\n\n"
            "Let me know if that time slot works for you and I will send a calendar invite.\n\n"
            "Best,\nMorgan"
        ),
    },
    {
        "sender": "billing@cloudinfra.net",
        "subject": "Your hosting invoice for October has cleared (#INV-2026-884)",
        "body": (
            "Dear Customer,\n\n"
            "Your hosting invoice for October has cleared.\n"
            "Amount Charged: $48.50 USD\n"
            "Payment Method: Visa ending in 4021\n"
            "Status: Paid in full.\n\n"
            "Thank you for choosing CloudInfra. No further action is required."
        ),
    },
]

# Authentic user style samples to seed Tiger Data / pgvector semantic memory
USER_STYLE_SAMPLES: List[str] = [
    (
        "Hi David,\n\n"
        "Thanks for alerting me. I received the report and am investigating the logs right now. "
        "I will keep you posted with a fix and root cause summary before 11:00 AM.\n\n"
        "Best,\nAlex"
    ),
    (
        "Hi Sarah,\n\n"
        "Thanks so much for reaching out! Excited to hear about the project. "
        "My freelance rate is $135/hour and I can start next Monday. "
        "Looking forward to reviewing the wireframes.\n\n"
        "Best regards,\nAlex"
    ),
    (
        "Hi Morgan,\n\n"
        "Wednesday at 4:00 PM works great for me. I'll take a look at the roadmap draft beforehand. "
        "See you then!\n\n"
        "Best,\nAlex"
    ),
]


async def seed_style_memory() -> None:
    """Pre-seed vector memory with user's genuine communication style."""
    async with AsyncSessionLocal() as session:
        for sample_text in USER_STYLE_SAMPLES:
            await vector_service.add_style_sample(session, sample_text)
        logger.info(f"Seeded {len(USER_STYLE_SAMPLES)} style samples into vector memory.")


async def seed_demo_backlog() -> List[Dict[str, Any]]:
    """Ingest the 5 demo email scenarios into the overnight triage pipeline."""
    # Ensure tables exist
    await init_db()

    # Pre-seed style memory if empty
    await seed_style_memory()

    # Convert scenarios to JSON strings for activity ingestion
    raw_items = [json.dumps(scenario) for scenario in DEMO_EMAIL_SCENARIOS]

    logger.info("Executing overnight email prep pipeline for 5 mock scenarios...")
    results = await trigger_email_batch_workflow(raw_items)
    logger.info(f"Seed batch completed with {len(results)} items triaged.")
    return results


if __name__ == "__main__":
    asyncio.run(seed_demo_backlog())
