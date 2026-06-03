from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database.models.content import Task
from database.models.progress import UserLessonProgress, TaskAttempt, UserTopicStats
import uuid

class SpacedRepetitionService:
    def __init__(self, db: Session):
        self.db = db

    def get_topics_to_repeat(self, user_id: uuid.UUID, limit=5):
        """
        Возвращает список тегов тем, которые рекомендовано повторить.
        Использует простейший алгоритм: низкая точность + прошло > N дней с последней практики.
        """
        stats = self.db.query(UserTopicStats).filter(
            UserTopicStats.user_id == user_id,
            UserTopicStats.total_attempts >= 3
        ).all()
        now = datetime.now()
        topics = []
        for s in stats:
            last_attempt = self.db.query(TaskAttempt).join(TaskAttempt.task).filter(
                TaskAttempt.user_id == user_id,
                Task.topic_tags.contains([s.topic_tag])
            ).order_by(TaskAttempt.created_at.desc()).first()
            if last_attempt and (now - last_attempt.created_at) > timedelta(days=3):
                topics.append(s)
        # Сортируем по возрастанию точности
        topics.sort(key=lambda x: x.accuracy_rate)
        return topics[:limit]

    def get_repeat_recommendations(self, user_id: uuid.UUID) -> list:
        """Возвращает список тегов с рекомендациями"""
        return [s.topic_tag for s in self.get_topics_to_repeat(user_id)]