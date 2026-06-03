from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QMessageBox
)

from PyQt6.QtCore import Qt

from services.auth_service import AuthService

import re
import dns.resolver

def validate_email(email: str) -> bool:
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    if not re.match(pattern, email):
        return False

    domain = email.split("@")[1]
    try:
        dns.resolver.resolve(domain, "MX")
        return True
    except:
        if domain in ['mail.ru', 'yandex.ru', 'list.ru', 'gmail.com']:
            return True
        return False

class RegisterWindow(QWidget):

    def __init__(self, db_session):
        super().__init__()
        self.db_session = db_session

        self.setWindowTitle("Интерактивная химия | Регистрация")
        self.setFixedSize(400, 350)

        self.init_ui()

    def init_ui(self):

        layout = QVBoxLayout()
        layout.setSpacing(15)

        title = QLabel("Регистрация")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Имя пользователя")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Повторите пароль")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)

        register_button = QPushButton("Зарегистрироваться")
        register_button.clicked.connect(self.register)

        back_button = QPushButton("Вернутся ко входу")
        back_button.setFlat(True)
        back_button.clicked.connect(self.back_to_login)

        layout.addWidget(title)
        layout.addWidget(self.username_input)
        layout.addWidget(self.email_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.confirm_password_input)
        layout.addWidget(register_button)
        layout.addWidget(back_button)

        layout.addStretch()

        self.setLayout(layout)

    def register(self):
        username = self.username_input.text()
        email = self.email_input.text()
        password = self.password_input.text()

        if self.password_input.text() != self.confirm_password_input.text():
            success, message = False, "Пароли не совпадают"

        elif not validate_email(self.email_input.text()):
            success, message = False, "Введите корректный email"
        
        else:
            success, message = AuthService.register(username, email, password)

        if success:
            from gui.windows.login_window import LoginWindow
            QMessageBox.information(self, "Success", message)
            self.login_window = LoginWindow(db_session=self.db_session)
            self.login_window.show()
            self.close()

        else:
            QMessageBox.warning(self, "Error", message)

    def back_to_login(self):
        from gui.windows.login_window import LoginWindow
        self.login_window = LoginWindow(db_session=self.db_session)
        self.login_window.show()
        self.close()