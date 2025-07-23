# data/database.py

import sqlite3
import json
import os

# Определяем путь к папке 'data' и файлу БД
DATA_DIR = 'data'
DB_NAME = os.path.join(DATA_DIR, 'mitox_bot.db')

def init_db():
    """Инициализирует базу данных и создает таблицы, если их нет."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Таблица пользователей с новыми полями
    # schedules и reminders будут хранить данные в формате JSON
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            telegram_id INTEGER UNIQUE NOT NULL,
            schedules TEXT NOT NULL DEFAULT '{}',
            reminders TEXT NOT NULL DEFAULT '{}'
        )
    ''')

    # Таблица для хранения комплексов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS complexes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            supplements TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"База данных инициализирована по пути: {DB_NAME}")

def add_user_if_not_exists(telegram_id):
    """Добавляет нового пользователя, если его еще нет в базе."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    # Если пользователя нет, создаем новую запись.
    # Поля schedules и reminders получат значения по умолчанию ('{}')
    if not user:
        cursor.execute("INSERT INTO users (telegram_id) VALUES (?)", (telegram_id,))
        conn.commit()
        print(f"Добавлен новый пользователь с ID: {telegram_id}")
    conn.close()

def add_complex(telegram_id, complex_data):
    """
    Сохраняет новый комплекс для пользователя.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
    user_record = cursor.fetchone()
    if not user_record:
        print(f"Ошибка: пользователь с telegram_id {telegram_id} не найден.")
        conn.close()
        return

    user_db_id = user_record[0]
    complex_name = complex_data['name']
    
    supplements_json = json.dumps(complex_data['supplements'], ensure_ascii=False)

    cursor.execute(
        "INSERT INTO complexes (user_id, name, supplements) VALUES (?, ?, ?)",
        (user_db_id, complex_name, supplements_json)
    )
    conn.commit()
    conn.close()
    print(f"Для пользователя {telegram_id} сохранен комплекс '{complex_name}'")
