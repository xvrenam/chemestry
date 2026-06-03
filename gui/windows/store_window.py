from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, QGridLayout, QMessageBox, QTabWidget, QListWidget, QListWidgetItem, QHBoxLayout
from PyQt6.QtGui import QPixmap, QIcon, QColor
from PyQt6.QtCore import QSize
from PyQt6.QtCore import Qt
from services.shop_service import ShopService
import os
import sys
from basedir import resource_path

class StoreWindow(QWidget):
    def __init__(self, user, db_session):
        super().__init__()
        self.user = user
        self.db = db_session
        self.shop_svc = ShopService(self.db)
        self.setWindowTitle("Магазин")
        self.setFixedSize(700, 550)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        title = QLabel("Магазин предметов")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        # Вкладки по категориям
        tabs = QTabWidget()
        categories = [("Все", None), ("Аватары", "avatar"), ("Витрины", "showcase"),
                      ("Темы", "profile_theme"), ("Артефакты", "artifact")]
        for cat_name, cat_code in categories:
            widget = QListWidget()
            widget.setViewMode(QListWidget.ViewMode.IconMode)
            widget.setIconSize(QSize(64, 64))
            widget.setResizeMode(QListWidget.ResizeMode.Adjust)
            widget.setDragEnabled(False)
            items = self.shop_svc.get_available_items() if cat_code is None else self.shop_svc.get_items_by_category(cat_code)
            for shop_item in items:
                item_type = shop_item.item_type
                icon = self.get_icon(item_type.icon_url)
                text = f"{item_type.name}\n"
                if shop_item.price_coins:
                    text += f"💰{shop_item.price_coins} "
                if shop_item.price_crystals:
                    text += f"💎{shop_item.price_crystals}"
                list_item = QListWidgetItem()
                list_item.setData(Qt.ItemDataRole.UserRole, shop_item.id)
                list_item.setText(text)
                list_item.setIcon(icon)
                widget.addItem(list_item)
            widget.itemDoubleClicked.connect(self.buy_item)
            tabs.addTab(widget, cat_name)

        layout.addWidget(tabs)

        back_btn = QPushButton("Назад в профиль")
        back_btn.clicked.connect(self.back_to_profile)
        layout.addWidget(back_btn)
        self.setLayout(layout)

    def get_icon(self, url: str) -> QIcon:
        """Создаёт QIcon с отладочной проверкой и заглушкой при ошибке."""
        if not url:
            # Заглушка – серый квадрат
            pix = QPixmap(64, 64)
            pix.fill(QColor(100, 100, 100))
            return QIcon(pix)

        abs_path = resource_path(url)
        if not os.path.exists(abs_path):
            print(f"DEBUG: Файл не найден: {abs_path}")
            pix = QPixmap(64, 64)
            pix.fill(QColor(200, 0, 0))  # красный квадрат для отсутствующей иконки
            return QIcon(pix)

        pix = QPixmap(abs_path)
        pix = pix.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        if pix.isNull():
            print(f"DEBUG: QPixmap не загрузился: {abs_path}")
            pix = QPixmap(64, 64)
            pix.fill(QColor(200, 200, 0))  # жёлтый – ошибка чтения

        return QIcon(pix)

    def buy_item(self, item):
        shop_item_id = item.data(Qt.ItemDataRole.UserRole)
        success = self.shop_svc.purchase_item(self.user.id, shop_item_id)
        if success:
            QMessageBox.information(self, "Успех", "Предмет куплен!")
        else:
            QMessageBox.warning(self, "Ошибка", "Недостаточно средств.")

    def back_to_profile(self):
        from gui.windows.profile_window import ProfileWindow
        self.profile = ProfileWindow(self.user, self.db)
        self.profile.show()
        self.close()