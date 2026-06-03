# database/models/progress.py
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, ForeignKey, UniqueConstraint, Text, DECIMAL
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.db import Base


class UserTrackProgress(Base):
    __tablename__ = "user_track_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "track_id", name="unique_user_track"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    track_id = Column(Integer, ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), default='active')  # active, completed, paused, repeating
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)
    is_repeating = Column(Boolean, default=False)
    total_xp = Column(Integer, default=0)
    current_lesson_index = Column(Integer, default=0)

    user = relationship("User", back_populates="track_progresses")
    track = relationship("Track", back_populates="user_progresses")
    lesson_progresses = relationship("UserLessonProgress", back_populates="track_progress", cascade="all, delete-orphan")


class UserLessonProgress(Base):
    __tablename__ = "user_lesson_progress"
    __table_args__ = (
        UniqueConstraint("user_track_progress_id", "lesson_id", name="unique_user_lesson"),
    )

    id = Column(Integer, primary_key=True)
    user_track_progress_id = Column(Integer, ForeignKey("user_track_progress.id", ondelete="CASCADE"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    version_id = Column(Integer, ForeignKey("lesson_versions.id"))
    status = Column(String(20), default='locked')  # locked, available, in_progress, completed, skipped

    theory_viewed = Column(Boolean, default=False)
    theory_viewed_at = Column(DateTime)

    tasks_completed = Column(Integer, default=0)
    tasks_total = Column(Integer, default=0)
    score_earned = Column(Integer, default=0)
    score_total = Column(Integer, default=0)

    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    is_skipped = Column(Boolean, default=False)

    track_progress = relationship("UserTrackProgress", back_populates="lesson_progresses")
    lesson = relationship("Lesson", back_populates="user_progresses")
    version = relationship("LessonVersion", back_populates="user_progresses")
    task_attempts = relationship("TaskAttempt", back_populates="lesson_progress")


class TaskAttempt(Base):
    __tablename__ = "task_attempts"

    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    variant_id = Column(Integer, ForeignKey("task_variants.id"))

    user_answer = Column(JSONB, nullable=False)
    is_correct = Column(Boolean)
    score_earned = Column(Integer)
    score_max = Column(Integer)

    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    time_spent = Column(Integer)  # в секундах

    hints_used = Column(Integer, default=0)
    hints_cost = Column(Integer, default=0)

    lesson_progress_id = Column(Integer, ForeignKey("user_lesson_progress.id"))
    attempt_number = Column(Integer)

    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="task_attempts")
    task = relationship("Task", back_populates="attempts")
    variant = relationship("TaskVariant", back_populates="attempts")
    lesson_progress = relationship("UserLessonProgress", back_populates="task_attempts")


class UserTopicStats(Base):
    __tablename__ = "user_topic_stats"
    __table_args__ = (
        UniqueConstraint("user_id", "topic_tag", name="unique_user_topic"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic_tag = Column(String(50), nullable=False)

    total_attempts = Column(Integer, default=0)
    correct_attempts = Column(Integer, default=0)

    accuracy_rate = Column(DECIMAL(5,2))

    stats_by_task_type = Column(JSONB, default={})

    current_streak = Column(Integer, default=0)
    max_streak = Column(Integer, default=0)

    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="topic_stats")