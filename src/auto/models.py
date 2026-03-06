from datetime import datetime, timezone

from .db import Base

from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    DateTime,
    Float,
    ForeignKey,
    UniqueConstraint,
    text,
)

from sqlalchemy.types import TypeDecorator


class TZDateTime(TypeDecorator):
    """A timezone-aware DateTime that normalizes to UTC."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class Post(Base):
    __tablename__ = "posts"

    id = Column(String, primary_key=True, nullable=False)
    title = Column(String, nullable=False)
    link = Column(String, nullable=False)
    summary = Column(Text)
    content = Column(Text)
    published = Column(String)
    created_at = Column(
        TZDateTime(),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at = Column(
        TZDateTime(),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class PostStatus(Base):
    __tablename__ = "post_status"

    post_id = Column(String, ForeignKey("posts.id"), primary_key=True)
    network = Column(String, primary_key=True)
    scheduled_at = Column(
        TZDateTime(),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    status = Column(String, nullable=False, server_default="pending")
    attempts = Column(Integer, nullable=False, server_default="0")
    last_error = Column(Text)
    updated_at = Column(
        TZDateTime(),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class PostPreview(Base):
    __tablename__ = "post_previews"

    post_id = Column(String, ForeignKey("posts.id"), primary_key=True)
    network = Column(String, primary_key=True)
    content = Column(Text, nullable=False)
    updated_at = Column(
        TZDateTime(),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String, nullable=False)
    payload = Column(Text)
    scheduled_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    status = Column(String, nullable=False, server_default="pending")
    attempts = Column(Integer, nullable=False, server_default="0")
    last_error = Column(Text)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class InstagramPipelineRun(Base):
    __tablename__ = "instagram_pipeline_runs"
    __table_args__ = (
        UniqueConstraint(
            "post_id",
            "network",
            "pipeline_version",
            name="uq_instagram_pipeline_run_key",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(String, ForeignKey("posts.id"), nullable=False)
    network = Column(String, nullable=False, server_default="instagram")
    pipeline_version = Column(String, nullable=False)
    status = Column(String, nullable=False, server_default="pending")
    selected_concept_id = Column(Integer, nullable=True)
    score_summary = Column(Text)
    publish_payload = Column(Text)
    published_at = Column(TZDateTime(), nullable=True)
    last_error = Column(Text)
    created_at = Column(
        TZDateTime(),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at = Column(
        TZDateTime(),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class InstagramPipelineConcept(Base):
    __tablename__ = "instagram_pipeline_concepts"
    __table_args__ = (
        UniqueConstraint(
            "run_id",
            "concept_key",
            name="uq_instagram_pipeline_concept_key",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(
        Integer,
        ForeignKey("instagram_pipeline_runs.id"),
        nullable=False,
    )
    concept_key = Column(String, nullable=False)
    concept_payload = Column(Text, nullable=False)
    score_total = Column(Float, nullable=True)
    score_breakdown = Column(Text)
    rank = Column(Integer, nullable=True)
    created_at = Column(
        TZDateTime(),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at = Column(
        TZDateTime(),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class InstagramPipelineAsset(Base):
    __tablename__ = "instagram_pipeline_assets"
    __table_args__ = (
        UniqueConstraint(
            "run_id",
            "asset_key",
            name="uq_instagram_pipeline_asset_key",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(
        Integer,
        ForeignKey("instagram_pipeline_runs.id"),
        nullable=False,
    )
    concept_id = Column(
        Integer,
        ForeignKey("instagram_pipeline_concepts.id"),
        nullable=True,
    )
    asset_key = Column(String, nullable=False)
    asset_type = Column(String, nullable=False)
    asset_uri = Column(Text, nullable=True)
    asset_metadata = Column(Text)
    status = Column(String, nullable=False, server_default="pending")
    created_at = Column(
        TZDateTime(),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at = Column(
        TZDateTime(),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=lambda: datetime.now(timezone.utc),
    )
