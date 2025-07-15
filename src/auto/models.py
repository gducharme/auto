from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, text

from .db import Base

class Post(Base):
    __tablename__ = "posts"

    id = Column(String, primary_key=True, nullable=False)
    title = Column(String, nullable=False)
    link = Column(String, nullable=False)
    summary = Column(Text)
    published = Column(String)

class PostStatus(Base):
    __tablename__ = "post_status"

    post_id = Column(String, ForeignKey("posts.id"), primary_key=True)
    network = Column(String, primary_key=True)
    scheduled_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    status = Column(String, nullable=False, server_default="pending")
    attempts = Column(Integer, nullable=False, server_default="0")
    last_error = Column(Text)
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
