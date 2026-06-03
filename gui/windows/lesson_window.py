# gui/windows/lesson_window.py
import json
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QTabWidget, QScrollArea, QFrame, QMessageBox, QStackedWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from sqlalchemy import func

from basedir import resource_path
from database.db import SessionLocal
from services.lesson_service import LessonService
from services.task_service import TaskService
from services.progress_service import ProgressService
from gui.widgets.task_widgets import create_task_widget
from gui.widgets.molecule_widget import MoleculeWidget
from database.models.content import Lesson
from database.models.progress import TaskAttempt, UserLessonProgress
from services.currency_service import CurrencyService
from services.achievement_service import AchievementService
from services.challenge_service import ChallengeService
from services.leaderboard_service import LeaderboardService
from services.statistics_service import StatisticsService


class LessonWindow(QWidget):
    def __init__(self, user, track, lesson, db_session):
        super().__init__()
        self.user = user
        self.track = track
        self.lesson = lesson
        self.db = db_session
        self.lesson_service = LessonService(self.db)
        self.progress_service = ProgressService(self.db)
        self.task_service = TaskService(self.db)

        # Получаем данные урока
        self.content = self.lesson_service.get_lesson_with_content(lesson.id, user.id)
        self.active_version = self.content['active_version']

        self.lesson_tasks = self.task_service.get_lesson_tasks(lesson.id)  # список (LessonTask, Task)
        self.current_task_idx = 0
        self.task_variants = {}  # кеш вариантов для заданий
        self.task_widgets = {}   # кеш виджетов заданий (опционально)

        self.setWindowTitle(f"Урок: {self.active_version.title}")
        self.setFixedSize(800, 600)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Заголовок с информацией
        header = QHBoxLayout()
        title_label = QLabel(self.active_version.title)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        xp_label = QLabel(f"Награда: {self.active_version.xp_reward} XP")
        xp_label.setProperty("class", "xp-label")
        header.addWidget(title_label)
        header.addStretch()
        header.addWidget(xp_label)
        main_layout.addLayout(header)

        # Вкладки
        self.tabs = QTabWidget()
        self.theory_tab = self.create_theory_tab()
        self.tabs.addTab(self.theory_tab, "Теория")
        # Практика пока заглушка
        # ... создаём вкладку практики ...
        self.setup_practice_tab()
        main_layout.addWidget(self.tabs)

        # Нижняя панель с кнопками
        bottom_layout = QHBoxLayout()
        self.back_btn = QPushButton("Назад к урокам")
        self.back_btn.clicked.connect(self.back_to_lessons)
        self.complete_theory_btn = QPushButton("Завершить теорию")
        self.complete_theory_btn.clicked.connect(self.complete_theory)
        bottom_layout.addWidget(self.back_btn)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.complete_theory_btn)
        main_layout.addLayout(bottom_layout)

        self.setLayout(main_layout)

    def create_theory_tab(self):
        """Создаёт вкладку с теорией на основе JSONB."""
        widget = QWidget()
        layout = QVBoxLayout()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_layout = QVBoxLayout()

        # Проходим по всем элементам теории
        for lesson_theory, theory in self.content['theory']:
            data = theory.data
            if isinstance(data, str):
                data = json.loads(data)
            blocks = data.get('blocks', [])
            for block in blocks:
                if block['type'] == 'text':
                    label = QLabel(block['content'])
                    label.setWordWrap(True)
                    label.setStyleSheet("font-size: 14px; margin: 5px;")
                    content_layout.addWidget(label)
                elif block['type'] == 'image':
                    # Изображение (путь к файлу)
                    pixmap = QPixmap(resource_path(block['src']))
                    if not pixmap.isNull():
                        img_label = QLabel()
                        img_label.setPixmap(pixmap.scaledToWidth(600, Qt.TransformationMode.SmoothTransformation))
                        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        content_layout.addWidget(img_label)
                        if 'caption' in block:
                            caption = QLabel(block['caption'])
                            caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
                            caption.setStyleSheet("color: #aaa; font-style: italic;")
                            content_layout.addWidget(caption)
                    else:
                        error_label = QLabel(f"Изображение не найдено: {block['src']}")
                        error_label.setStyleSheet("color: red;")
                        content_layout.addWidget(error_label)
                elif block['type'] == 'molecule':
                    molecule_view = MoleculeWidget()
                    molecule_view.load_from_data(block['data'])
                    molecule_view.setFixedSize(300, 200)
                    content_layout.addWidget(molecule_view)

        content_layout.addStretch()
        content_widget.setLayout(content_layout)
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        widget.setLayout(layout)
        return widget

    def complete_theory(self):
        # Отмечаем теорию как просмотренную
        track_progress = self.progress_service.get_or_create_track_progress(self.user.id, self.track.id)
        lesson_progress = self.progress_service.get_or_create_lesson_progress(
            track_progress.id, self.lesson.id
        )
        lesson_progress.theory_viewed = True
        lesson_progress.theory_viewed_at = func.now()
        self.db.commit()
        QMessageBox.information(self, "Теория", "Теория отмечена как изученная. Теперь можно перейти к заданиям.")
        # Активируем вкладку "Практика" (пока заглушка)
        self.tabs.setCurrentIndex(1)

    def back_to_lessons(self):
        from gui.windows.lesson_list_window import LessonListWindow
        self.lesson_list = LessonListWindow(self.user, self.track, self.db)
        self.lesson_list.show()
        self.close()

    def setup_practice_tab(self):
        """Настраивает вкладку «Практика»."""
        practice_widget = QWidget()
        layout = QVBoxLayout()

        # Стек для отображения текущего задания
        self.task_stack = QStackedWidget()
        layout.addWidget(self.task_stack, 1)

        # Панель с прогрессом и кнопками
        control_layout = QHBoxLayout()
        self.progress_label = QLabel(f"Задание 0 из {len(self.lesson_tasks)}")
        control_layout.addWidget(self.progress_label)
        control_layout.addStretch()
        self.next_btn = QPushButton("Далее")
        self.next_btn.setEnabled(False)
        self.next_btn.clicked.connect(self.next_task)
        control_layout.addWidget(self.next_btn)
        layout.addLayout(control_layout)

        # Кнопка завершения урока
        self.finish_btn = QPushButton("Завершить урок")
        self.finish_btn.setEnabled(False)
        self.finish_btn.clicked.connect(self.finish_lesson)
        layout.addWidget(self.finish_btn)

        practice_widget.setLayout(layout)
        self.tabs.addTab(practice_widget, "Практика")

        # Загружаем первое задание
        self.load_task(0)

    def load_task(self, index):
        """Загружает задание по индексу в task_stack."""
        if index >= len(self.lesson_tasks):
            # Все задания пройдены
            self.task_stack.setCurrentIndex(-1)
            self.progress_label.setText("Все задания выполнены!")
            self.next_btn.setEnabled(False)
            self.finish_btn.setEnabled(True)
            return

        lesson_task, task = self.lesson_tasks[index]
        # Получаем или создаём вариант
        if task.id not in self.task_variants:
            variant = self.task_service.get_or_create_variant(task)
            self.task_variants[task.id] = variant
        else:
            variant = self.task_variants[task.id]

        # Создаём виджет задания
        widget = create_task_widget(task, variant)
        widget.answer_submitted.connect(self.on_answer_submitted)

        # Добавляем в стек (если уже был, заменяем)
        if self.task_stack.count() > index:
            self.task_stack.removeWidget(self.task_stack.widget(index))
        self.task_stack.insertWidget(index, widget)
        self.task_stack.setCurrentIndex(index)

        self.progress_label.setText(f"Задание {index+1} из {len(self.lesson_tasks)}")
        self.next_btn.setEnabled(False)  # ждём ответа

    def on_answer_submitted(self, answer):
        """Обрабатывает ответ пользователя на текущее задание."""
        idx = self.current_task_idx
        lesson_task, task = self.lesson_tasks[idx]
        variant = self.task_variants[task.id]

        # Сохраняем попытку
        track_progress = self.progress_service.get_or_create_track_progress(self.user.id, self.track.id)
        lesson_progress = self.progress_service.get_or_create_lesson_progress(
            track_progress.id, self.lesson.id
        )
        attempt = self.task_service.save_attempt(
            user_id=self.user.id,
            task_id=task.id,
            variant_id=variant.id,
            user_answer=answer,
            lesson_progress_id=lesson_progress.id
        )

        # Проверяем результат и даём обратную связь
        if attempt.is_correct:
            QMessageBox.information(self, "Результат", "Правильно!")
        else:
            QMessageBox.warning(self, "Результат", "Неправильно!")

        # Разрешаем переход к следующему только если это не последнее задание
        if idx < len(self.lesson_tasks) - 1:
            self.next_btn.setEnabled(True)
        else:
            self.next_btn.setEnabled(False)  # на всякий случай деактивируем
            self.finish_btn.setEnabled(True)

    def next_task(self):
        """Переход к следующему заданию."""
        self.current_task_idx += 1
        if self.current_task_idx < len(self.lesson_tasks):
            self.load_task(self.current_task_idx)
        else:
            self.task_stack.setCurrentIndex(-1)
            self.progress_label.setText("Все задания выполнены!")
            self.next_btn.setEnabled(False)
            self.finish_btn.setEnabled(True)

    def finish_lesson(self):
        """Завершает урок, если условия выполнены."""
        # Проверяем, что теория просмотрена и выполнено >50% заданий
        track_progress = self.progress_service.get_or_create_track_progress(self.user.id, self.track.id)
        lesson_progress = self.progress_service.get_or_create_lesson_progress(
            track_progress.id, self.lesson.id
        )
        if len(self.content['theory']) > 0 and not lesson_progress.theory_viewed:
            QMessageBox.warning(self, "Ошибка", "Сначала изучите теорию!")
            return

        total_tasks = len(self.lesson_tasks)
        if total_tasks == 0:
            # Если нет заданий, урок считается пройденным после теории
            lesson_progress.status = 'completed'
            lesson_progress.completed_at = func.now()
            # Начисляем XP и т.д.
            self.db.commit()
            QMessageBox.information(self, "Урок завершён", "Поздравляем! Урок пройден.")
            self.back_to_lessons()
            return

        # Подсчитываем количество успешно выполненных заданий
        completed_tasks = self.db.query(TaskAttempt).filter(
            TaskAttempt.lesson_progress_id == lesson_progress.id,
            TaskAttempt.is_correct == True
        ).count()
        # Статистика по темам
        stats_svc = StatisticsService(self.db)
        for lesson_task, task in self.lesson_tasks:
            # ищем последнюю попытку этого задания в рамках урока
            last_attempt = self.db.query(TaskAttempt).filter(
                TaskAttempt.user_id == self.user.id,
                TaskAttempt.task_id == task.id,
                TaskAttempt.lesson_progress_id == lesson_progress.id
            ).order_by(TaskAttempt.created_at.desc()).first()
            if last_attempt:
                stats_svc.update_topic_stats(
                    self.user.id,
                    task.topic_tags,
                    is_correct=last_attempt.is_correct,
                    task_type=task.type
                )

        percent = (completed_tasks / total_tasks) * 100
        if percent >= 50:
            lesson_progress.status = 'completed'
            lesson_progress.completed_at = func.now()
            track_progress.total_xp += self.active_version.xp_reward
            self.db.commit()

            next_lesson = self.db.query(Lesson).filter(
                Lesson.track_id == self.track.id,
                Lesson.order_index > self.lesson.order_index
            ).order_by(Lesson.order_index).first()
            if next_lesson:
                track_progress.current_lesson_index = next_lesson.order_index
            else:
                track_progress.current_lesson_index = self.lesson.order_index
            self.db.commit()

            # ---------- Геймификация ----------
            currency_svc = CurrencyService(self.db)
            # Награда за урок: монеты = XP/2, кристаллы = XP/10
            coins_earned = self.active_version.xp_reward // 2
            crystals_earned = max(1, self.active_version.xp_reward // 10)
            currency_svc.add_coins(self.user.id, coins_earned)
            currency_svc.add_crystals(self.user.id, crystals_earned)

            # Достижения
            achievement_svc = AchievementService(self.db)
            achievement_svc.check_and_award(self.user.id, 'complete_lesson', {
                'track_id': self.track.id,
                'lesson_id': self.lesson.id,
                'score_percent': percent
            })
            achievement_svc.check_and_award(self.user.id, 'count_tasks', {
                'count': completed_tasks
            })

            # Челленджи
            challenge_svc = ChallengeService(self.db)
            challenge_svc.update_progress(self.user.id, 'complete_lesson', 1)

            # Лидерборды
            lb_svc = LeaderboardService(self.db)
            lb_svc.update_entry(self.user.id, 'xp_total', self.active_version.xp_reward)
            lb_svc.update_entry(self.user.id, 'xp_weekly', self.active_version.xp_reward)
            lb_svc.update_entry(self.user.id, 'xp_daily', self.active_version.xp_reward)
            lb_svc.update_entry(self.user.id, 'xp_monthly', self.active_version.xp_reward)
            lb_svc.update_entry(self.user.id, 'tasks_completed', completed_tasks)

            # Статистика тем (из тегов заданий)
            stats_svc = StatisticsService(self.db)
            all_stats = stats_svc.get_all_topic_stats(self.user.id)
            if all_stats:
                total_attempts = sum(s.total_attempts for s in all_stats)
                correct_attempts = sum(s.correct_attempts for s in all_stats)
                if total_attempts > 0:
                    accuracy = correct_attempts / total_attempts * 100.0
                    lb_svc.update_entry(self.user.id, 'accuracy_rate', accuracy)

            QMessageBox.information(self, "Урок завершён", f"Урок пройден! Получено {self.active_version.xp_reward} XP.")
            self.back_to_lessons()
        else:
            QMessageBox.warning(self, "Недостаточно", f"Выполните хотя бы 50% заданий. Сейчас: {percent:.1f}%")