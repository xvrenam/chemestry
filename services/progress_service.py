import uuid
from sqlalchemy.sql import func
from sqlalchemy.orm import Session
from database.models.progress import UserTrackProgress, UserLessonProgress
from database.models.user import User
import uuid
from typing import Optional

class ProgressService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_track_progress(self, user_id: uuid.UUID, track_id: int) -> UserTrackProgress:
        """Получить или создать прогресс трека для пользователя."""
        progress = self.db.query(UserTrackProgress).filter(
            UserTrackProgress.user_id == user_id,
            UserTrackProgress.track_id == track_id
        ).first()

        if progress:
            return progress

        new_progress = UserTrackProgress(
            user_id=user_id,
            track_id=track_id,
            status='active',
            started_at=func.now()
        )
        self.db.add(new_progress)
        self.db.commit()
        return new_progress

    def get_or_create_lesson_progress(self, track_progress_id: int, lesson_id: int) -> UserLessonProgress:
        """Получить или создать прогресс урока по ID прогресса трека и ID урока."""
        progress = self.db.query(UserLessonProgress).filter(
            UserLessonProgress.user_track_progress_id == track_progress_id,
            UserLessonProgress.lesson_id == lesson_id
        ).first()

        if progress:
            return progress

        new_progress = UserLessonProgress(
            user_track_progress_id=track_progress_id,
            lesson_id=lesson_id,
            status='locked',  # начальный статус, потом изменится
            started_at=func.now()
        )
        self.db.add(new_progress)
        self.db.commit()
        self.db.refresh(new_progress)
        return new_progress

    def update_lesson_status(self, lesson_progress_id: int, status: str) -> None:
        """Обновить статус урока."""
        self.db.query(UserLessonProgress).filter(
            UserLessonProgress.id == lesson_progress_id
        ).update({'status': status})
        self.db.commit()