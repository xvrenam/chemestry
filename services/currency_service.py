from sqlalchemy.orm import Session
from database.models.user import UserCurrency

class CurrencyService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_wallet(self, user_id) -> UserCurrency:
        wallet = self.db.query(UserCurrency).filter(UserCurrency.user_id == user_id).first()
        if not wallet:
            wallet = UserCurrency(user_id=user_id, coins=0, crystals=0)
            self.db.add(wallet)
            self.db.commit()
            self.db.refresh(wallet)
        return wallet

    def add_coins(self, user_id, amount: int):
        wallet = self.get_or_create_wallet(user_id)
        wallet.coins += amount
        self.db.commit()

    def add_crystals(self, user_id, amount: int):
        wallet = self.get_or_create_wallet(user_id)
        wallet.crystals += amount
        self.db.commit()

    def spend(self, user_id, coins: int = 0, crystals: int = 0) -> bool:
        wallet = self.get_or_create_wallet(user_id)
        if wallet.coins >= coins and wallet.crystals >= crystals:
            wallet.coins -= coins
            wallet.crystals -= crystals
            self.db.commit()
            return True
        return False