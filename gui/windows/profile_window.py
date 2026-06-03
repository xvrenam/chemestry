from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
import os
from services.currency_service import CurrencyService
from services.shop_service import ShopService
from services.achievement_service import AchievementService  # нужно добавить метод get_user_achievements

class ProfileWindow(QWidget):
    def __init__(self, user, db_session):
        super().__init__()
        self.user = user
        self.db = db_session
        self.shop_svc = ShopService(self.db)
        self.ach_svc = AchievementService(self.db)
        self.setWindowTitle("Профиль")
        self.setFixedSize(700, 700)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        # Верхняя панель
        top = QHBoxLayout()
        back_btn = QPushButton("Меню")
        back_btn.clicked.connect(self.back_to_menu)
        friends_btn = QPushButton("Друзья")
        friends_btn.clicked.connect(self.open_friends)
        store_btn = QPushButton("Магазин")
        store_btn.clicked.connect(self.open_store)
        settings_btn = QPushButton("Настроить профиль")
        settings_btn.clicked.connect(self.open_settings)
        top.addWidget(back_btn)
        top.addStretch()
        top.addWidget(friends_btn)
        top.addWidget(store_btn)
        top.addWidget(settings_btn)
        layout.addLayout(top)

        # Аватар
        avatar_label = QLabel()
        avatar_inv = self.shop_svc.get_equipped_avatar(self.user.id)
        if avatar_inv and avatar_inv.item_type.icon_url:
            pix = QPixmap(avatar_inv.item_type.icon_url)
        else:
            pix = QPixmap("C:\\0.0.Diploma2\\profile.png")
        avatar_label.setPixmap(pix.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(avatar_label)

        username = QLabel(self.user.username)
        username.setAlignment(Qt.AlignmentFlag.AlignCenter)
        username.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(username)

        # Валюта
        curr_svc = CurrencyService(self.db)
        wallet = curr_svc.get_or_create_wallet(self.user.id)
        currency_label = QLabel(f"Монеты: {wallet.coins}  Кристаллы: {wallet.crystals}")
        currency_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(currency_label)

        # Витрина (горизонтальный скролл)
        layout.addWidget(QLabel("Моя витрина"))
        showcase_container = self.create_showcase_display()
        layout.addWidget(showcase_container)

        # Достижения
        layout.addWidget(QLabel("Достижения"))
        ach_scroll = self.create_achievements_display()
        layout.addWidget(ach_scroll)

        self.setLayout(layout)

    def create_showcase_display(self):
        """Отображает активную витрину с размещёнными артефактами."""
        widget = QWidget()
        layout = QHBoxLayout()
        active = self.shop_svc.get_active_showcase(self.user.id)
        if not active:
            layout.addWidget(QLabel("Нет активной витрины. Купите и выберите в настройках."))
            widget.setLayout(layout)
            return widget

        capacity = active.item_type.capacity
        slots = self.shop_svc.get_showcase_slots(self.user.id)
        # Рисуем витрину как рамку с иконками артефактов в слотах
        # Для простоты используем горизонтальный ряд квадратов
        for slot_num in range(1, capacity+1):
            slot_widget = QWidget()
            slot_layout = QVBoxLayout()
            slot_widget.setFixedSize(80, 80)
            slot_widget.setStyleSheet("border: 1px solid;")
            if slot_num in slots:
                art_inv = slots[slot_num]
                icon_label = QLabel()
                pix = QPixmap(art_inv.item_type.icon_url) if os.path.exists(art_inv.item_type.icon_url) else QPixmap()
                if pix.isNull():
                    # Заглушка: цветной круг с буквой
                    icon_label.setText(art_inv.item_type.name[0])
                    icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    icon_label.setStyleSheet("font-size: 20px; color: white;")
                else:
                    icon_label.setPixmap(pix.scaled(70, 70, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                slot_layout.addWidget(icon_label)
            else:
                slot_layout.addWidget(QLabel("Пусто"), alignment=Qt.AlignmentFlag.AlignCenter)
            slot_widget.setLayout(slot_layout)
            layout.addWidget(slot_widget)
        widget.setLayout(layout)
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(120)
        return scroll

    def create_achievements_display(self):
        """Отображает достижения, отмеченные для показа в профиле."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(100)
        container = QWidget()
        h_layout = QHBoxLayout()
        user_achievements = self.ach_svc.get_user_achievements(self.user.id)
        displayed = [ua for ua in user_achievements if ua.is_displayed]
        if not displayed:
            h_layout.addWidget(QLabel("Нет достижений для отображения."))
        else:
            for ua in displayed:
                frame = QFrame()
                frame.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
                frame.setMinimumHeight(70)
                frame.setMaximumWidth(200)
                frame.setStyleSheet("border: 2px solid #81C784;")
                lbl = QLabel(ua.achievement.name)
                lbl.setWordWrap(True)
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                f_layout = QVBoxLayout(frame)
                f_layout.addWidget(lbl)
                h_layout.addWidget(frame)
        container.setLayout(h_layout)
        scroll.setWidget(container)
        return scroll
    
    def open_settings(self):
        from gui.windows.profile_settings_window import ProfileSettingsWindow
        self.settings_win = ProfileSettingsWindow(self.user, self.db)
        self.settings_win.show()
        self.close()
    
    def open_store(self):
        from gui.windows.store_window import StoreWindow
        self.store = StoreWindow(self.user, self.db)
        self.store.show()
        self.close()

    def back_to_menu(self):
        from gui.windows.main_window import MainMenuWindow
        self.menu = MainMenuWindow(self.user, self.db)
        self.menu.show()
        self.close()

    def open_friends(self):
        from gui.windows.friends_window import FriendsWindow
        self.friends_win = FriendsWindow(self.user, self.db)
        self.friends_win.show()
        self.close()