# gui/styles/theme_manager.py
import os
from PyQt6.QtWidgets import QApplication
from sqlalchemy.orm import Session
from services.shop_service import ShopService

THEMES = {
    "classic": "gui/styles/themes/classic.qss",
    "acid_yellow": "gui/styles/themes/acid_yellow.qss",
    "neon_blue": "gui/styles/themes/neon_blue.qss",
    "dark_reactive": "gui/styles/themes/dark_reactive.qss",
}

def _read_stylesheet(filename: str) -> str:
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()

def apply_theme(theme_name: str) -> None:
    """Применить QSS-тему глобально ко всему приложению."""
    app = QApplication.instance()
    if app is None:
        return
    if theme_name not in THEMES:
        theme_name = "classic"  # fallback
    path = os.path.join(os.path.dirname(__file__), "themes", f"{theme_name}.qss")
    if not os.path.exists(path):
        path = os.path.join(os.path.dirname(__file__), "themes", "classic.qss")
    stylesheet = _read_stylesheet(path)
    app.setStyleSheet(stylesheet)

def get_user_theme(user_id, db: Session) -> str:
    """Определяет активную тему пользователя."""
    shop = ShopService(db)
    equipped = shop.get_equipped_theme(user_id)
    if equipped:
        # Предположим, что название предмета совпадает с ключом темы (например, "Кислотный жёлтый" -> "acid_yellow")
        name = equipped.item_type.name
        mapping = {
            "Классическая": "classic",
            "Кислотный жёлтый": "acid_yellow",
            "Неоновый синий": "neon_blue",
            "Тёмный реактив": "dark_reactive",
        }
        return mapping.get(name, "classic")
    return "classic"