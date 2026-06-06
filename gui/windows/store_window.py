from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, QGridLayout, QMessageBox, QTabWidget, QListWidget, QListWidgetItem, QHBoxLayout
from PyQt6.QtGui import QPixmap, QIcon, QColor
from PyQt6.QtCore import QSize, Qt
from gui.windows.base_window import BaseWindow
from services.shop_service import ShopService
import os
from basedir import resource_path

class StoreWindow(BaseWindow):   # наследник BaseWindow – уже должно быть
    def __init__(self, user, db_session):
        super().__init__("store")
        self.user = user
        self.db = db_session
        self.shop_svc = ShopService(self.db)
        self.setWindowTitle("Магазин")
        self.setMinimumSize(700, 550)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        title = QLabel("Магазин предметов")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        self.tabs = QTabWidget()
        # Категории: ("Все", None), ("Аватары", "avatar"), ("Витрины", "showcase"),
        # ("Темы", "profile_theme"), ("Артефакты", "artifact")
        categories = [("Все", None), ("Аватары", "avatar"), ("Витрины", "showcase"),
                      ("Темы", "profile_theme"), ("Артефакты", "artifact")]
        self.tab_widgets = {}  # словарь {category_code: QListWidget}
        for cat_name, cat_code in categories:
            list_widget = QListWidget()
            list_widget.setViewMode(QListWidget.ViewMode.IconMode)
            list_widget.setIconSize(QSize(64, 64))
            list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
            list_widget.itemDoubleClicked.connect(self.buy_item)
            # сохраняем категорию для каждого list widget
            list_widget.category_code = cat_code
            self.tabs.addTab(list_widget, cat_name)
            self.tab_widgets[cat_code] = list_widget
        layout.addWidget(self.tabs)

        back_btn = QPushButton("Назад в профиль")
        back_btn.clicked.connect(self.back_to_profile)
        layout.addWidget(back_btn)
        self.setLayout(layout)

        self.refresh_all_tabs()

    def refresh_all_tabs(self):
        """Обновляет все вкладки магазина."""
        for cat_code, list_widget in self.tab_widgets.items():
            self.populate_tab(list_widget, cat_code)

    def populate_tab(self, list_widget, category_code):
        """Заполняет QListWidget товарами, доступными для покупки."""
        list_widget.clear()
        if category_code is None:
            items = self.shop_svc.get_purchasable_items(self.user.id)
        else:
            items = self.shop_svc.get_purchasable_items(self.user.id, category_code)

        if not items:
            # Добавляем информационный пункт (неактивный)
            msg_item = QListWidgetItem("🏆 Вы купили все предметы в этой категории!")
            msg_item.setFlags(msg_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)  # нельзя выбрать
            msg_item.setForeground(QColor(100, 100, 100))
            list_widget.addItem(msg_item)
            return

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
            list_widget.addItem(list_item)

    def buy_item(self, item):
        """Покупка и последующее обновление вкладок."""
        shop_item_id = item.data(Qt.ItemDataRole.UserRole)
        success = self.shop_svc.purchase_item(self.user.id, shop_item_id)
        if success:
            QMessageBox.information(self, "Успех", "Предмет куплен!")
            # Обновляем все вкладки, чтобы купленный предмет исчез
            self.refresh_all_tabs()
        else:
            QMessageBox.warning(self, "Ошибка", "Недостаточно средств.")

    def get_icon(self, url: str) -> QIcon:
        """Загружает иконку, используя resource_path."""
        if not url:
            pix = QPixmap(64, 64)
            pix.fill(QColor(100, 100, 100))
            return QIcon(pix)

        abs_path = resource_path(url)
        if not os.path.exists(abs_path):
            pix = QPixmap(64, 64)
            pix.fill(QColor(200, 0, 0))
            return QIcon(pix)

        pix = QPixmap(abs_path)
        pix = pix.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        if pix.isNull():
            pix = QPixmap(64, 64)
            pix.fill(QColor(200, 200, 0))
        return QIcon(pix)

    def back_to_profile(self):
        from gui.windows.profile_window import ProfileWindow
        geo = self.geometry()
        self.close()
        self.profile = ProfileWindow(self.user, self.db)
        self.profile.setGeometry(geo)
        self.profile.show()