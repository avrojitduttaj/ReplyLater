import unittest
from unittest.mock import patch

from app.core.sentry import trace_llm_span


class RecordingSpan:
    def __init__(self):
        self.data = {}
        self.status = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def set_data(self, key, value):
        self.data[key] = value

    def set_status(self, status):
        self.status = status


class SentryPrivacyTests(unittest.TestCase):
    @patch("app.core.sentry.sentry_sdk.start_span")
    def test_span_records_metrics_without_prompt_or_output_text(self, start_span):
        span = RecordingSpan()
        start_span.return_value = span
        prompt = "PRIVATE incoming email content"
        output = "PRIVATE generated draft"

        with trace_llm_span("draft", prompt=prompt) as context:
            context.set_output(output)

        self.assertNotIn("gen_ai.prompt_preview", span.data)
        self.assertNotIn("gen_ai.output_preview", span.data)
        self.assertEqual(span.data["gen_ai.prompt_chars"], len(prompt))
        self.assertEqual(span.data["gen_ai.output_chars"], len(output))
        self.assertNotIn(prompt, repr(span.data))
        self.assertNotIn(output, repr(span.data))

    @patch("app.core.sentry.sentry_sdk.capture_message")
    @patch("app.core.sentry.sentry_sdk.start_span")
    def test_failure_reports_only_error_type_and_step(self, start_span, capture_message):
        span = RecordingSpan()
        start_span.return_value = span

        with self.assertRaisesRegex(RuntimeError, "PRIVATE incoming email"):
            with trace_llm_span("triage", prompt="PRIVATE incoming email"):
                raise RuntimeError("PRIVATE incoming email")

        self.assertEqual(span.data["error.type"], "RuntimeError")
        self.assertNotIn("error.message", span.data)
        capture_message.assert_called_once_with(
            "LLM step failed during triage (RuntimeError)",
            level="error",
        )


if __name__ == "__main__":
    unittest.main()
