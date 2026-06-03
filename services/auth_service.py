import bcrypt
from database.db import SessionLocal
from database.models.user import User, UserInventory, ItemType
from services.shop_service import ShopService


class AuthService:

    @staticmethod
    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode(), salt)
        return hashed.decode()

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(password.encode(), hashed_password.encode())

    @staticmethod
    def register(username: str, email: str, password: str):

        db = SessionLocal()

        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            return False, "Такой пользователь уже зарегистрирован"

        hashed_password = AuthService.hash_password(password)

        user = User(
            username=username,
            email=email,
            password_hash=hashed_password
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        # Выдаём классическую тему
        classic_theme = db.query(ItemType).filter(ItemType.name == "Классическая").first()
        if classic_theme:
            shop = ShopService(db)  # придётся импортировать
            shop.add_item_to_inventory(user.id, classic_theme.id)
            # Сразу экипируем её
            equipped = db.query(UserInventory).filter(
                UserInventory.user_id == user.id,
                UserInventory.item_type_id == classic_theme.id
            ).first()
            if equipped:
                shop.equip_item(user.id, equipped.id)  # equip_item сам снимет другие темы
        db.close()
        return True, "Успешная регистрация"

    @staticmethod
    def login(username: str, password: str):

        db = SessionLocal()

        user = db.query(User).filter(User.username == username).first()

        if not user:
            return False, "Пользователя с таким именем не существует"

        if not AuthService.verify_password(password, user.password_hash):
            return False, "Неверный пароль"

        return True, user