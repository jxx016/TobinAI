"""CRM tables shared by tools, the API, and nightly reflection."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    email: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(64), default="")
    company: Mapped[str] = mapped_column(String(255), default="")
    role: Mapped[str] = mapped_column(String(255), default="")
    source: Mapped[str] = mapped_column(String(255), default="")
    industry: Mapped[str] = mapped_column(String(255), default="")
    stage: Mapped[str] = mapped_column(String(32), default="NEW", index=True)
    enrichment_notes: Mapped[str] = mapped_column(Text, default="")
    profile_json: Mapped[str] = mapped_column(Text, default="{}")
    touchpoint_count: Mapped[int] = mapped_column(Integer, default=0)
    last_angle_used: Mapped[str] = mapped_column(String(64), default="")
    next_follow_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    outcome_label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Touchpoint(Base):
    __tablename__ = "touchpoints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[str] = mapped_column(ForeignKey("leads.id"), index=True)
    channel: Mapped[str] = mapped_column(String(32), default="system")
    direction: Mapped[str] = mapped_column(String(16), default="outbound")
    body: Mapped[str] = mapped_column(Text, default="")
    angle: Mapped[str] = mapped_column(String(64), default="")
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ScheduledJob(Base):
    __tablename__ = "scheduled_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[str] = mapped_column(ForeignKey("leads.id"), index=True)
    run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    kind: Mapped[str] = mapped_column(String(32), default="follow_up")
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ReflectionLog(Base):
    __tablename__ = "reflection_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    summary: Mapped[str] = mapped_column(Text, default="")
    report_json: Mapped[str] = mapped_column(Text, default="{}")
    playbook_diff: Mapped[str] = mapped_column(Text, default="")
