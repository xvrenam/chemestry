import uuid
from sqlalchemy.sql import func
from sqlalchemy.orm import Session
from database.models.content import Track, Lesson
from database.models.progress import UserTrackProgress, UserLessonProgress
from typing import List, Optional

class TrackService:
    def __init__(self, db: Session):
        self.db = db

    def get_published_tracks(self) -> List[Track]:
        """Возвращает все опубликованные треки."""
        return self.db.query(Track).filter(Track.is_published == True).all()

    def get_track(self, track_id: int) -> Optional[Track]:
        """Получить трек по ID."""
        return self.db.query(Track).filter(Track.id == track_id).first()

    def check_track_available(self, user_id: uuid.UUID, track_id: int) -> bool:
        """Проверить, доступен ли трек пользователю."""
        # Проверяем, есть ли уже прогресс по этому треку
        progress = self.db.query(UserTrackProgress).filter(
            UserTrackProgress.user_id == user_id,
            UserTrackProgress.track_id == track_id
        ).first()
        if progress:
            # Если прогресс существует, проверяем статус
            if progress.status == 'completed':
                # Трек завершён, следующий доступен
                return True
            elif progress.status in ('active', 'paused', 'repeating'):
                # Активен, приостановлен или повторяется - проверяем, не заблокирован ли предыдущий трек
                prev_track = self.db.query(UserTrackProgress).filter(
                    UserTrackProgress.user_id == user_id,
                    UserTrackProgress.track_id == track_id - 1
                ).first()
                if prev_track and prev_track.status == 'completed':
                    return True
        # Если ничего не найдено или заблокировано
        return False

    def start_track(self, user_id: uuid.UUID, track_id: int) -> Optional[UserTrackProgress]:
        """Начать трек для пользователя, создать прогресс."""
        # Проверяем, нет ли уже записи
        existing = self.db.query(UserTrackProgress).filter(
            UserTrackProgress.user_id == user_id,
            UserTrackProgress.track_id == track_id
        ).first()
        if existing:
            return existing
        # Создаём новый прогресс
        new_progress = UserTrackProgress(
            user_id=user_id,
            track_id=track_id,
            status='active',
            started_at=func.now(),
            current_lesson_index=0
        )
        self.db.add(new_progress)
        self.db.commit()
        self.db.refresh(new_progress)
        
        # Создаём прогресс для первого урока со статусом available
        first_lesson = self.db.query(Lesson).filter(
            Lesson.track_id == track_id
        ).order_by(Lesson.order_index).first()
        if first_lesson:
            first_lesson_progress = UserLessonProgress(
                user_track_progress_id=new_progress.id,
                lesson_id=first_lesson.id,
                status='available',
                started_at=func.now()
            )
            self.db.add(first_lesson_progress)
            self.db.commit()

        return new_progress