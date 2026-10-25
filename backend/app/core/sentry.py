import time
import logging
from contextlib import contextmanager
from typing import Optional, Generator, Any
import sentry_sdk
from app.core.config import settings

logger = logging.getLogger("replylater.sentry")


def init_sentry() -> None:
    """Initialize Sentry SDK with AI Agent Tracing enabled."""
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.SENTRY_ENVIRONMENT,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            send_default_pii=False,
            _experiments={
                "enable_ai_agent_tracing": True,
            },
        )
        logger.info("Sentry initialized with AI Agent Tracing enabled.")
    else:
        logger.info("Sentry DSN not provided; running in local telemetry logging mode.")


class LLMSpanContext:
    def __init__(self, step_name: str, model_name: str, prompt: str):
        self.step_name = step_name
        self.model_name = model_name
        self.prompt = prompt
        self.tokens_in: int = len(prompt.split()) if prompt else 0
        self.tokens_out: int = 0
        self.duration_ms: float = 0.0
        self.output: Optional[str] = None
        self.span: Any = None
        self._start_time: float = 0.0

    def set_tokens(self, tokens_in: Optional[int] = None, tokens_out: Optional[int] = None) -> None:
        if tokens_in is not None:
            self.tokens_in = tokens_in
        if tokens_out is not None:
            self.tokens_out = tokens_out

    def set_output(self, output: str) -> None:
        self.output = output
        if not self.tokens_out and output:
            self.tokens_out = len(output.split())


@contextmanager
def trace_llm_span(
    step_name: str,
    model_name: str = "gemma2:2b",
    prompt: str = "",
    tokens_in: Optional[int] = None,
    tokens_out: Optional[int] = None,
) -> Generator[LLMSpanContext, None, None]:
    """Context manager for tracing LLM execution spans via Sentry AI Agent telemetry.
    
    Records prompt spans, token counts, and latency cleanly using sentry_sdk.start_span(op="gen_ai.gemma").
    """
    ctx = LLMSpanContext(step_name=step_name, model_name=model_name, prompt=prompt)
    if tokens_in is not None:
        ctx.tokens_in = tokens_in
    if tokens_out is not None:
        ctx.tokens_out = tokens_out

    ctx._start_time = time.perf_counter()

    try:
        # sentry_sdk.start_span returns a span or null context if not initialized
        with sentry_sdk.start_span(op="gen_ai.gemma", name=f"Gemma: {step_name}") as span:
            ctx.span = span
            if span:
                span.set_data("gen_ai.system", "ollama")
                span.set_data("gen_ai.model", model_name)
                span.set_data("gen_ai.prompt_chars", len(prompt))
                span.set_data("gen_ai.step", step_name)

            yield ctx

            # After execution, compute duration and record token metrics
            ctx.duration_ms = (time.perf_counter() - ctx._start_time) * 1000.0

            if span:
                span.set_data("gen_ai.tokens.prompt", ctx.tokens_in)
                span.set_data("gen_ai.tokens.completion", ctx.tokens_out)
                span.set_data("gen_ai.tokens.total", ctx.tokens_in + ctx.tokens_out)
                span.set_data("gen_ai.duration_ms", round(ctx.duration_ms, 2))
                if ctx.output:
                    span.set_data("gen_ai.output_chars", len(ctx.output))
    except Exception as exc:
        ctx.duration_ms = (time.perf_counter() - ctx._start_time) * 1000.0
        if ctx.span:
            ctx.span.set_status("internal_error")
            ctx.span.set_data("error.type", type(exc).__name__)
        sentry_sdk.capture_message(
            f"LLM step failed during {step_name} ({type(exc).__name__})",
            level="error",
        )
        logger.error(f"Error in LLM span [{step_name}]: {exc}")
        raise
    finally:
        logger.debug(
            f"[Sentry Span: {step_name}] Model={model_name} in={ctx.tokens_in} out={ctx.tokens_out} latency={ctx.duration_ms:.1f}ms"
        )
