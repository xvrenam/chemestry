from services.friends_service import FriendsService

from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QLineEdit,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QFrame,
    QMessageBox
)

from PyQt6.QtCore import Qt
from gui.windows.base_window import BaseWindow


class FriendsWindow(BaseWindow):

    def __init__(self, user, db_session):
        super().__init__("friends")

        self.user = user
        self.session = db_session

        self.setWindowTitle("Интерактивная химия | Друзья")
        self.setMinimumSize(500, 400)

        self.init_ui()

    def init_ui(self):

        main_layout = QVBoxLayout()

        # ---- верхняя панель ----

        top_layout = QHBoxLayout()

        back_button = QPushButton("Назад")
        back_button.clicked.connect(self.back_to_profile)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск друзей...")
        self.search_input.setFixedWidth(250)

        request_button = QPushButton("Отравить запрос")
        request_button.clicked.connect(self.send_request)

        top_layout.addWidget(back_button)
        top_layout.addStretch()
        top_layout.addWidget(self.search_input)
        top_layout.addStretch()
        top_layout.addWidget(request_button)
        top_layout.addStretch()

        # ---- список друзей ----

        friends_title = QLabel("Друзья")
        friends_title.setStyleSheet("font-size: 16px; font-weight: bold;")

        self.friends_scroll = self.create_friends_scroll()

        # ---- заявки ----

        requests_title = QLabel("Заявки в друзья")
        requests_title.setStyleSheet("font-size: 14px;")

        self.requests_scroll = self.create_requests_scroll()

        # ---- сборка ----

        main_layout.addLayout(top_layout)

        main_layout.addSpacing(10)

        main_layout.addWidget(friends_title)
        main_layout.addWidget(self.friends_scroll)

        main_layout.addSpacing(10)

        main_layout.addWidget(requests_title)
        main_layout.addWidget(self.requests_scroll)

        self.setLayout(main_layout)

    # ---- скролл друзей ----

    def create_friends_scroll(self):

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        layout = QVBoxLayout()

        # друзья
        friends = FriendsService.get_friends(self.user.id)
        for friend in friends:

            friend_frame = QFrame()
            friend_frame.setStyleSheet("""
                border: 1px solid;
            """)
            friend_frame.setFixedHeight(40)

            label = QLabel(friend.username)

            remove_button = QPushButton("Удалить")

            remove_button.clicked.connect(
                lambda _, u=friend: self.remove_friend(u)
            )

            row = QHBoxLayout()
            row.addWidget(label)
            row.addStretch()
            row.addWidget(remove_button)

            friend_frame.setLayout(row)

            layout.addWidget(friend_frame)

        layout.addStretch()

        container.setLayout(layout)
        scroll.setWidget(container)

        return scroll

    # ---- скролл заявок ----

    def create_requests_scroll(self):

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(120)

        container = QWidget()
        layout = QVBoxLayout()

        # заявки
        requests = FriendsService.get_requests(self.user.id)
        for request in requests:

            request_frame = QFrame()
            request_frame.setStyleSheet("""
                border: 1px solid;
            """)
            request_frame.setFixedHeight(40)

            name = QLabel(f"Заявка от {request.username}")

            accept = QPushButton("✔")
            decline = QPushButton("✖")
            accept.clicked.connect(
                lambda _, u=request.id: self.handle_accept(u)
            )

            decline.clicked.connect(
                lambda _, u=request.id: self.handle_decline(u)
            )

            row = QHBoxLayout()
            row.addWidget(name)
            row.addStretch()
            row.addWidget(accept)
            row.addWidget(decline)

            request_frame.setLayout(row)

            layout.addWidget(request_frame)

        layout.addStretch()

        container.setLayout(layout)
        scroll.setWidget(container)

        return scroll

    # ---- кнопка назад ----

    def back_to_profile(self):
        from gui.windows.profile_window import ProfileWindow
        current_geo = self.geometry()
        self.close()
        self.profile = ProfileWindow(self.user, self.session)
        self.profile.setGeometry(current_geo)
        self.profile.show()

    def send_request(self):
        username = self.search_input.text()

        success, message = FriendsService.send_request(
            self.user.id,
            username
        )

        if success:
            QMessageBox.information(self, "Успех", message)
        else:
            QMessageBox.warning(self, "Ошибка", message)

    def remove_friend(self, friend):
        success, message = FriendsService.remove_friend(
            self.user.id,
            friend.id
        )

        if success:
            QMessageBox.information(self, "Успех", message)
            self.reload_friends()
        else:
            QMessageBox.warning(self, "Ошибка", message)

    def reload_friends(self):
        new_scroll = self.create_friends_scroll()

        self.layout().replaceWidget(self.friends_scroll, new_scroll)
        self.friends_scroll.deleteLater()

        self.friends_scroll = new_scroll


    def reload_requests(self):
        new_scroll = self.create_requests_scroll()

        self.layout().replaceWidget(self.requests_scroll, new_scroll)
        self.requests_scroll.deleteLater()

        self.requests_scroll = new_scroll

    def handle_accept(self, requester_id):
        success, message = FriendsService.accept_request(self.user.id, requester_id)

        if success:
            QMessageBox.information(self, "Успех", message)
            self.reload_requests()
            self.reload_friends()
        else:
            QMessageBox.warning(self, "Ошибка", message)

    def handle_decline(self, requester_id):
        success, message = FriendsService.decline_request(self.user.id, requester_id)

        if success:
            QMessageBox.information(self, "Успех", message)
            self.reload_requests()
        else:
            QMessageBox.warning(self, "Ошибка", message)