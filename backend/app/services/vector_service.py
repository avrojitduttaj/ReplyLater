import math
import hashlib
import logging
from typing import List, Optional
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import StyleSample
from app.db.database import is_sqlite

logger = logging.getLogger("replylater.vector")


def _deterministic_mock_embedding(text: str, dim: int = 384) -> List[float]:
    """Generate a deterministic 384-d normalized vector representation for text offline."""
    vec = [0.0] * dim
    words = text.lower().split()
    if not words:
        words = ["empty"]

    for word in words:
        # Hash each token to multiple dimensions with pseudo-random weights
        h = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
        for offset in range(3):
            idx = (h + offset * 127) % dim
            sign = 1.0 if ((h >> offset) & 1) else -1.0
            vec[idx] += sign * (1.0 / math.sqrt(len(word) + 1.0))

    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    if not vec_a or not vec_b:
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class VectorService:
    @staticmethod
    async def get_embedding(text: str) -> List[float]:
        """Fetch 384-dim embedding from Ollama or compute deterministic fallback vector."""
        # 1. Try Ollama if reachable with fast connect timeout
        try:
            timeout = httpx.Timeout(5.0, connect=0.2)
            async with httpx.AsyncClient(timeout=timeout) as client:
                res = await client.post(
                    f"{settings.OLLAMA_HOST}/api/embeddings",
                    json={"model": settings.GEMMA_MODEL, "prompt": text[:512]},
                )
                if res.status_code == 200:
                    data = res.json()
                    embedding = data.get("embedding", [])
                    if embedding:
                        # Normalize or truncate/pad to 384 if needed
                        if len(embedding) > 384:
                            embedding = embedding[:384]
                        elif len(embedding) < 384:
                            embedding = embedding + [0.0] * (384 - len(embedding))
                        norm = math.sqrt(sum(x * x for x in embedding))
                        if norm > 0:
                            return [x / norm for x in embedding]
                        return embedding
        except Exception:
            pass

        # 2. Deterministic local embedding (Zero cloud egress & 100% offline resilient)
        return _deterministic_mock_embedding(text, dim=384)

    @classmethod
    async def add_style_sample(cls, session: AsyncSession, body: str) -> StyleSample:
        """Embed and persist a writing style sample to the database."""
        emb = await cls.get_embedding(body)
        sample = StyleSample(body=body, embedding=emb)
        session.add(sample)
        await session.commit()
        await session.refresh(sample)
        return sample

    @classmethod
    async def retrieve_style_context(cls, session: AsyncSession, query_text: str, top_k: int = 2) -> List[str]:
        """Retrieve top-k user style samples semantically closest to the incoming email."""
        query_emb = await cls.get_embedding(query_text)

        result = await session.execute(select(StyleSample))
        all_samples = result.scalars().all()

        if not all_samples:
            return []

        # Calculate cosine similarities
        scored = []
        for s in all_samples:
            sample_emb = s.embedding
            if isinstance(sample_emb, list) and len(sample_emb) > 0:
                score = _cosine_similarity(query_emb, sample_emb)
                scored.append((score, s.body))
            else:
                scored.append((0.0, s.body))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [text for _, text in scored[:top_k]]


vector_service = VectorService()
