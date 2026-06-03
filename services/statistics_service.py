from sqlalchemy.orm import Session
from database.models.progress import UserTopicStats, TaskAttempt
from database.models.content import Task
import uuid

class StatisticsService:
    def __init__(self, db: Session):
        self.db = db

    def update_topic_stats(self, user_id: uuid.UUID, topic_tags: list, is_correct: bool, task_type: str = None):
        """Обновляет статистику по каждому тегу после попытки"""
        for tag in topic_tags:
            stats = self.db.query(UserTopicStats).filter(
                UserTopicStats.user_id == user_id,
                UserTopicStats.topic_tag == tag
            ).first()
            if not stats:
                stats = UserTopicStats(
                    user_id=user_id,
                    topic_tag=tag,
                    total_attempts = 0,
                    correct_attempts = 0,
                    current_streak = 0,
                    max_streak = 0
                    )
                self.db.add(stats)

            if stats.total_attempts:
                stats.total_attempts += 1
            else:
                stats.total_attempts = 1

            if is_correct:
                if stats.correct_attempts:
                    stats.correct_attempts += 1
                else:
                    stats.correct_attempts = 1
                if stats.current_streak:
                    stats.current_streak += 1
                else:
                    stats.current_streak = 1
                if stats.max_streak:
                    stats.max_streak = max(stats.max_streak, stats.current_streak)
                else:
                    stats.max_streak = max(0, stats.current_streak)
            else:
                stats.current_streak = 0

            # Обновляем статистику по типам заданий
            if task_type:
                type_dict = stats.stats_by_task_type or {}
                type_data = type_dict.get(task_type, {'total': 0, 'correct': 0})
                type_data['total'] += 1
                if is_correct:
                    type_data['correct'] += 1
                type_dict[task_type] = type_data
                stats.stats_by_task_type = type_dict

            # Пересчитываем accuracy_rate
            stats.accuracy_rate = (stats.correct_attempts / stats.total_attempts) * 100
            self.db.commit()

    def get_weakest_topics(self, user_id: uuid.UUID, limit=3):
        """Возвращает темы с самой низкой точностью для повторения"""
        stats = self.db.query(UserTopicStats).filter(
            UserTopicStats.user_id == user_id,
            UserTopicStats.total_attempts >= 3  # минимальный опыт
        ).order_by(UserTopicStats.accuracy_rate.asc()).limit(limit).all()
        return stats
    
    def get_all_topic_stats(self, user_id: uuid.UUID):
        return self.db.query(UserTopicStats).filter(UserTopicStats.user_id == user_id).all()