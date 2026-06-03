# database/models/user.py
import uuid
from sqlalchemy import (
    Column, Integer, String, DateTime, Date, Boolean, ForeignKey, CheckConstraint, UniqueConstraint, Text
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(32), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    avatar_url = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    last_active = Column(DateTime)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_login_date = Column(Date)

    # Relationships
    friendships_initiated = relationship("Friendship", foreign_keys="Friendship.requester_id", back_populates="requester")
    friendships_received = relationship("Friendship", foreign_keys="Friendship.addressee_id", back_populates="addressee")
    currencies = relationship("UserCurrency", back_populates="user", uselist=False, cascade="all, delete-orphan")
    inventory = relationship("UserInventory", back_populates="user", cascade="all, delete-orphan")
    showcases = relationship("UserShowcase", back_populates="user", cascade="all, delete-orphan")
    track_progresses = relationship("UserTrackProgress", back_populates="user", cascade="all, delete-orphan")
    task_attempts = relationship("TaskAttempt", back_populates="user", cascade="all, delete-orphan")
    topic_stats = relationship("UserTopicStats", back_populates="user", cascade="all, delete-orphan")
    achievements = relationship("UserAchievement", back_populates="user", cascade="all, delete-orphan")
    challenges = relationship("UserChallenge", back_populates="user", cascade="all, delete-orphan")
    leaderboard_entries = relationship("LeaderboardEntry", back_populates="user", cascade="all, delete-orphan")


class Friendship(Base):
    __tablename__ = "friendships"
    __table_args__ = (
        CheckConstraint("requester_id <> addressee_id", name="check_self_friend"),
        UniqueConstraint("requester_id", "addressee_id", name="unique_friendship"),
    )

    id = Column(Integer, primary_key=True)
    requester_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    addressee_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(10), nullable=False)  # pending, accepted, blocked
    created_at = Column(DateTime, server_default=func.now())

    requester = relationship("User", foreign_keys=[requester_id], back_populates="friendships_initiated")
    addressee = relationship("User", foreign_keys=[addressee_id], back_populates="friendships_received")


class UserCurrency(Base):
    __tablename__ = "user_currencies"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    coins = Column(Integer, default=0, nullable=False)
    crystals = Column(Integer, default=0, nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="currencies")


class ItemType(Base):
    __tablename__ = "item_types"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    category = Column(String(15), nullable=False)  # showcase, artifact, profile_theme, showcase_theme
    description = Column(Text)
    icon_url = Column(String(255))
    max_stack = Column(Integer, default=1)
    is_purchasable = Column(Boolean, default=True)
    capacity = Column(Integer, default=0)

    shop_items = relationship("ShopItem", back_populates="item_type")
    inventories = relationship("UserInventory", back_populates="item_type")
    reward_for_achievements = relationship("Achievement", foreign_keys="Achievement.item_reward_id")


class ShopItem(Base):
    __tablename__ = "shop_items"

    id = Column(Integer, primary_key=True)
    item_type_id = Column(Integer, ForeignKey("item_types.id"), nullable=False)
    price_coins = Column(Integer)
    price_crystals = Column(Integer)
    required_level = Column(Integer, default=0)
    is_limited = Column(Boolean, default=False)
    available_from = Column(DateTime)
    available_until = Column(DateTime)
    is_active = Column(Boolean, default=True)

    item_type = relationship("ItemType", back_populates="shop_items")


class UserInventory(Base):
    __tablename__ = "user_inventory"

    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    item_type_id = Column(Integer, ForeignKey("item_types.id"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    acquired_at = Column(DateTime, server_default=func.now())
    is_equipped = Column(Boolean, default=False)
    equipped_slot = Column(Integer)

    user = relationship("User", back_populates="inventory")
    item_type = relationship("ItemType", back_populates="inventories")
    showcase_slots = relationship("UserShowcase", foreign_keys="UserShowcase.showcase_item_id")
    artifact_slots = relationship("UserShowcase", foreign_keys="UserShowcase.artifact_item_id")


class UserShowcase(Base):
    __tablename__ = "user_showcases"
    __table_args__ = (
        UniqueConstraint("user_id", "showcase_item_id", "slot_number", name="unique_showcase_slot"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    showcase_item_id = Column(Integer, ForeignKey("user_inventory.id"), nullable=False)
    slot_number = Column(Integer, nullable=False)
    artifact_item_id = Column(Integer, ForeignKey("user_inventory.id"))

    user = relationship("User", back_populates="showcases")
    showcase_item = relationship("UserInventory", foreign_keys=[showcase_item_id], back_populates="showcase_slots")
    artifact_item = relationship("UserInventory", foreign_keys=[artifact_item_id], back_populates="artifact_slots")