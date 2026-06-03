import sys

from PyQt6.QtWidgets import QApplication

from database.init_db import init_db
from database.seed import seed_data
from database.db import SessionLocal
from gui.styles.theme_manager import apply_theme

from gui.windows.login_window import LoginWindow


def main():
    init_db()
    seed_data()
    
    app = QApplication(sys.argv)

    apply_theme('classic')

    db_session = SessionLocal()

    window = LoginWindow(db_session=db_session)
    window.show()

    exit_code = app.exec()
    db_session.close()  # закрываем сессию при выходе
    sys.exit(exit_code)


if __name__ == "__main__":
    main()