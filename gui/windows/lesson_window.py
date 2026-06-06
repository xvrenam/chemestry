# gui/windows/lesson_window.py
import json
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QTabWidget, QScrollArea, QFrame, QMessageBox, QStackedWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from sqlalchemy import func

from basedir import resource_path
from gui.windows.base_window import BaseWindow
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


class LessonWindow(BaseWindow):
    def __init__(self, user, track, lesson, db_session):
        super().__init__("lesson")
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
        self.setMinimumSize(500, 400)
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
        current_geo = self.geometry()
        self.close()
        self.lesson_list = LessonListWindow(self.user, self.track, self.db)
        self.lesson_list.setGeometry(current_geo)
        self.lesson_list.show()

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
        scoring = task.scoring_type
        if scoring == 'binary':
            if attempt.is_correct:
                msg = "Правильно!"
            else:
                msg = "Неправильно!"
        else:
            # Частичная или пропорциональная оценка
            if attempt.score_earned == attempt.score_max:
                msg = f"Правильно! +{attempt.score_earned} из {attempt.score_max} баллов."
            elif attempt.score_earned > 0:
                msg = f"Частично правильно: {attempt.score_earned} из {attempt.score_max} баллов."
            else:
                msg = f"Неправильно. 0 из {attempt.score_max} баллов."

        if attempt.is_correct or (scoring != 'binary' and attempt.score_earned > 0):
            QMessageBox.information(self, "Результат", msg)
        else:
            QMessageBox.warning(self, "Результат", msg)

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
        # Получаем прогресс
        track_progress = self.progress_service.get_or_create_track_progress(self.user.id, self.track.id)
        lesson_progress = self.progress_service.get_or_create_lesson_progress(
            track_progress.id, self.lesson.id
        )

        # Если урок уже завершён – не даём XP повторно
        if lesson_progress.status == 'completed':
            QMessageBox.information(self, "Урок уже пройден", "Вы уже завершили этот урок.")
            self.back_to_lessons()
            return

        # Проверяем теорию (если есть)
        if len(self.content['theory']) > 0 and not lesson_progress.theory_viewed:
            QMessageBox.warning(self, "Ошибка", "Сначала изучите теорию!")
            return

        total_tasks = len(self.lesson_tasks)
        if total_tasks == 0:
            # Нет заданий – урок считается пройденным без XP
            lesson_progress.status = 'completed'
            lesson_progress.completed_at = func.now()
            self.db.commit()
            QMessageBox.information(self, "Урок завершён", "Теория изучена. Урок пройден.")
            self.back_to_lessons()
            return

        # Подсчитываем количество правильно выполненных заданий (или сумму баллов)
        # Используем score_earned и score_total для более точной оценки (если есть partial)
        lesson_attempts = self.db.query(TaskAttempt).filter(
            TaskAttempt.lesson_progress_id == lesson_progress.id
        ).all()
        total_score_earned = sum(att.score_earned for att in lesson_attempts)
        total_score_max = sum(att.score_max for att in lesson_attempts) if lesson_attempts else total_tasks

        # Вычисляем процент (можно использовать и по количеству правильных, и по баллам)
        if total_score_max > 0:
            percent = (total_score_earned / total_score_max) * 100
        else:
            percent = 0.0

        # Если процент ниже 50 – недостаточно для завершения
        if percent < 50:
            QMessageBox.warning(self, "Недостаточно", f"Выполните хотя бы 50% заданий. Сейчас: {percent:.1f}%")
            return

        # Начисляем XP пропорционально успеху (но не более xp_reward)
        xp_reward_full = self.active_version.xp_reward
        xp_earned = int(xp_reward_full * (percent / 100))
        # Минимум 1 XP, если есть хоть какой-то прогресс
        if xp_earned == 0 and percent > 0:
            xp_earned = 1

        # Если трек в режиме повторения – XP не начисляем (или можно начислять уменьшенный, но пока 0)
        if track_progress.is_repeating:
            xp_earned = 0

        # Обновляем прогресс
        lesson_progress.status = 'completed'
        lesson_progress.completed_at = func.now()
        lesson_progress.score_earned = total_score_earned
        lesson_progress.score_total = total_score_max

        if xp_earned > 0:
            track_progress.total_xp += xp_earned
            # Дополнительно можно проверить, не превышает ли track_progress.total_xp сумму XP всех уроков трека
            # Но оставим простое накопление, т.к. при повторном прохождении xp_earned = 0

        self.db.commit()

        # ---- Геймификация (награды) с учётом реально начисленного XP ----
        currency_svc = CurrencyService(self.db)
        # Награда за урок: монеты = XP_заработанные / 2, кристаллы = XP_заработанные / 10
        coins_earned = xp_earned // 2
        crystals_earned = max(1, xp_earned // 10) if xp_earned > 0 else 0
        currency_svc.add_coins(self.user.id, coins_earned)
        currency_svc.add_crystals(self.user.id, crystals_earned)

        # Достижения и челленджи
        achievement_svc = AchievementService(self.db)
        achievement_svc.check_and_award(self.user.id, 'complete_lesson', {
            'track_id': self.track.id,
            'lesson_id': self.lesson.id,
            'score_percent': percent
        })
        achievement_svc.check_and_award(self.user.id, 'count_tasks', {
            'count': len([att for att in lesson_attempts if att.is_correct])
        })

        challenge_svc = ChallengeService(self.db)
        challenge_svc.update_progress(self.user.id, 'complete_lesson', 1)

        # Лидерборды обновляем с фактическим XP
        lb_svc = LeaderboardService(self.db)
        lb_svc.update_entry(self.user.id, 'xp_total', xp_earned)
        lb_svc.update_entry(self.user.id, 'xp_weekly', xp_earned)
        lb_svc.update_entry(self.user.id, 'xp_daily', xp_earned)
        lb_svc.update_entry(self.user.id, 'xp_monthly', xp_earned)
        lb_svc.update_entry(self.user.id, 'tasks_completed', len([att for att in lesson_attempts if att.is_correct]))

        # Статистика тем
        stats_svc = StatisticsService(self.db)
        all_stats = stats_svc.get_all_topic_stats(self.user.id)
        if all_stats:
            total_attempts = sum(s.total_attempts for s in all_stats)
            correct_attempts = sum(s.correct_attempts for s in all_stats)
            if total_attempts > 0:
                accuracy = correct_attempts / total_attempts * 100.0
                lb_svc.update_entry(self.user.id, 'accuracy_rate', accuracy)

        # Разблокируем следующий урок
        next_lesson = self.db.query(Lesson).filter(
            Lesson.track_id == self.track.id,
            Lesson.order_index > self.lesson.order_index
        ).order_by(Lesson.order_index).first()
        if next_lesson:
            track_progress.current_lesson_index = next_lesson.order_index
            # Делаем следующий урок доступным
            next_progress = self.db.query(UserLessonProgress).filter(
                UserLessonProgress.user_track_progress_id == track_progress.id,
                UserLessonProgress.lesson_id == next_lesson.id
            ).first()
            if next_progress:
                next_progress.status = 'available'
            else:
                new_next = UserLessonProgress(
                    user_track_progress_id=track_progress.id,
                    lesson_id=next_lesson.id,
                    status='available'
                )
                self.db.add(new_next)
            self.db.commit()

        QMessageBox.information(self, "Урок завершён", f"Вы набрали {total_score_earned} из {total_score_max} баллов.\nПолучено XP: {xp_earned}.")
        self.back_to_lessons()