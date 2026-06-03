# database/init_db.py
import os

from sqlalchemy import text

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from urllib.parse import urlparse

from database.db import engine, Base
from database.models import *  # импорт всех моделей для регистрации в Base.metadata


def ensure_database_exists(db_url: str):
    """Создаёт базу данных, если она не существует."""
    url = urlparse(db_url)
    db_name = url.path[1:]  # убираем слеш
    user = url.username
    password = url.password
    host = url.hostname
    port = url.port or 5432

    # Подключаемся к служебной БД postgres
    conn = psycopg2.connect(
        dbname='postgres',
        user=user,
        password=password,
        host=host,
        port=port
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
    exists = cur.fetchone()
    if not exists:
        cur.execute(f"CREATE DATABASE {db_name}")
        print(f"База данных '{db_name}' создана.")
    else:
        print(f"База данных '{db_name}' уже существует.")
    cur.close()
    conn.close()

def init_db():
    ensure_database_exists(os.getenv("DATABASE_URL"))
    # Создаём все таблицы, если их нет
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("База данных инициализирована.")