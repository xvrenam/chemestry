from database.db import SessionLocal
from database.models.user import User, Friendship


class FriendsService:

    # 🔍 поиск пользователей
    @staticmethod
    def search_users(query: str):

        db = SessionLocal()

        users = db.query(User).filter(
            User.username.ilike(f"%{query}%")
        ).all()

        return users
    
    @staticmethod
    def get_user_by_id(u_id : int):

        db = SessionLocal()

        user = db.query(User).filter(
            User.id == u_id
        ).all()

        return user

    # 👥 список друзей
    @staticmethod
    def get_friends(user_id):

        db = SessionLocal()

        friendships = db.query(Friendship).filter(
            ((Friendship.requester_id == user_id) |
             (Friendship.addressee_id == user_id)) &
            (Friendship.status == "accepted")
        ).all()

        friends = []

        for f in friendships:
            friend_id = (
                f.addressee_id if f.requester_id == user_id
                else f.requester_id
            )

            user = db.query(User).filter(User.id == friend_id).first()
            if user:
                friends.append(user)

        return friends

    # 📩 входящие заявки
    @staticmethod
    def get_requests(user_id):

        db = SessionLocal()

        requests = db.query(Friendship).filter(
            (Friendship.addressee_id == user_id) &
            (Friendship.status == "pending")
        ).all()

        users = []

        for r in requests:
            user = db.query(User).filter(User.id == r.requester_id).first()
            if user:
                users.append(user)

        return users

    # ➕ отправить заявку
    @staticmethod
    def send_request(requester_id, username):

        db = SessionLocal()

        target = db.query(User).filter(User.username == username).first()

        if not target:
            return False, "Пользователь не найден"

        if target.id == requester_id:
            return False, "Нельзя добавить себя"

        # проверка существующей связи
        existing = db.query(Friendship).filter(
            ((Friendship.requester_id == requester_id) &
             (Friendship.addressee_id == target.id)) |
            ((Friendship.requester_id == target.id) &
             (Friendship.addressee_id == requester_id))
        ).first()

        if existing:
            return False, "Запрос уже существует"

        friendship = Friendship(
            requester_id=requester_id,
            addressee_id=target.id,
            status="pending"
        )

        db.add(friendship)
        db.commit()

        return True, "Запрос отправлен"

    # ✅ принять заявку
    @staticmethod
    def accept_request(user_id, requester_id):

        db = SessionLocal()

        friendship = db.query(Friendship).filter(
            (Friendship.requester_id == requester_id) &
            (Friendship.addressee_id == user_id)
        ).first()

        if not friendship:
            return False, "Заявка не найдена"

        friendship.status = "accepted"
        db.commit()

        return True, "Пользователь добавлен в друзья"

    # ❌ отклонить заявку
    @staticmethod
    def decline_request(user_id, requester_id):

        db = SessionLocal()

        friendship = db.query(Friendship).filter(
            (Friendship.requester_id == requester_id) &
            (Friendship.addressee_id == user_id)
        ).first()

        if not friendship:
            return False, "Заявка не найдена"

        db.delete(friendship)
        db.commit()

        return True, "Заявка отклонена"
    
    # ❌ удалить друга
    @staticmethod
    def remove_friend(user_id, friend_id):

        db = SessionLocal()

        friendship = db.query(Friendship).filter(
            (
                (Friendship.requester_id == user_id) &
                (Friendship.addressee_id == friend_id)
            ) |
            (
                (Friendship.requester_id == friend_id) &
                (Friendship.addressee_id == user_id)
            )
        ).first()

        if not friendship:
            return False, "Пользователь не найден в друзьях"

        db.delete(friendship)
        db.commit()

        return True, "Пользователь удалён из друзей"