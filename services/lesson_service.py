import uuid
from sqlalchemy.orm import Session
from database.models.content import Lesson, LessonVersion, Theory, LessonTheory, Task, LessonTask
from database.models.progress import UserLessonProgress
from typing import List, Optional

class LessonService:
    def __init__(self, db: Session):
        self.db = db

    def get_lessons_in_track(self, track_id: int) -> List[Lesson]:
        """Получить все уроки трека в правильном порядке."""
        return self.db.query(Lesson).filter(
            Lesson.track_id == track_id
        ).order_by(Lesson.order_index).all()

    def get_lesson_with_content(self, lesson_id: int, user_id: uuid.UUID) -> Optional[dict]:
        """Получить урок с активной версией теории и заданиями."""
        lesson = self.db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if not lesson:
            return None

        # Находим активную версию
        active_version = self.db.query(LessonVersion).filter(
            LessonVersion.version_of == lesson_id,
            LessonVersion.is_active == True
        ).order_by(LessonVersion.version_number.desc()).first()

        if not active_version:
            return None

        # Получаем теорию и задания
        theory_items = self.db.query(LessonTheory, Theory).select_from(
            LessonTheory
        ).join(
            Theory, LessonTheory.theory_id == Theory.id
        ).filter(
            LessonTheory.lesson_id == lesson_id
        ).order_by(LessonTheory.order_index).all()

        task_items = self.db.query(LessonTask, Task).select_from(
            LessonTask
        ).join(
            Task, LessonTask.task_id == Task.id
        ).filter(
            LessonTask.lesson_id == lesson_id
        ).order_by(LessonTask.order_index).all()

        return {
            'lesson': lesson,
            'active_version': active_version,
            'theory': theory_items,
            'tasks': task_items
        }
