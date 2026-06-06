# gui/windows/base_window.py
from PyQt6.QtCore import QSettings, QPoint, QSize
from PyQt6.QtWidgets import QWidget, QApplication

class BaseWindow(QWidget):
    """
    Базовый класс для всех окон с сохранением геометрии (позиция и размер).
    """
    def __init__(self, settings_key: str, parent=None):
        super().__init__(parent)
        self.settings_key = settings_key
        self.setMinimumSize(400, 300)  # Минимальный размер, чтобы окно нельзя было сжать до нуля
        self.restore_geometry()

    def restore_geometry(self):
        """Восстанавливает геометрию окна из QSettings, если она есть."""
        settings = QSettings("InteractiveChemistry", "DiplomaProject")
        geometry = settings.value(f"{self.settings_key}/geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            # Размер по умолчанию для новых окон
            self.resize(800, 600)

    def closeEvent(self, event):
        """Сохраняет геометрию окна при закрытии."""
        settings = QSettings("InteractiveChemistry", "DiplomaProject")
        settings.setValue(f"{self.settings_key}/geometry", self.saveGeometry())
        super().closeEvent(event)