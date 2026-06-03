# database/models/content.py
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text, ForeignKey, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.db import Base


class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    lessons = relationship("Lesson", back_populates="track", cascade="all, delete-orphan", order_by="Lesson.order_index")
    user_progresses = relationship("UserTrackProgress", back_populates="track")


class Lesson(Base):
    __tablename__ = "lessons"
    __table_args__ = (
        UniqueConstraint("track_id", "order_index", name="unique_lesson_order"),
    )

    id = Column(Integer, primary_key=True)
    track_id = Column(Integer, ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False)
    order_index = Column(Integer, nullable=False)

    track = relationship("Track", back_populates="lessons")
    versions = relationship("LessonVersion", back_populates="lesson", cascade="all, delete-orphan")
    theory_links = relationship("LessonTheory", back_populates="lesson", cascade="all, delete-orphan")
    task_links = relationship("LessonTask", back_populates="lesson", cascade="all, delete-orphan")
    user_progresses = relationship("UserLessonProgress", back_populates="lesson")


class LessonVersion(Base):
    __tablename__ = "lesson_versions"

    id = Column(Integer, primary_key=True)
    version_of = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    title = Column(String(200), nullable=False)
    estimated_time = Column(Integer)  # в минутах
    xp_reward = Column(Integer, default=10)
    version_number = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())
    is_active = Column(Boolean, default=True)
    replaced_by = Column(Integer, ForeignKey("lesson_versions.id"))

    lesson = relationship("Lesson", back_populates="versions")
    replaced_by_version = relationship("LessonVersion", remote_side=[id])
    user_progresses = relationship("UserLessonProgress", back_populates="version")


class Theory(Base):
    __tablename__ = "theory"

    id = Column(Integer, primary_key=True)
    data = Column(JSONB, nullable=False)  # структура теории (текст, изображения, анимации)
    topic_tags = Column(ARRAY(Text))
    estimated_time = Column(Integer)  # минут на чтение

    lesson_links = relationship("LessonTheory", back_populates="theory")


class LessonTheory(Base):
    __tablename__ = "lesson_theory"
    __table_args__ = (
        UniqueConstraint("lesson_id", "theory_id", "order_index", name="unique_lesson_theory_order"),
    )

    id = Column(Integer, primary_key=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    theory_id = Column(Integer, ForeignKey("theory.id", ondelete="CASCADE"), nullable=False)
    order_index = Column(Integer, nullable=False)
    is_required = Column(Boolean, default=True)

    lesson = relationship("Lesson", back_populates="theory_links")
    theory = relationship("Theory", back_populates="lesson_links")


class TaskGenerator(Base):
    __tablename__ = "task_generators"

    id = Column(Integer, primary_key=True)
    type = Column(String(30), nullable=False)  # напр. 'balance_equation', 'calculation'
    template_data = Column(JSONB, nullable=False)  # шаблон для генерации
    difficulty = Column(Integer, CheckConstraint("difficulty BETWEEN 1 AND 5"))
    topic_tags = Column(ARRAY(Text))
    created_at = Column(DateTime, server_default=func.now())

    tasks = relationship("Task", back_populates="generator")


class TaskPool(Base):
    __tablename__ = "task_pools"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    topic_tags = Column(ARRAY(Text))
    difficulty = Column(Integer, CheckConstraint("difficulty BETWEEN 1 AND 5"))

    tasks = relationship("Task", back_populates="pool")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    type = Column(String(20), nullable=False)  # match, choice, true_false, fill_blank, balance_equation, predict_product, classify, calculation, chain_transform, virtual_lab, find_error, open_experiment, puzzle, timed
    source_type = Column(String(20))  # generated, static, manual
    generator_id = Column(Integer, ForeignKey("task_generators.id"))
    pool_id = Column(Integer, ForeignKey("task_pools.id"))

    question_text = Column(Text, nullable=False)
    data = Column(JSONB, nullable=False)  # данные для рендеринга задания

    correct_answers = Column(JSONB, nullable=False)
    scoring_type = Column(String(20), default='binary')  # binary, partial, proportional
    max_score = Column(Integer, default=1)

    hints = Column(ARRAY(JSONB))  # массив JSONB объектов с подсказками
    max_hints_available = Column(Integer, default=3)

    difficulty = Column(Integer, CheckConstraint("difficulty BETWEEN 1 AND 5"))
    topic_tags = Column(ARRAY(Text))
    estimated_time = Column(Integer)  # секунд на выполнение

    created_at = Column(DateTime, server_default=func.now())

    generator = relationship("TaskGenerator", back_populates="tasks")
    pool = relationship("TaskPool", back_populates="tasks")
    variants = relationship("TaskVariant", back_populates="base_task", cascade="all, delete-orphan")
    lesson_links = relationship("LessonTask", back_populates="task")
    attempts = relationship("TaskAttempt", back_populates="task")


class TaskVariant(Base):
    __tablename__ = "task_variants"

    id = Column(Integer, primary_key=True)
    base_task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    variant_data = Column(JSONB, nullable=False)  # конкретные значения для варианта
    correct_answer = Column(JSONB, nullable=False)
    usage_count = Column(Integer, default=0)

    base_task = relationship("Task", back_populates="variants")
    attempts = relationship("TaskAttempt", back_populates="variant")


class LessonTask(Base):
    __tablename__ = "lesson_tasks"
    __table_args__ = (
        UniqueConstraint("lesson_id", "task_id", "order_index", name="unique_lesson_task_order"),
    )

    id = Column(Integer, primary_key=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    order_index = Column(Integer, nullable=False)
    is_required = Column(Boolean, default=True)

    lesson = relationship("Lesson", back_populates="task_links")
    task = relationship("Task", back_populates="lesson_links")