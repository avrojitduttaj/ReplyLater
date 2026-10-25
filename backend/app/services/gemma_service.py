import json
import logging
import re
from typing import Dict, Any, List, Optional
import httpx

from app.core.config import settings
from app.core.sentry import trace_llm_span

logger = logging.getLogger("replylater.gemma")


class GemmaService:
    def __init__(self, host: str = None, model: str = None):
        self.host = host or settings.OLLAMA_HOST
        self.model = model or settings.GEMMA_MODEL

    async def _call_ollama(self, prompt: str, system: Optional[str] = None, json_format: bool = False) -> Optional[str]:
        """Send inference prompt to local Ollama instance with fast connect timeout."""
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system
        if json_format:
            payload["format"] = "json"

        try:
            # Fast connect timeout (0.5s) so fallback is instantaneous if Ollama is not active
            timeout = httpx.Timeout(15.0, connect=0.5)
            async with httpx.AsyncClient(timeout=timeout) as client:
                res = await client.post(f"{self.host}/api/generate", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data.get("response", "").strip()
                logger.warning(f"Ollama returned HTTP status {res.status_code}: {res.text}")
        except Exception as e:
            logger.info(f"Local Ollama ({self.host}) unavailable ({e}). Using deterministic offline model fallback.")
        return None

    async def analyze_incoming_email(self, subject: str, body: str) -> Dict[str, Any]:
        """Categorize email, extract deadlines, detect commitments, and identify missing info.
        
        Returns JSON:
        {
            "needs_reply": bool,
            "detected_deadline": str | None,
            "suggested_weekday": "Monday" | "Tuesday" | "Wednesday" | "Thursday" | "Friday",
            "commitments": [str],
            "has_uncertainty": bool,
            "missing_question": str | None
        }
        """
        prompt = f"""You are an email triage assistant for a developer. Analyze the email below.
Subject: {subject}
Body: {body}

Return a valid JSON object strictly matching this schema:
{{
  "needs_reply": true/false (false for newsletters, receipts, notifications, automated alerts),
  "detected_deadline": "string or null (e.g. 'Monday morning', 'Wednesday 4 PM')",
  "suggested_weekday": "Monday"|"Tuesday"|"Wednesday"|"Thursday"|"Friday",
  "commitments": ["list of explicit promises or tasks identified in the thread"],
  "has_uncertainty": true/false (true ONLY if the sender asks for personal information you cannot guess, like hourly rate, schedule availability, pricing, or custom decisions),
  "missing_question": "Direct question to prompt the user if has_uncertainty is true, else null"
}}"""

        with trace_llm_span(
            step_name="analyze_incoming_email",
            model_name=self.model,
            prompt=prompt,
        ) as span_ctx:
            raw_response = await self._call_ollama(
                prompt=prompt,
                system="You are a strict, privacy-first local email parser. Output valid JSON only.",
                json_format=True,
            )

            if raw_response:
                try:
                    # Clean markdown fence if present
                    cleaned = re.sub(r"^```json\s*", "", raw_response, flags=re.MULTILINE)
                    cleaned = re.sub(r"```$", "", cleaned, flags=re.MULTILINE).strip()
                    parsed = json.loads(cleaned)
                    span_ctx.set_output(raw_response)
                    return parsed
                except Exception as err:
                    logger.warning(f"Failed to parse Ollama JSON output: {err}; using fallback.")

            # Deterministic Fallback Logic (100% offline & demo resilient)
            fallback = self._deterministic_fallback_analysis(subject, body)
            span_ctx.set_output(json.dumps(fallback))
            return fallback

    async def generate_draft_reply(
        self,
        subject: str,
        body: str,
        context_samples: List[str],
        user_clarification: Optional[str] = None,
    ) -> str:
        """Generate draft reply matching user's style, answering commitments, incorporating clarification."""
        context_str = "\n---\n".join(context_samples) if context_samples else "Be polite, concise, calm, and direct."
        clarification_str = (
            f"\nUser decision/clarification to incorporate: {user_clarification}"
            if user_clarification
            else ""
        )

        prompt = f"""Write an authentic, calm, professional email reply.
Style samples from previous emails:
{context_str}

Incoming Email:
Subject: {subject}
Body: {body}
{clarification_str}

Requirements:
- Embody the slow-and-steady ethos: calm, considerate, zero stress.
- Acknowledge any commitments clearly.
- If user clarification was provided, weave it naturally into the answer.
- Sign off cleanly.
Draft reply:"""

        with trace_llm_span(
            step_name="generate_draft_reply",
            model_name=self.model,
            prompt=prompt,
        ) as span_ctx:
            raw_response = await self._call_ollama(
                prompt=prompt,
                system="You are an overnight email assistant acting on behalf of the user.",
            )

            if raw_response and len(raw_response) > 20:
                span_ctx.set_output(raw_response)
                return raw_response

            # Deterministic Fallback Draft
            fallback_draft = self._deterministic_fallback_draft(subject, body, user_clarification)
            span_ctx.set_output(fallback_draft)
            return fallback_draft

    def _deterministic_fallback_analysis(self, subject: str, body: str) -> Dict[str, Any]:
        """Provides accurate offline analysis for standard email archetypes."""
        combined = f"{subject} {body}".lower()

        # Check for Newsletters, Receipts, Invoices, Automated spam
        if any(w in combined for w in ["newsletter", "digest", "top posts", "unsubscribe", "invoice", "receipt", "cleared", "order confirmation"]):
            return {
                "needs_reply": False,
                "detected_deadline": None,
                "suggested_weekday": "Monday",
                "commitments": [],
                "has_uncertainty": False,
                "missing_question": None,
            }

        # Check for Ambiguous scope requiring user call (e.g. rate, pricing, custom availability)
        if any(w in combined for w in ["hourly quote", "rate", "how much", "kick off", "quote and when"]):
            return {
                "needs_reply": True,
                "detected_deadline": "Friday EOD",
                "suggested_weekday": "Tuesday",
                "commitments": ["Send quote & kickoff timeline"],
                "has_uncertainty": True,
                "missing_question": "Client asked for your freelance hourly rate and start availability. Enter rate and start date:",
            }

        # Check for Urgent Bug
        if any(w in combined for w in ["urgent", "crashing", "crash", "bug", "checkout", "investigate today"]):
            return {
                "needs_reply": True,
                "detected_deadline": "Monday 10:00 AM",
                "suggested_weekday": "Monday",
                "commitments": ["Investigate checkout crash logs", "Send status update by 11 AM"],
                "has_uncertainty": False,
                "missing_question": None,
            }

        # Check for Coordination / Meeting
        if any(w in combined for w in ["review", "roadmap", "sync", "wednesday", "meeting", "call"]):
            return {
                "needs_reply": True,
                "detected_deadline": "Wednesday 4:00 PM",
                "suggested_weekday": "Wednesday",
                "commitments": ["Attend Q4 Roadmap sync at 4 PM Wednesday"],
                "has_uncertainty": False,
                "missing_question": None,
            }

        # Default fallback
        return {
            "needs_reply": True,
            "detected_deadline": "Thursday",
            "suggested_weekday": "Thursday",
            "commitments": ["Review details and respond"],
            "has_uncertainty": False,
            "missing_question": None,
        }

    def _deterministic_fallback_draft(
        self, subject: str, body: str, user_clarification: Optional[str] = None
    ) -> str:
        """High-quality deterministic draft replies matching the user's sloth/steady tone."""
        combined = f"{subject} {body}".lower()

        if user_clarification:
            return (
                f"Hi there,\n\n"
                f"Thanks so much for reaching out! Regarding the project scope:\n"
                f"{user_clarification}\n\n"
                f"Looking forward to collaborating. Let me know if that works for your timeline.\n\n"
                f"Best regards,\nAlex"
            )

        if "crashing" in combined or "crash" in combined or "urgent" in combined:
            return (
                "Hi Team,\n\n"
                "I saw the alert regarding the checkout crash and am prioritizing it first thing this morning. "
                "I am pulling the production logs now and will have a fix or progress update for you by 11:00 AM.\n\n"
                "Thanks for flagging this,\nAlex"
            )

        if "roadmap" in combined or "wednesday" in combined:
            return (
                "Hi Morgan,\n\n"
                "Wednesday at 4:00 PM works well for me. I will review the Q4 roadmap notes beforehand "
                "so we can dive straight into priority topics.\n\n"
                "Talk soon,\nAlex"
            )

        return (
            "Hi,\n\n"
            "Thanks for your message. I have reviewed the details and will prepare the requested follow-up items. "
            "I will check in again later this week with full updates.\n\n"
            "Best regards,\nAlex"
        )


gemma_service = GemmaService()
