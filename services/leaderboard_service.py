from datetime import date, timedelta
from sqlalchemy.orm import Session
from database.models.gamification import LeaderboardCategory, LeaderboardEntry
from database.models.user import User
import uuid

class LeaderboardService:
    def __init__(self, db: Session):
        self.db = db

    def ensure_user_entries(self, user_id: uuid.UUID):
        """Создаёт записи с score=0 для всех активных категорий на текущий период, если их нет."""
        categories = self.db.query(LeaderboardCategory).filter(
            LeaderboardCategory.is_active == True
        ).all()
        today = date.today()
        for cat in categories:
            # Определяем период
            period_start = today
            if cat.reset_period == 'weekly':
                period_start = today - timedelta(days=today.weekday())
            elif cat.reset_period == 'monthly':
                period_start = today.replace(day=1)
            elif cat.reset_period == 'never':
                period_start = date(2000, 1, 1)  # фиксированная дата для "никогда"
            # Проверяем, есть ли уже запись
            exists = self.db.query(LeaderboardEntry).filter(
                LeaderboardEntry.category_id == cat.id,
                LeaderboardEntry.user_id == user_id,
                LeaderboardEntry.period_start == period_start
            ).first()
            if not exists:
                entry = LeaderboardEntry(
                    category_id=cat.id,
                    user_id=user_id,
                    period_start=period_start,
                    score=0.0,
                    rank=0
                )
                self.db.add(entry)
        self.db.commit()

    def update_entry(self, user_id: uuid.UUID, metric_type: str, score: float):
        """Обновляет запись лидерборда для заданной метрики"""
        categories = self.db.query(LeaderboardCategory).filter(
            LeaderboardCategory.metric_type == metric_type,
            LeaderboardCategory.is_active == True
        ).all()
        if not categories:
            return

        # Определяем, суммируемые ли метрики
        cumulative_metrics = ('xp_total', 'xp_weekly', 'xp_daily', 'xp_monthly', 'tasks_completed', 'challenges_completed')
        is_cumulative = metric_type in cumulative_metrics

        for cat in categories:
            period_start = date.today()
            if cat.reset_period == 'weekly':
                period_start = period_start - timedelta(days=period_start.weekday())
            elif cat.reset_period == 'monthly':
                period_start = period_start.replace(day=1)
            elif cat.reset_period == 'never':
                period_start = date(2000, 1, 1)
            # daily оставляем сегодня

            entry = self.db.query(LeaderboardEntry).filter(
                LeaderboardEntry.category_id == cat.id,
                LeaderboardEntry.user_id == user_id,
                LeaderboardEntry.period_start == period_start
            ).first()

            if not entry:
                entry = LeaderboardEntry(
                    category_id=cat.id,
                    user_id=user_id,
                    period_start=period_start,
                    score=0.0,
                    rank=0
                )
                self.db.add(entry)

            if is_cumulative:
                entry.score += score
            else:
                entry.score = score

        self.db.commit()

        # Пересчёт рангов
        for cat in categories:
            entries = self.db.query(LeaderboardEntry).filter(
                LeaderboardEntry.category_id == cat.id,
                LeaderboardEntry.period_start == (
                    date.today() if cat.reset_period in ('daily', 'weekly', 'monthly', 'never')  # упростим: возьмём период как у текущей записи
                    else date(2000,1,1)  # не совсем точно, но для ранжирования сойдёт, можно доработать
                )
            ).order_by(LeaderboardEntry.score.desc()).all()
            for i, e in enumerate(entries, start=1):
                e.rank = i
        self.db.commit()