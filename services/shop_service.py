from sqlalchemy.orm import Session, joinedload
from typing import Optional
from database.models.user import UserInventory, ShopItem, UserShowcase, ItemType
import uuid

class ShopService:
    def __init__(self, db: Session):
        self.db = db

    def get_available_items(self):
        return self.db.query(ShopItem).filter(ShopItem.is_active == True).all()

    def purchase_item(self, user_id: uuid.UUID, shop_item_id: int) -> bool:
        from services.currency_service import CurrencyService
        item = self.db.query(ShopItem).filter(ShopItem.id == shop_item_id).first()
        if not item:
            return False
        curr_svc = CurrencyService(self.db)
        can_afford = curr_svc.spend(user_id, coins=item.price_coins or 0, crystals=item.price_crystals or 0)
        if can_afford:
            self.add_item_to_inventory(user_id, item.item_type_id)
            return True
        return False

    def add_item_to_inventory(self, user_id: uuid.UUID, item_type_id: int, quantity=1):
        existing = self.db.query(UserInventory).filter(
            UserInventory.user_id == user_id,
            UserInventory.item_type_id == item_type_id
        ).first()
        if existing:
            existing.quantity += quantity
        else:
            inv = UserInventory(user_id=user_id, item_type_id=item_type_id, quantity=quantity)
            self.db.add(inv)
        self.db.commit()

    def get_inventory(self, user_id: uuid.UUID):
        return self.db.query(UserInventory).filter(UserInventory.user_id == user_id).all()

    def place_in_showcase(self, user_id: uuid.UUID, inventory_id: int, slot_number: int, artifact_id: int = None):
        showcase = UserShowcase(
            user_id=user_id,
            showcase_item_id=inventory_id,
            slot_number=slot_number,
            artifact_item_id=artifact_id
        )
        self.db.add(showcase)
        self.db.commit()

    def get_items_by_category(self, category: str):
        """Возвращает ShopItem, отфильтрованные по категории item_type."""
        return self.db.query(ShopItem).join(ItemType).filter(
            ShopItem.is_active == True,
            ItemType.category == category
        ).all()

    def get_purchasable_items(self, user_id: uuid.UUID, category: str = None):
        """
        Возвращает список ShopItem, которые пользователь ещё не купил.
        Если указана category, фильтрует по ней.
        """
        from database.models.user import UserInventory
        # Подзапрос: item_type_id уже купленных пользователем предметов
        subq = self.db.query(UserInventory.item_type_id).filter(
            UserInventory.user_id == user_id
        ).subquery()
        query = self.db.query(ShopItem).filter(
            ShopItem.is_active == True,
            ~ShopItem.item_type_id.in_(subq)  # исключаем уже купленные
        )
        if category:
            query = query.join(ItemType).filter(ItemType.category == category)
        return query.all()

    def equip_item(self, user_id: uuid.UUID, inventory_id: int):
        # Загружаем предмет с подгрузкой item_type
        inv = self.db.query(UserInventory).options(joinedload(UserInventory.item_type)).filter(
            UserInventory.id == inventory_id, UserInventory.user_id == user_id
        ).first()
        if not inv:
            return False, "Предмет не найден в инвентаре"
        
        category = inv.item_type.category

        # Снимаем все экипированные предметы данной категории
        equipped = self.db.query(UserInventory).filter(
            UserInventory.user_id == user_id,
            UserInventory.is_equipped == True,
            UserInventory.item_type.has(category=category)
        ).all()
        for eq in equipped:
            eq.is_equipped = False
            eq.equipped_slot = None

        # Если это витрина – снимаем все артефакты и очищаем слоты
        if category == 'showcase':
            # Сбрасываем артефакты
            artifacts = self.db.query(UserInventory).filter(
                UserInventory.user_id == user_id,
                UserInventory.is_equipped == True,
                UserInventory.item_type.has(category='artifact')
            ).all()
            for art in artifacts:
                art.is_equipped = False
                art.equipped_slot = None
            
            # Удаляем все записи о слотах витрины, чтобы не оставалось мусора
            self.db.query(UserShowcase).filter(
                UserShowcase.user_id == user_id
            ).delete()

        # Экипируем выбранный предмет
        inv.is_equipped = True
        inv.equipped_slot = None  # витрина не имеет слота
        self.db.commit()
        return True, "Предмет экипирован"
    
    def remove_artifact_from_slot(self, user_id: uuid.UUID, slot: int):
        """Убирает артефакт из указанного слота активной витрины."""
        art = self.db.query(UserInventory).filter(
            UserInventory.user_id == user_id,
            UserInventory.is_equipped == True,
            UserInventory.equipped_slot == slot,
            UserInventory.item_type.has(category='artifact')
        ).first()
        if art:
            art.is_equipped = False
            art.equipped_slot = None
            self.db.commit()
            return True, "Артефакт удалён из слота"
        return False, "Слот пуст"

    def unequip_item(self, user_id: uuid.UUID, inventory_id: int):
        inv = self.db.query(UserInventory).filter(
            UserInventory.id == inventory_id, UserInventory.user_id == user_id
        ).first()
        if inv:
            inv.is_equipped = False
            inv.equipped_slot = None
            self.db.commit()

    def unequip_showcase(self, user_id: uuid.UUID):
        """Снимает активную витрину и очищает все связанные слоты."""
        showcase = self.get_active_showcase(user_id)
        if not showcase:
            return
        # Снимаем все артефакты, которые были в слотах
        artifacts = self.db.query(UserInventory).filter(
            UserInventory.user_id == user_id,
            UserInventory.is_equipped == True,
            UserInventory.item_type.has(category='artifact')
        ).all()
        for art in artifacts:
            art.is_equipped = False
            art.equipped_slot = None
        # Снимаем саму витрину
        showcase.is_equipped = False
        showcase.equipped_slot = None
        # Удаляем записи слотов витрины (при их наличии)
        self.db.query(UserShowcase).filter(UserShowcase.user_id == user_id).delete()
        self.db.commit()

    def get_equipped_avatar(self, user_id: uuid.UUID) -> Optional[UserInventory]:
        return self.db.query(UserInventory).filter(
            UserInventory.user_id == user_id,
            UserInventory.is_equipped == True,
            UserInventory.item_type.has(category='avatar')
        ).first()

    def get_equipped_theme(self, user_id: uuid.UUID) -> Optional[UserInventory]:
        return self.db.query(UserInventory).filter(
            UserInventory.user_id == user_id,
            UserInventory.is_equipped == True,
            UserInventory.item_type.has(category='profile_theme')
        ).first()

    def get_active_showcase(self, user_id: uuid.UUID) -> Optional[UserInventory]:
        return self.db.query(UserInventory).filter(
            UserInventory.user_id == user_id,
            UserInventory.is_equipped == True,
            UserInventory.item_type.has(category='showcase')
        ).first()

    def get_showcase_slots(self, user_id: uuid.UUID) -> dict:
        """Возвращает словарь {slot_number: UserInventory artifact} для активной витрины."""
        showcase = self.get_active_showcase(user_id)
        if not showcase:
            return {}
        artifacts = self.db.query(UserInventory).filter(
            UserInventory.user_id == user_id,
            UserInventory.is_equipped == True,
            UserInventory.item_type.has(category='artifact')
        ).all()
        slots = {}
        for art in artifacts:
            if art.equipped_slot is not None:
                slots[art.equipped_slot] = art
        return slots

    def place_artifact_in_slot(self, user_id: uuid.UUID, artifact_inventory_id: int, slot: int):
        """Размещает артефакт в слоте активной витрины."""
        showcase = self.get_active_showcase(user_id)
        if not showcase:
            return False, "Нет активной витрины"
        capacity = showcase.item_type.capacity
        if slot < 1 or slot > capacity:
            return False, "Неверный слот"
        # Проверяем, что артефакт в инвентаре и не экипирован
        art = self.db.query(UserInventory).filter(
            UserInventory.id == artifact_inventory_id, UserInventory.user_id == user_id,
            UserInventory.item_type.has(category='artifact')
        ).first()
        if not art:
            return False, "Артефакт не найден"
        if art.is_equipped and art.equipped_slot != slot:
            return False, "Артефакт уже размещён в другом слоте"
        # Убираем старый артефакт из этого слота
        old = self.db.query(UserInventory).filter(
            UserInventory.user_id == user_id,
            UserInventory.is_equipped == True,
            UserInventory.equipped_slot == slot,
            UserInventory.item_type.has(category='artifact')
        ).first()
        if old:
            old.is_equipped = False
            old.equipped_slot = None
        # Размещаем новый
        art.is_equipped = True
        art.equipped_slot = slot
        self.db.commit()
        return True, "Артефакт размещён"