from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ResearchQuery(Base):
    __tablename__ = "research_queries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="research_queries", lazy="selectin")
    tasks = relationship("ResearchTask", back_populates="query", cascade="all, delete-orphan", lazy="selectin")
    sources = relationship("ResearchSource", back_populates="query", cascade="all, delete-orphan", lazy="selectin")
    report = relationship(
        "ResearchReport",
        back_populates="query",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    metrics = relationship(
        "ExecutionMetric",
        back_populates="query",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ResearchTask(Base):
    __tablename__ = "research_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    query_id: Mapped[str] = mapped_column(ForeignKey("research_queries.id", ondelete="CASCADE"), index=True)
    task_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    execution_logs: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    query = relationship("ResearchQuery", back_populates="tasks", lazy="selectin")


class ResearchSource(Base):
    __tablename__ = "research_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    query_id: Mapped[str] = mapped_column(ForeignKey("research_queries.id", ondelete="CASCADE"), index=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    extracted_content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)

    query = relationship("ResearchQuery", back_populates="sources", lazy="selectin")


class ResearchReport(Base):
    __tablename__ = "research_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    query_id: Mapped[str] = mapped_column(
        ForeignKey("research_queries.id", ondelete="CASCADE"), unique=True, index=True
    )
    report_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    generated_summary: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    query = relationship("ResearchQuery", back_populates="report", lazy="selectin")


class ExecutionMetric(Base):
    __tablename__ = "execution_metrics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    query_id: Mapped[str] = mapped_column(
        ForeignKey("research_queries.id", ondelete="CASCADE"), unique=True, index=True
    )
    execution_time: Mapped[float] = mapped_column(Float, default=0.0)
    token_usage: Mapped[int] = mapped_column(Integer, default=0)
    retrieval_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    query = relationship("ResearchQuery", back_populates="metrics", lazy="selectin")
