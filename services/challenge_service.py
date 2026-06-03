from datetime import date
from sqlalchemy.orm import Session
from database.models.gamification import Challenge, UserChallenge
import uuid

class ChallengeService:
    def __init__(self, db: Session):
        self.db = db

    def get_active_challenges(self, user_id: uuid.UUID):
        """Возвращает активные ежедневные/еженедельные челленджи пользователя"""
        today = date.today()
        # Получаем все активные глобальные челленджи на сегодня
        global_challenges = self.db.query(Challenge).filter(
            Challenge.is_active == True,
            Challenge.valid_from <= today,
            Challenge.valid_until >= today
        ).all()

        result = []
        for ch in global_challenges:
            uc = self.db.query(UserChallenge).filter(
                UserChallenge.user_id == user_id,
                UserChallenge.challenge_id == ch.id
            ).first()
            if not uc:
                uc = UserChallenge(
                    user_id=user_id,
                    challenge_id=ch.id,
                    progress_current=0,
                    progress_target=ch.condition_data.get('target', 1)
                )
                self.db.add(uc)
                self.db.commit()
            result.append((ch, uc))
        return result

    def update_progress(self, user_id: uuid.UUID, event_type: str, amount: int = 1):
        """Вызывается при совершении действий (завершение урока, задание и т.п.)"""
        active = self.get_active_challenges(user_id)
        for ch, uc in active:
            if ch.condition_type == event_type:
                uc.progress_current += amount
                if uc.progress_current >= uc.progress_target and not uc.is_completed:
                    uc.is_completed = True
                    # награда будет выдана при запросе (claim)
                self.db.commit()