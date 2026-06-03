from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout
)

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon


class MainMenuWindow(QWidget):

    def __init__(self, user, db_session):
        super().__init__()

        self.user = user
        self.db_session = db_session

        self.setWindowTitle("Интерактивная химия | Главное меню")
        self.setFixedSize(500, 400)

        self.init_ui()

    def init_ui(self):

        main_layout = QVBoxLayout()

        top_layout = QHBoxLayout()
        top_layout.addStretch()

        profile_button = QPushButton("Профиль")
        profile_button.setIcon(QIcon("C:\\0.0.Diploma2\\profile.png"))
        profile_button.setIconSize(QSize(32,32))
        profile_button.clicked.connect(self.open_profile)

        top_layout.addWidget(profile_button)

        title = QLabel("Интерактивная химия")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 26px; font-weight: bold;")

        menu_layout = QVBoxLayout()
        menu_layout.setSpacing(15)

        learn_button = QPushButton("Учиться")
        learn_button.clicked.connect(self.open_learning)


        leaderboard_button = QPushButton("Доска почёта")
        leaderboard_button.clicked.connect(self.open_leaderboard)

        exit_button = QPushButton("Выход")
        exit_button.clicked.connect(self.logout)

        menu_layout.addWidget(learn_button)
        menu_layout.addWidget(leaderboard_button)
        menu_layout.addWidget(exit_button)

        main_layout.addLayout(top_layout)
        main_layout.addStretch()

        main_layout.addWidget(title)

        main_layout.addSpacing(20)
        main_layout.addLayout(menu_layout)

        main_layout.addStretch()

        self.setLayout(main_layout)

    def open_profile(self):
        from gui.windows.profile_window import ProfileWindow
        self.profile_window = ProfileWindow(self.user, self.db_session)
        self.profile_window.show()
        self.close()

    def open_learning(self):
        from gui.windows.track_selection_window import TrackSelectionWindow
        self.learning_window = TrackSelectionWindow(self.user, self.db_session)
        self.learning_window.show()
        self.close()

    def open_leaderboard(self):
        from gui.windows.leaderboard_window import LeaderboardWindow
        self.leaderboard_window = LeaderboardWindow(self.user, self.db_session)
        self.leaderboard_window.show()
        self.close()

    def logout(self):
        from gui.windows.login_window import LoginWindow
        self.login_window = LoginWindow(self.db_session)
        self.login_window.show()
        self.close()