# gui/windows/lesson_list_window.py
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt
from database.db import SessionLocal
from database.models.progress import UserLessonProgress
from services.lesson_service import LessonService
from services.progress_service import ProgressService
from gui.windows.lesson_window import LessonWindow
from database.models.content import LessonVersion
import uuid

class LessonListWindow(QWidget):
    def __init__(self, user, track, db_session):
        super().__init__()
        self.user = user
        self.track = track
        self.db = db_session
        self.lesson_service = LessonService(self.db)
        self.progress_service = ProgressService(self.db)

        self.setWindowTitle(f"Уроки: {track.name}")
        self.setFixedSize(800, 500)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Заголовок
        title = QLabel(f"Трек: {self.track.name}")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        # Список уроков
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        lessons_layout = QVBoxLayout()
        container.setLayout(lessons_layout)

        lessons = self.lesson_service.get_lessons_in_track(self.track.id)
        track_progress = self.progress_service.get_or_create_track_progress(self.user.id, self.track.id)

        for idx, lesson in enumerate(lessons):
            # Получаем существующий прогресс урока (без создания)
            lesson_progress = self.db.query(UserLessonProgress).filter(
                UserLessonProgress.user_track_progress_id == track_progress.id,
                UserLessonProgress.lesson_id == lesson.id
            ).first()

            # Определяем, заблокирован ли урок
            is_locked = True
            if track_progress.is_repeating:
                is_locked = False
            elif idx == 0:
                is_locked = False  # первый урок всегда доступен
            elif idx > 0:
                prev_lesson = lessons[idx-1]
                prev_progress = self.db.query(UserLessonProgress).filter(
                    UserLessonProgress.user_track_progress_id == track_progress.id,
                    UserLessonProgress.lesson_id == prev_lesson.id
                ).first()
                if prev_progress and prev_progress.status in ('completed', 'skipped'):
                    is_locked = False

            # Если урок доступен, но прогресса ещё нет, создадим его при открытии (в LessonWindow)
            # Пока просто передаём флаг is_locked

            active_version = self.db.query(LessonVersion).filter(
                LessonVersion.version_of == lesson.id,
                LessonVersion.is_active == True
            ).order_by(LessonVersion.version_number.desc()).first()
            title_text = active_version.title if active_version else f"Урок {lesson.order_index}"

            frame = self.create_lesson_frame(lesson, title_text, lesson_progress, is_locked)
            lessons_layout.addWidget(frame)

        lessons_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

        # Кнопка назад
        back_btn = QPushButton("Назад к трекам")
        back_btn.clicked.connect(self.back_to_tracks)
        layout.addWidget(back_btn)

        self.setLayout(layout)

    def create_lesson_frame(self, lesson, title, progress, is_locked):
        frame = QFrame()
        frame.setProperty("class", "lesson-frame")
        frame.setFixedHeight(70)

        hbox = QHBoxLayout()

        # Номер урока
        num_label = QLabel(f"{lesson.order_index+1}.")
        num_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        num_label.setFixedWidth(30)

        # Название
        name_label = QLabel(title)
        name_label.setStyleSheet("font-size: 14px;")

        # Статус
        if progress:
            status_text = progress.status
            if progress.status == 'completed':
                status_text = "✓ Завершён"
            elif progress.status == 'in_progress':
                status_text = "В процессе"
            elif progress.status == 'skipped':
                status_text = "Пропущен"
            elif progress.status == 'locked':
                status_text = "🔒 Заблокирован"
            elif progress.status == 'available':
                status_text = "Доступен"
        else:
            # Если прогресса нет, но урок не заблокирован - значит он новый
            if is_locked:
                status_text = "🔒 Заблокирован"
            else:
                status_text = "Новый"
        status_label = QLabel(status_text)
        status_label.setProperty("class", "status-label")

        hbox.addWidget(num_label)
        hbox.addWidget(name_label, 1)
        hbox.addWidget(status_label, 0)

        # Кнопка "Открыть", если урок не заблокирован
        if not is_locked and (progress is None or progress.status != 'locked'):
            open_btn = QPushButton("Открыть")
            open_btn.clicked.connect(lambda checked, l=lesson: self.open_lesson(l))
            hbox.addWidget(open_btn, 0)
        else:
            dummy = QLabel("")
            dummy.setFixedWidth(80)
            hbox.addWidget(dummy)

        frame.setLayout(hbox)
        return frame

    def open_lesson(self, lesson):
        self.lesson_window = LessonWindow(self.user, self.track, lesson, self.db)
        self.lesson_window.show()
        self.close()

    def back_to_tracks(self):
        from gui.windows.track_selection_window import TrackSelectionWindow
        self.tracks_window = TrackSelectionWindow(self.user, self.db)
        self.tracks_window.show()
        self.close()