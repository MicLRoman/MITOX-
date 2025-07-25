# data/database.py
import sqlite3
import os
import json
import threading

# --- Настройки ---

# Этот код находит абсолютный путь к папке, где лежит этот файл.
# Это делает его независимым от того, откуда запускается бот или Flask.
DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(DB_DIR, 'mitox_app.db')

# Создаем локальный для потока объект, чтобы у каждого потока (запроса)
# было свое собственное соединение с БД. Это стандартная практика для Flask.
local_storage = threading.local()

def get_db_connection():
    """Открывает новое соединение с БД, если его еще нет для текущего потока."""
    db = getattr(local_storage, '_database', None)
    if db is None:
        db = local_storage._database = sqlite3.connect(DB_NAME, timeout=10)
        # Включаем режим WAL для лучшей параллельной работы
        db.execute('PRAGMA journal_mode=WAL;')
    return db

def close_db_connection(exception=None):
    """Закрывает соединение с БД в конце запроса."""
    db = getattr(local_storage, '_database', None)
    if db is not None:
        db.close()
        local_storage._database = None

# --- Инициализация ---

def init_db():
    """
    Инициализирует базу данных: создает папку, файл и таблицы, если их нет.
    """
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()

    # Таблица пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Таблица комплексов со связью (FOREIGN KEY)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complexes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            supplements TEXT NOT NULL, -- Храним как JSON-строку
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    print("Database initialized successfully with WAL mode enabled.")
    close_db_connection()


# --- Функции для работы с пользователями ---

def ensure_user(telegram_id, username='', first_name=''):
    """
    Проверяет, существует ли пользователь. Если нет - создает.
    Возвращает внутренний id пользователя.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    
    if user:
        close_db_connection()
        return user[0]
    else:
        cursor.execute(
            "INSERT INTO users (telegram_id, username, first_name) VALUES (?, ?, ?)",
            (telegram_id, username, first_name)
        )
        conn.commit()
        user_id = cursor.lastrowid
        print(f"Created new user with Telegram ID: {telegram_id}")
        close_db_connection()
        return user_id

# --- Функции для работы с комплексами ---

def add_complex(telegram_id, complex_data):
    """Сохраняет новый комплекс для пользователя."""
    user_id = ensure_user(telegram_id)
    supplements_json = json.dumps(complex_data.get('supplements', []), ensure_ascii=False)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO complexes (user_id, name, supplements) VALUES (?, ?, ?)",
        (user_id, complex_data['name'], supplements_json)
    )
    conn.commit()
    close_db_connection()
    print(f"Saved complex '{complex_data['name']}' for user with Telegram ID {telegram_id}")

def get_user_complexes(telegram_id):
    """Получает все комплексы конкретного пользователя."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Сначала найдем внутренний ID пользователя
    cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    
    if not user:
        close_db_connection()
        return [] # Пользователя нет в базе, значит и комплексов нет
    
    user_id = user[0]
    cursor.execute(
        "SELECT id, name, supplements FROM complexes WHERE user_id = ? ORDER BY id DESC", 
        (user_id,)
    )
    complexes_raw = cursor.fetchall()
    close_db_connection()

    # Преобразуем данные в удобный формат
    complexes_list = []
    for row in complexes_raw:
        complexes_list.append({
            "id": row[0],
            "name": row[1],
            "supplements": json.loads(row[2])
        })
    return complexes_list
