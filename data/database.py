import sqlite3
import json
import os

# --- PATH SETUP ---
# Определяем абсолютный путь к файлу базы данных, чтобы он работал независимо от того, откуда запускается скрипт
# __file__ -> database.py
# os.path.dirname(__file__) -> /path/to/project/data
# os.path.join(...) -> /path/to/project/data/mitox_bot.db
DB_PATH = os.path.join(os.path.dirname(__file__), 'mitox_bot.db')

def _execute_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    """Универсальная функция для выполнения SQL-запросов."""
    # WAL (Write-Ahead Logging) значительно улучшает производительность при одновременных операциях чтения и записи.
    # timeout предотвращает ошибки "database is locked" при высокой нагрузке.
    with sqlite3.connect(DB_PATH, timeout=10) as conn:
        conn.execute('PRAGMA journal_mode=WAL;')
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        if commit:
            conn.commit()
        
        if fetchone:
            return cursor.fetchone()
        
        if fetchall:
            return cursor.fetchall()

def _check_and_add_columns():
    """Проверяет и добавляет недостающие колонки в таблицы."""
    tables = {
        'users': ['telegram_id', 'username', 'first_name', 'created_at'],
        'complexes': ['id', 'user_id', 'name', 'supplements', 'created_at', 'reminder_enabled', 'reminder_time']
    }
    
    for table_name, expected_columns in tables.items():
        rows = _execute_query(f"PRAGMA table_info({table_name});", fetchall=True)
        existing_columns = [row[1] for row in rows]
        
        for column in expected_columns:
            if column not in existing_columns:
                print(f"Обнаружена отсутствующая колонка '{column}' в таблице '{table_name}'. Добавляю...")
                if column == 'reminder_enabled':
                    _execute_query(f'ALTER TABLE {table_name} ADD COLUMN {column} INTEGER DEFAULT 0;', commit=True)
                elif column == 'reminder_time':
                    _execute_query(f'ALTER TABLE {table_name} ADD COLUMN {column} TEXT;', commit=True)
                else: # для других колонок, если понадобятся в будущем
                     _execute_query(f'ALTER TABLE {table_name} ADD COLUMN {column};', commit=True)
                print(f"Колонка '{column}' успешно добавлена.")


def init_db():
    """Инициализирует базу данных и создает таблицы, если их нет."""
    _execute_query('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''', commit=True)
    
    _execute_query('''
        CREATE TABLE IF NOT EXISTS complexes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            supplements TEXT NOT NULL, -- Храним как JSON-строку
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    ''', commit=True)
    print("База данных инициализирована.")
    _check_and_add_columns()


def ensure_user(telegram_id, username=None, first_name=None):
    """
    Гарантирует, что пользователь существует в БД.
    Если пользователь существует - обновляет его username и first_name.
    Если не существует - создает нового.
    Возвращает данные пользователя.
    """
    user = _execute_query("SELECT * FROM users WHERE telegram_id = ?;", (telegram_id,), fetchone=True)
    if user:
        # Пользователь найден, обновляем данные, если они изменились
        _execute_query(
            "UPDATE users SET username = ?, first_name = ? WHERE telegram_id = ?;",
            (username, first_name, telegram_id),
            commit=True
        )
    else:
        # Пользователь не найден, создаем нового
        _execute_query(
            "INSERT INTO users (telegram_id, username, first_name) VALUES (?, ?, ?);",
            (telegram_id, username, first_name),
            commit=True
        )
    # Возвращаем актуальные данные
    user_data = _execute_query("SELECT id, username, first_name FROM users WHERE telegram_id = ?;", (telegram_id,), fetchone=True)
    return {'id': user_data[0], 'username': user_data[1], 'first_name': user_data[2]}

def add_complex(telegram_id, complex_data):
    """Добавляет новый комплекс для пользователя."""
    user = ensure_user(telegram_id) # Гарантируем, что пользователь существует
    user_id = user['id']
    
    supplements_json = json.dumps(complex_data.get('supplements', []), ensure_ascii=False)
    reminder_enabled = complex_data.get('reminder_enabled', 0)
    reminder_time = complex_data.get('reminder_time', None)

    _execute_query(
        "INSERT INTO complexes (user_id, name, supplements, reminder_enabled, reminder_time) VALUES (?, ?, ?, ?, ?);",
        (user_id, complex_data['name'], supplements_json, reminder_enabled, reminder_time),
        commit=True
    )

def update_complex(complex_id, complex_data):
    """Обновляет существующий комплекс."""
    supplements_json = json.dumps(complex_data.get('supplements', []), ensure_ascii=False)
    reminder_enabled = complex_data.get('reminder_enabled', 0)
    reminder_time = complex_data.get('reminder_time', None)

    _execute_query(
        "UPDATE complexes SET name = ?, supplements = ?, reminder_enabled = ?, reminder_time = ? WHERE id = ?;",
        (complex_data['name'], supplements_json, reminder_enabled, reminder_time, complex_id),
        commit=True
    )

def delete_complex(complex_id):
    """Удаляет комплекс по его ID."""
    _execute_query("DELETE FROM complexes WHERE id = ?;", (complex_id,), commit=True)


def get_user_complexes(telegram_id):
    """Возвращает все комплексы конкретного пользователя."""
    user = ensure_user(telegram_id)
    if not user:
        return []
    
    user_id = user['id']
    rows = _execute_query("SELECT id, name, supplements, reminder_enabled, reminder_time FROM complexes WHERE user_id = ? ORDER BY created_at DESC;", (user_id,), fetchall=True)
    
    complexes = []
    for row in rows:
        complexes.append({
            'id': row[0],
            'name': row[1],
            'supplements': json.loads(row[2]),
            'reminder_enabled': bool(row[3]),
            'reminder_time': row[4]
        })
    return complexes

def get_active_reminders():
    """
    Возвращает все активные напоминания из базы данных.
    Возвращает список кортежей: (telegram_id, complex_name, reminder_time)
    """
    query = """
        SELECT u.telegram_id, c.name, c.reminder_time
        FROM complexes c
        JOIN users u ON c.user_id = u.id
        WHERE c.reminder_enabled = 1 AND c.reminder_time IS NOT NULL;
    """
    return _execute_query(query, fetchall=True)

