# gui/windows/login_window.py

from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QMessageBox
)

from PyQt6.QtCore import Qt

from datetime import date, timedelta

from gui.windows.base_window import BaseWindow
from gui.windows.register_window import RegisterWindow
from gui.windows.main_window import MainMenuWindow
from services.auth_service import AuthService
from services.leaderboard_service import LeaderboardService
from gui.styles.theme_manager import apply_theme, get_user_theme

class LoginWindow(BaseWindow):

    def __init__(self, db_session):
        super().__init__("login")

        self.db_session = db_session

        self.setWindowTitle("Интерактивная химия | Вход")
        self.setMinimumSize(500, 400)

        self.init_ui()

    def init_ui(self):

        layout = QVBoxLayout()
        layout.setSpacing(15)

        title = QLabel("Вход")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Имя пользователя")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        login_button = QPushButton("Войти")
        login_button.clicked.connect(self.login)

        register_button = QPushButton("Регистрация")
        register_button.setFlat(True)
        register_button.clicked.connect(self.open_register)

        layout.addStretch()
        
        layout.addWidget(title)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(login_button)
        layout.addWidget(register_button)

        layout.addStretch()

        self.setLayout(layout)

    def open_register(self):
        current_geo = self.geometry()
        self.close()
        self.register_window = RegisterWindow(self.db_session)
        self.register_window.setGeometry(current_geo)
        self.register_window.show()

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        success, result = AuthService.login(username, password)

        if success:
            user = result
            today = date.today()
            if user.last_login_date:
                diff = (today - user.last_login_date).days
                if diff == 0:
                    pass  # уже заходил сегодня
                elif diff == 1:
                    user.current_streak += 1
                    user.longest_streak = max(user.longest_streak, user.current_streak)
                else:
                    user.current_streak = 1
            else:
                user.current_streak = 1
            user.last_login_date = today
            self.db_session.commit()

            lb_service = LeaderboardService(self.db_session)
            lb_service.ensure_user_entries(result.id)
            if result.current_streak:
                lb_service.update_entry(result.id, 'current_streak', result.current_streak)
            
            theme = get_user_theme(user.id, self.db_session)
            apply_theme(theme)

            current_geo = self.geometry()
            self.close()
            self.main_window = MainMenuWindow(result, self.db_session)
            self.main_window.setGeometry(current_geo)
            self.main_window.show()

        else:
            QMessageBox.warning(self, "Ошибка!", result)
            self.username_input.clear()
            self.password_input.clear()