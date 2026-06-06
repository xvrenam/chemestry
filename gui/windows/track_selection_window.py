# gui/windows/track_selection_window.py
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt
from gui.windows.base_window import BaseWindow
from database.db import SessionLocal
from database.models.progress import UserTrackProgress
from services.track_service import TrackService
from services.progress_service import ProgressService
from gui.windows.lesson_list_window import LessonListWindow
from gui.windows.main_window import MainMenuWindow
import uuid

class TrackSelectionWindow(BaseWindow):
    def __init__(self, user, db_session):
        super().__init__("track_selection")
        self.user = user
        self.db = db_session
        self.track_service = TrackService(self.db)
        self.progress_service = ProgressService(self.db)

        self.setWindowTitle("Выбор трека")
        self.setMinimumSize(500, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Заголовок
        title = QLabel("Доступные образовательные треки")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        # Скролл с треками
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        tracks_layout = QVBoxLayout()
        container.setLayout(tracks_layout)

        tracks = self.track_service.get_published_tracks()
        for track in tracks:
            # Получаем прогресс пользователя по треку
            progress = self.db.query(UserTrackProgress).filter(
                UserTrackProgress.user_id == self.user.id,
                UserTrackProgress.track_id == track.id
            ).first()
            frame = self.create_track_frame(track, progress)
            tracks_layout.addWidget(frame)

        tracks_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

        # Кнопка назад
        back_btn = QPushButton("Назад в меню")
        back_btn.clicked.connect(self.back_to_menu)
        layout.addWidget(back_btn)

        self.setLayout(layout)

    def create_track_frame(self, track, progress):
        frame = QFrame()
        frame.setFixedHeight(100)

        hbox = QHBoxLayout()

        # Информация о треке
        info_layout = QVBoxLayout()
        name_label = QLabel(track.name)
        name_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        desc_label = QLabel(track.description or "")
        desc_label.setWordWrap(True)

        # Прогресс
        if progress:
            progress_text = f"Прогресс: {progress.total_xp} XP"
            if progress.status == 'completed':
                progress_text += " (завершён)"
            elif progress.status == 'active':
                progress_text += f" (урок {progress.current_lesson_index + 1})"
        else:
            progress_text = "Новый трек"
        progress_label = QLabel(progress_text)

        info_layout.addWidget(name_label)
        info_layout.addWidget(desc_label)
        info_layout.addWidget(progress_label)
        info_layout.addStretch()

        # Кнопка действия
        btn = QPushButton()
        if progress and progress.status == 'completed':
            btn.setText("Повторить")
        elif progress and progress.status == 'active':
            btn.setText("Продолжить")
        else:
            btn.setText("Начать")
        btn.clicked.connect(lambda checked, t=track, p=progress: self.handle_track_action(t, p))

        hbox.addLayout(info_layout, 1)
        hbox.addWidget(btn, 0)
        frame.setLayout(hbox)

        return frame

    def handle_track_action(self, track, progress):
        if not progress:
            # Начинаем трек
            self.track_service.start_track(self.user.id, track.id)
        # Открываем список уроков
        self.open_lesson_list(track)

    def open_lesson_list(self, track):
        current_geo = self.geometry()
        self.close()
        self.lesson_list_window = LessonListWindow(self.user, track, self.db)
        self.lesson_list_window.setGeometry(current_geo)
        self.lesson_list_window.show()

    def back_to_menu(self):
        current_geo = self.geometry()
        self.close()
        self.menu = MainMenuWindow(self.user, self.db)
        self.menu.setGeometry(current_geo)
        self.menu.show()