from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QHeaderView
)
from PyQt6.QtCore import Qt
from datetime import date, timedelta
from services.leaderboard_service import LeaderboardService
from services.friends_service import FriendsService

class LeaderboardWindow(QWidget):
    def __init__(self, user, db_session):
        super().__init__()
        self.user = user
        self.db = db_session
        self.leaderboard_svc = LeaderboardService(self.db)
        self.friends_svc = FriendsService()

        self.setWindowTitle("Доска почёта")
        self.setFixedSize(700, 500)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Верхняя панель: выбор скоупа и метрики
        top_layout = QHBoxLayout()

        # ComboBox для скоупа (глобальный / друзья)
        self.scope_combo = QComboBox()
        self.scope_combo.addItems(["Глобальный рейтинг", "Рейтинг среди друзей"])
        self.scope_combo.currentIndexChanged.connect(self.on_scope_changed)
        top_layout.addWidget(QLabel("Категория:"))
        top_layout.addWidget(self.scope_combo)

        # ComboBox для метрики (заполняется в зависимости от скоупа)
        self.metric_combo = QComboBox()
        self.metric_combo.currentIndexChanged.connect(self.load_leaderboard)
        top_layout.addWidget(QLabel("Метрика:"))
        top_layout.addWidget(self.metric_combo)

        layout.addLayout(top_layout)

        # Таблица результатов
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Место", "Пользователь", "Результат"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        # Кнопка назад
        back_btn = QPushButton("Назад в меню")
        back_btn.clicked.connect(self.back_to_menu)
        layout.addWidget(back_btn)

        self.setLayout(layout)

        # Начальная загрузка метрик
        self.on_scope_changed(0)  # глобальный по умолчанию

    def on_scope_changed(self, index):
        """Обновляет список метрик в зависимости от выбранного скоупа."""
        scope = "global" if index == 0 else "friends"
        # Получаем список активных категорий с нужным скоупом
        from database.models.gamification import LeaderboardCategory
        categories = self.db.query(LeaderboardCategory).filter(
            LeaderboardCategory.is_active == True,
            LeaderboardCategory.scope == scope
        ).all()

        self.metric_combo.clear()
        self.category_ids = []
        for cat in categories:
            self.metric_combo.addItem(cat.name, cat.id)
            self.category_ids.append(cat.id)

        if categories:
            self.load_leaderboard()

    def load_leaderboard(self):
        """Загружает таблицу лидеров для выбранной категории."""
        if self.metric_combo.currentIndex() < 0:
            self.table.setRowCount(0)
            return

        category_id = self.metric_combo.currentData()
        if category_id is None:
            return
        # Получаем период начала (сегодня, неделя, месяц) – базовый запрос из сервиса
        # Для простоты используем прямой запрос, т.к. сервис может требовать доработки
        from database.models.gamification import LeaderboardEntry, LeaderboardCategory
        from database.models.user import User

        self.leaderboard_svc.ensure_user_entries(self.user.id)

        category = self.db.query(LeaderboardCategory).filter(
            LeaderboardCategory.id == category_id
        ).first()
        if not category:
            return

        # Определяем границы периода
        period_start = date.today()
        if category.reset_period == 'weekly':
            period_start = period_start - timedelta(days=period_start.weekday())
        elif category.reset_period == 'monthly':
            period_start = period_start.replace(day=1)
        elif category.reset_period == 'daily':
            period_start = period_start
        else:
            period_start = date(2000, 1, 1)  # для "never" берём все

        # Базовый запрос записей
        query = self.db.query(LeaderboardEntry).filter(
            LeaderboardEntry.category_id == category_id,
            LeaderboardEntry.period_start == period_start
        )

        # Если скоуп "friends" – фильтруем по друзьям
        if self.scope_combo.currentIndex() == 1:
            friends = self.friends_svc.get_friends(self.user.id)
            friend_ids = [f.id for f in friends] + [self.user.id]  # включаем себя
            query = query.filter(LeaderboardEntry.user_id.in_(friend_ids))

        entries = query.order_by(LeaderboardEntry.score.desc()).all()

        self.table.setRowCount(len(entries))
        for i, entry in enumerate(entries):
            user = self.db.query(User).filter(User.id == entry.user_id).first()
            username = user.username if user else "Unknown"

            rank_item = QTableWidgetItem(str(i + 1))
            rank_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            name_item = QTableWidgetItem(username)
            score_item = QTableWidgetItem(str(entry.score))

            self.table.setItem(i, 0, rank_item)
            self.table.setItem(i, 1, name_item)
            self.table.setItem(i, 2, score_item)

    def back_to_menu(self):
        from gui.windows.main_window import MainMenuWindow
        self.menu = MainMenuWindow(self.user, self.db)
        self.menu.show()
        self.close()