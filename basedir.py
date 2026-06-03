import os
import sys

# Определяем корневую папку проекта (где лежит main.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def resource_path(relative_path: str) -> str:
    """Возвращает абсолютный путь к ресурсу. Работает и с PyInstaller."""
    if getattr(sys, 'frozen', False):
        # Если приложение собрано в exe
        base = sys._MEIPASS
    else:
        base = BASE_DIR
    return os.path.normpath(os.path.join(base, relative_path))