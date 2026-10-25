import uuid
import json
from datetime import datetime, timezone
import enum
from typing import List, Optional
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    ForeignKey,
    Enum as SqlEnum,
    JSON,
    TypeDecorator,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import relationship
from app.db.database import Base, is_sqlite

try:
    from pgvector.sqlalchemy import Vector as PgVector
except ImportError:
    PgVector = None


class CompatibleVector(TypeDecorator):
    """Custom type to support pgvector Vector on PostgreSQL and JSON representation on SQLite."""
    impl = Text
    cache_ok = True

    def __init__(self, dim=384, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dim = dim

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and PgVector is not None:
            return dialect.type_descriptor(PgVector(self.dim))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql" and PgVector is not None:
            return value
        # SQLite: serialize list of floats to JSON string
        if isinstance(value, (list, tuple)):
            return json.dumps(list(value))
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql" and PgVector is not None:
            return value
        # SQLite: deserialize from JSON string to list of floats
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return []
        return value


class ThreadStatus(str, enum.Enum):
    PENDING = "PENDING"
    NEEDS_INPUT = "NEEDS_INPUT"
    SCHEDULED = "SCHEDULED"
    ARCHIVED = "ARCHIVED"


class DraftStatus(str, enum.Enum):
    NEEDS_INPUT = "NEEDS_INPUT"
    SCHEDULED = "SCHEDULED"
    APPROVED = "APPROVED"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Thread(Base):
    __tablename__ = "threads"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sender = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    raw_body = Column(Text, nullable=False)
    received_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    status = Column(SqlEnum(ThreadStatus), default=ThreadStatus.PENDING, nullable=False)

    # Relationships
    drafts = relationship("Draft", back_populates="thread", cascade="all, delete-orphan", lazy="selectin")

    def to_dict(self):
        return {
            "id": self.id,
            "sender": self.sender,
            "subject": self.subject,
            "raw_body": self.raw_body,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "status": self.status.value if isinstance(self.status, ThreadStatus) else self.status,
        }


class StyleSample(Base):
    __tablename__ = "style_samples"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    body = Column(Text, nullable=False)
    embedding = Column(CompatibleVector(384), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "body": self.body,
        }


class Draft(Base):
    __tablename__ = "drafts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    thread_id = Column(String(36), ForeignKey("threads.id", ondelete="CASCADE"), nullable=False)
    status = Column(SqlEnum(DraftStatus), default=DraftStatus.NEEDS_INPUT, nullable=False)
    suggested_weekday = Column(String(32), default="Monday", nullable=False)
    detected_deadline = Column(String(255), nullable=True)
    commitments_found = Column(JSON, default=list, nullable=False)
    missing_info_question = Column(String(500), nullable=True)
    user_clarification = Column(Text, nullable=True)
    proposed_reply = Column(Text, default="", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    thread = relationship("Thread", back_populates="drafts", lazy="selectin")

    def to_dict(self):
        return {
            "id": self.id,
            "thread_id": self.thread_id,
            "status": self.status.value if isinstance(self.status, DraftStatus) else self.status,
            "suggested_weekday": self.suggested_weekday,
            "detected_deadline": self.detected_deadline,
            "commitments_found": self.commitments_found or [],
            "missing_info_question": self.missing_info_question,
            "user_clarification": self.user_clarification,
            "proposed_reply": self.proposed_reply,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "thread": self.thread.to_dict() if self.thread else None,
        }
