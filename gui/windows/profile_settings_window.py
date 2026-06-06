from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QHBoxLayout, QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt
from gui.windows.base_window import BaseWindow
from services.shop_service import ShopService
from services.achievement_service import AchievementService
from database.models.user import ItemType

class ProfileSettingsWindow(BaseWindow):
    def __init__(self, user, db_session):
        super().__init__("profile_settings")
        self.user = user
        self.db = db_session
        self.shop_svc = ShopService(self.db)
        self.ach_svc = AchievementService(self.db)
        self.setWindowTitle("Настройки профиля")
        self.setMinimumSize(500, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        tabs = QTabWidget()

        # Вкладка Аватар
        avatar_widget = self.create_avatar_tab()
        tabs.addTab(avatar_widget, "Аватар")

        # Вкладка Тема
        theme_widget = self.create_theme_tab()
        tabs.addTab(theme_widget, "Тема")

        # Вкладка Витрина
        showcase_widget = self.create_showcase_tab()
        tabs.addTab(showcase_widget, "Витрина")

        # Вкладка Достижения
        achievements_widget = self.create_achievements_tab()
        tabs.addTab(achievements_widget, "Достижения")

        layout.addWidget(tabs)

        back_btn = QPushButton("Назад в профиль")
        back_btn.clicked.connect(self.back_to_profile)
        layout.addWidget(back_btn)
        self.setLayout(layout)

    def create_avatar_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Выберите аватар из вашего инвентаря:"))
        list_widget = QListWidget()
        inventory = self.shop_svc.get_inventory(self.user.id)
        equipped_avatar = self.shop_svc.get_equipped_avatar(self.user.id)
        for inv in inventory:
            if inv.item_type.category != 'avatar':
                continue
            item = QListWidgetItem(inv.item_type.name)
            item.setData(Qt.ItemDataRole.UserRole, inv.id)
            if equipped_avatar and inv.id == equipped_avatar.id:
                item.setSelected(True)
            list_widget.addItem(item)
        list_widget.itemClicked.connect(self.equip_avatar)
        layout.addWidget(list_widget)
        widget.setLayout(layout)
        return widget

    def equip_avatar(self, item):
        inv_id = item.data(Qt.ItemDataRole.UserRole)
        self.shop_svc.equip_item(self.user.id, inv_id)
        QMessageBox.information(self, "Аватар", "Аватар обновлён!")

    def create_theme_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Выберите тему профиля:"))

        # 1. Гарантируем, что классическая тема есть у пользователя
        classic_theme = self.db.query(ItemType).filter(ItemType.name == "Классическая").first()
        if classic_theme:
            from database.models.user import UserInventory
            existing = self.db.query(UserInventory).filter(
                UserInventory.user_id == self.user.id,
                UserInventory.item_type_id == classic_theme.id
            ).first()
            if not existing:
                self.shop_svc.add_item_to_inventory(self.user.id, classic_theme.id)

        # 2. Получаем актуальный инвентарь и показываем список
        inventory = self.shop_svc.get_inventory(self.user.id)
        equipped_theme = self.shop_svc.get_equipped_theme(self.user.id)

        list_widget = QListWidget()
        for inv in inventory:
            if inv.item_type.category != 'profile_theme':
                continue
            item = QListWidgetItem(inv.item_type.name)
            item.setData(1, inv.id)
            if equipped_theme and inv.id == equipped_theme.id:
                item.setSelected(True)
            list_widget.addItem(item)
        list_widget.itemClicked.connect(self.equip_theme)
        layout.addWidget(list_widget)
        widget.setLayout(layout)
        return widget

    def equip_theme(self, item):
        inv_id = item.data(1)
        self.shop_svc.equip_item(self.user.id, inv_id)
        from gui.styles.theme_manager import apply_theme, get_user_theme
        theme = get_user_theme(self.user.id, self.db)
        apply_theme(theme)
        QMessageBox.information(self, "Тема", "Тема обновлена!")

    def create_showcase_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Управление витриной"))

        # Выбор активной витрины
        layout.addWidget(QLabel("Активная витрина:"))
        self.showcase_combo = QComboBox()
        self.showcase_combo.addItem('Без витрины', None)
        inventory = self.shop_svc.get_inventory(self.user.id)
        self.showcase_ids = []
        for inv in inventory:
            if inv.item_type.category == 'showcase':
                self.showcase_combo.addItem(f"{inv.item_type.name} (вместимость {inv.item_type.capacity})", inv.id)
                self.showcase_ids.append(inv.id)
        active = self.shop_svc.get_active_showcase(self.user.id)
        if active:
            # ИСПРАВЛЕНО: учитываем первый пункт "Без витрины"
            if active.id in self.showcase_ids:
                idx = self.showcase_ids.index(active.id) + 1
            else:
                idx = 0
            self.showcase_combo.setCurrentIndex(idx)
        else:
            self.showcase_combo.setCurrentIndex(0)
        self.showcase_combo.currentIndexChanged.connect(self.on_showcase_changed)
        layout.addWidget(self.showcase_combo)

        # Слоты витрины
        layout.addWidget(QLabel("Заполнение слотов:"))
        self.slots_layout = QVBoxLayout()
        layout.addLayout(self.slots_layout)
        self.refresh_slots()

        widget.setLayout(layout)
        return widget

    def on_showcase_changed(self):
        if self.showcase_combo.currentIndex() < 0:
            return
        inv_id = self.showcase_combo.currentData()
        if inv_id is None:
            self.shop_svc.unequip_showcase(self.user.id)
            self.refresh_slots()
            QMessageBox.information(self, "Витрина", "Витрина снята")
            return
        success, msg = self.shop_svc.equip_item(self.user.id, inv_id)
        if success:
            self.refresh_slots()
            QMessageBox.information(self, "Витрина", "Витрина выбрана")
        else:
            QMessageBox.warning(self, "Ошибка", msg)

    def refresh_slots(self):
        # Очищаем текущие виджеты слотов
        while self.slots_layout.count():
            child = self.slots_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        active = self.shop_svc.get_active_showcase(self.user.id)
        if not active:
            self.slots_layout.addWidget(QLabel("Нет активной витрины"))
            return

        capacity = active.item_type.capacity
        slots = self.shop_svc.get_showcase_slots(self.user.id)
        inventory = self.shop_svc.get_inventory(self.user.id)

        for slot_num in range(1, capacity + 1):
            # ИСПРАВЛЕНО: строим список артефактов для этого слота
            # включаем артефакт, который сейчас стоит в этом слоте (даже если equipped=True),
            # но исключаем артефакты, уже занятые в ДРУГИХ слотах
            current_artifact = slots.get(slot_num)
            current_art_id = current_artifact.id if current_artifact else None
            artifacts_for_slot = []
            for inv in inventory:
                if inv.item_type.category != 'artifact':
                    continue
                # Если это текущий артефакт слота — включаем всегда
                if inv.id == current_art_id:
                    artifacts_for_slot.append(inv)
                # Иначе включаем только не экипированные
                elif not inv.is_equipped:
                    artifacts_for_slot.append(inv)

            slot_widget = QWidget()
            slot_layout = QHBoxLayout()
            slot_layout.addWidget(QLabel(f"Слот {slot_num}:"))

            combo = QComboBox()
            combo.addItem("Пусто", None)
            selected_idx = 0
            for i, art in enumerate(artifacts_for_slot):
                combo.addItem(art.item_type.name, art.id)
                if art.id == current_art_id:
                    selected_idx = i + 1
            combo.setCurrentIndex(selected_idx)

            # Захват переменных для лямбды осуществляется через аргументы по умолчанию
            combo.currentIndexChanged.connect(
                lambda idx, s=slot_num, c=combo: self.place_artifact(s, c)
            )
            slot_layout.addWidget(combo)
            slot_widget.setLayout(slot_layout)
            self.slots_layout.addWidget(slot_widget)

    def place_artifact(self, slot, combo):
        inv_id = combo.currentData()
        if inv_id is not None:
            success, msg = self.shop_svc.place_artifact_in_slot(self.user.id, inv_id, slot)
            if not success:
                QMessageBox.warning(self, "Ошибка", msg)
            else:
                QMessageBox.information(self, "Витрина", "Артефакт размещён")
                self.refresh_slots()
        else:
            # Если выбран "Пусто" — убрать артефакт из слота (предполагаем, что метод поддерживает это)
            self.shop_svc.remove_artifact_from_slot(self.user.id, slot)
            self.refresh_slots()
            QMessageBox.information(self, "Витрина", "Артефакт убран")
            return

    def create_achievements_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Отметьте достижения, которые будут видны в профиле:"))
        user_achievements = self.ach_svc.get_user_achievements(self.user.id)
        if not user_achievements:
            layout.addWidget(QLabel("У вас пока нет достижений."))
        for ua in user_achievements:
            cb = QPushButton(f"{ua.achievement.name} {'✅' if ua.is_displayed else '❌'}")
            cb.setCheckable(True)
            cb.setChecked(ua.is_displayed)
            cb.ua_id = ua.id
            cb.achievement_name = ua.achievement.name
            cb.clicked.connect(lambda checked, cb=cb: self.toggle_achievement_display(cb, checked))
            layout.addWidget(cb)
        widget.setLayout(layout)
        return widget

    def toggle_achievement_display(self, button, checked):
        self.ach_svc.toggle_display(self.user.id, button.ua_id, checked)
        button.setText(f"{button.achievement_name} {'✅' if checked else '❌'}")
        button.setChecked(checked)

    def back_to_profile(self):
        from gui.windows.profile_window import ProfileWindow
        current_geo = self.geometry()
        self.close()
        self.profile = ProfileWindow(self.user, self.db)
        self.profile.setGeometry(current_geo)
        self.profile.show()