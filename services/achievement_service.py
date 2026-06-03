from sqlalchemy.orm import Session
from database.models.gamification import Achievement, UserAchievement
from database.models.user import User, UserInventory
from database.models.progress import TaskAttempt, UserLessonProgress, UserTopicStats,UserTrackProgress
from database.models.content import Task
import uuid

class AchievementService:
    def __init__(self, db: Session):
        self.db = db

    def check_and_award(self, user_id: uuid.UUID, event_type: str, event_data: dict = None):
        """После важного действия (завершение урока, серия правильных ответов и т.д.)"""
        achievements = self.db.query(Achievement).filter(
            Achievement.condition_type == event_type
        ).all()

        for ach in achievements:
            if self._condition_met(ach, user_id, event_data):
                existing = self.db.query(UserAchievement).filter(
                    UserAchievement.user_id == user_id,
                    UserAchievement.achievement_id == ach.id
                ).first()
                if not existing:
                    ua = UserAchievement(user_id=user_id, achievement_id=ach.id)
                    self.db.add(ua)
                    # Награда
                    from services.currency_service import CurrencyService
                    curr = CurrencyService(self.db)
                    if ach.xp_reward:
                        # Здесь нужно сервис прогресса для добавления XP, но передадим обработку вызывающему коду
                        pass
                    if ach.coins_reward:
                        curr.add_coins(user_id, ach.coins_reward)
                    if ach.crystals_reward:
                        curr.add_crystals(user_id, ach.crystals_reward)
                    if ach.item_reward_id:
                        from services.shop_service import ShopService
                        shop = ShopService(self.db)
                        shop.add_item_to_inventory(user_id, ach.item_reward_id)
                    self.db.commit()

    def _condition_met(self, achievement: Achievement, user_id: uuid.UUID, event_data: dict) -> bool:
        data = achievement.condition_data
        if achievement.condition_type == 'complete_lesson':
            # data: {"count": int}
            completed = self.db.query(UserLessonProgress).join(
                UserTrackProgress,
                UserLessonProgress.user_track_progress_id == UserTrackProgress.id
            ).filter(
                UserTrackProgress.user_id == user_id,
                UserLessonProgress.status == 'completed'
            ).count()
            return completed >= data['count']
        elif achievement.condition_type == 'complete_track':
            completed = self.db.query(UserTrackProgress).filter(
                UserTrackProgress.user_id == user_id,
                UserTrackProgress.status == 'completed'
            ).count()
            return completed >= data.get('count', 1)
        elif achievement.condition_type == 'streak':
            user = self.db.query(User).filter(User.id == user_id).first()
            return user.current_streak >= data['days']
        elif achievement.condition_type == 'count_tasks':
            count = self.db.query(TaskAttempt).filter(
                TaskAttempt.user_id == user_id,
                TaskAttempt.is_correct == True
            ).count()
            return count >= data['count']
        elif achievement.condition_type == 'count_tasks_by_type':
            count = self.db.query(TaskAttempt).join(Task).filter(
                TaskAttempt.user_id == user_id,
                TaskAttempt.is_correct == True,
                Task.type == data['type']
            ).count()
            return count >= data['count']
        elif achievement.condition_type == 'accuracy':
            stats = self.db.query(UserTopicStats).filter(UserTopicStats.user_id == user_id).all()
            total_attempts = sum(s.total_attempts for s in stats)
            if total_attempts < data.get('min_attempts', 0):
                return False
            correct_attempts = sum(s.correct_attempts for s in stats)
            accuracy = correct_attempts / total_attempts if total_attempts > 0 else 0
            return accuracy >= data['threshold']
        elif achievement.condition_type == 'collect_items':
            inventory_count = self.db.query(UserInventory).filter(
                UserInventory.user_id == user_id
            ).count()
            return inventory_count >= data['count']
        elif achievement.condition_type == 'showcase_artifacts':
            artifacts_count = self.db.query(UserInventory).filter(
                UserInventory.user_id == user_id,
                UserInventory.is_equipped == True,
                UserInventory.item_type.has(category='artifact')
            ).count()
            return artifacts_count >= data['count']
        elif achievement.condition_type == 'speed':
            # Проверяем, есть ли попытка с временем <= max_seconds
            # event_data должно содержать 'time_spent' для проверки, но это событие при каждой попытке.
            # Для упрощения сделаем проверку при завершении попытки, если время меньше порога.
            if event_data and 'time_spent' in event_data:
                return event_data['time_spent'] <= data['max_seconds']
            return False
        return False
    
    def get_user_achievements(self, user_id: uuid.UUID) -> list:
        """Возвращает все достижения пользователя с объектами Achievement."""
        return self.db.query(UserAchievement).filter(
            UserAchievement.user_id == user_id
        ).all()

    def toggle_display(self, user_id: uuid.UUID, achievement_id: int, show: bool):
        ua = self.db.query(UserAchievement).filter(
            UserAchievement.user_id == user_id,
            UserAchievement.id == achievement_id
        ).first()
        if ua:
            ua.is_displayed = show
            self.db.commit()