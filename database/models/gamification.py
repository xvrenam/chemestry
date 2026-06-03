# database/models/gamification.py
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Date, DECIMAL, CheckConstraint, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.db import Base


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    icon_url = Column(String(255))

    condition_type = Column(String(30))  # streak, count_tasks, count_topics, accuracy, complete_track, collect_items, spend_currency
    condition_data = Column(JSONB, nullable=False)

    xp_reward = Column(Integer, default=0)
    coins_reward = Column(Integer, default=0)
    crystals_reward = Column(Integer, default=0)
    item_reward_id = Column(Integer, ForeignKey("item_types.id"))

    is_hidden = Column(Boolean, default=False)

    item_reward = relationship("ItemType", foreign_keys=[item_reward_id], overlaps="reward_for_achievements")
    user_achievements = relationship("UserAchievement", back_populates="achievement")


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False)
    unlocked_at = Column(DateTime, server_default=func.now())
    shown_to_user = Column(Boolean, default=False)
    is_displayed = Column(Boolean, default=True)

    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="user_achievements")


class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True)
    type = Column(String(20))  # daily, weekly, monthly
    title = Column(String(100), nullable=False)
    description = Column(Text)
    condition_type = Column(String(30))
    condition_data = Column(JSONB)
    reward_coins = Column(Integer, default=0)
    reward_crystals = Column(Integer, default=0)
    xp_bonus = Column(Integer, default=0)
    valid_from = Column(Date)
    valid_until = Column(Date)
    is_active = Column(Boolean, default=True)

    user_challenges = relationship("UserChallenge", back_populates="challenge")


class UserChallenge(Base):
    __tablename__ = "user_challenges"

    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    challenge_id = Column(Integer, ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False)
    progress_current = Column(Integer, default=0)
    progress_target = Column(Integer)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    reward_claimed = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="challenges")
    challenge = relationship("Challenge", back_populates="user_challenges")


class LeaderboardCategory(Base):
    __tablename__ = "leaderboard_categories"

    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    metric_type = Column(String(30))  # xp_daily, xp_weekly, xp_monthly, xp_total, tasks_completed, challenges_completed, accuracy_rate, current_streak, max_streak
    scope = Column(String(20), default='global')  # global, friends
    reset_period = Column(String(20))  # daily, weekly, monthly, never
    is_active = Column(Boolean, default=True)

    entries = relationship("LeaderboardEntry", back_populates="category")


class LeaderboardEntry(Base):
    __tablename__ = "leaderboard_entries"
    __table_args__ = (
        UniqueConstraint("category_id", "user_id", "period_start", name="unique_leaderboard_entry"),
    )

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("leaderboard_categories.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    period_start = Column(Date)
    score = Column(DECIMAL(15,2), nullable=False)
    rank = Column(Integer)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    category = relationship("LeaderboardCategory", back_populates="entries")
    user = relationship("User", back_populates="leaderboard_entries")