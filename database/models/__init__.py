# database/models/__init__.py
from .user import (
    User, Friendship, UserCurrency, ItemType, ShopItem, UserInventory, UserShowcase
)
from .content import (
    Track, Lesson, LessonVersion, Theory, LessonTheory,
    TaskGenerator, TaskPool, Task, TaskVariant, LessonTask
)
from .progress import (
    UserTrackProgress, UserLessonProgress, TaskAttempt, UserTopicStats
)
from .gamification import (
    Achievement, UserAchievement, Challenge, UserChallenge,
    LeaderboardCategory, LeaderboardEntry
)

# Список всех моделей для Alembic или create_all
__all__ = [
    "User", "Friendship", "UserCurrency", "ItemType", "ShopItem", "UserInventory", "UserShowcase",
    "Track", "Lesson", "LessonVersion", "Theory", "LessonTheory",
    "TaskGenerator", "TaskPool", "Task", "TaskVariant", "LessonTask",
    "UserTrackProgress", "UserLessonProgress", "TaskAttempt", "UserTopicStats",
    "Achievement", "UserAchievement", "Challenge", "UserChallenge",
    "LeaderboardCategory", "LeaderboardEntry",
]