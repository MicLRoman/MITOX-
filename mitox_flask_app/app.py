# mitox_flask_app/app.py
from flask import Flask, render_template, request, redirect, url_for, session, g
import jwt
import sys
import os
import json

# --- Настройка путей для импорта ---
# Добавляем родительскую директорию (где лежит папка data) в путь
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Импортируем наш универсальный модуль для работы с БД и конфиг
from data.database import get_user_complexes, add_complex, init_db, get_db_connection, close_db_connection, ensure_user
import config # Используем тот же конфиг, что и бот

# --- Инициализация Flask ---
app = Flask(__name__)
# Устанавливаем секретный ключ для сессий Flask
app.secret_key = 'a-different-super-secret-key-for-flask-sessions'

# --- Работа с БД в контексте Flask ---
# Эти функции будут автоматически открывать и закрывать соединение с БД для каждого запроса
@app.before_request
def before_request():
    g.db = get_db_connection()

@app.teardown_request
def teardown_request(exception):
    close_db_connection(exception)


# --- Роуты (Маршруты) ---

@app.route('/')
def index():
    """Главная страница. Проверяет, залогинен ли пользователь."""
    # Если в сессии есть telegram_id, значит пользователь залогинен
    if 'telegram_id' in session:
        complexes = get_user_complexes(session['telegram_id'])
        # Мы передаем всю сессию в шаблон, чтобы иметь доступ ко всем данным
        return render_template('diary.html', user_session=session, complexes=complexes)
    else:
        # Если не залогинен, показываем простое сообщение
        return "Добро пожаловать! Пожалуйста, войдите через вашего Telegram-бота.", 401

@app.route('/login_with_token')
def login_with_token():
    """
    Страница, которая принимает токен, проверяет его и логинит пользователя.
    """
    token = request.args.get('token')
    if not token:
        return "Ошибка: Токен не предоставлен.", 400
    
    try:
        # Пытаемся расшифровать токен
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=['HS256'])
        
        # Сохраняем данные пользователя в сессию
        session['telegram_id'] = payload['telegram_id']
        # Можно сохранить и другие данные, если они есть в токене
        session['first_name'] = "Пользователь" # Для примера
        
        # Перенаправляем пользователя на главную страницу дневника
        return redirect(url_for('index'))

    except jwt.ExpiredSignatureError:
        return "Ошибка: Срок действия ссылки для входа истек. Пожалуйста, получите новую в боте.", 401
    except jwt.InvalidTokenError:
        return "Ошибка: Неверная ссылка для входа.", 401


@app.route('/add_complex', methods=['POST'])
def add_new_complex():
    """Обрабатывает форму добавления нового комплекса."""
    if 'telegram_id' not in session:
        return "Ошибка: Вы не авторизованы.", 401

    # Собираем данные из формы
    complex_data = {
        'name': request.form.get('complex_name'),
        'supplements': []
    }
    # request.form.getlist позволяет получить все значения для полей с одинаковым именем
    names = request.form.getlist('supplement_name')
    dosages = request.form.getlist('supplement_dosage')

    for name, dosage in zip(names, dosages):
        if name and dosage: # Убедимся, что поля не пустые
            complex_data['supplements'].append({'name': name, 'dosage': dosage})
    
    # Сохраняем в базу данных
    add_complex(session['telegram_id'], complex_data)
    
    # Перенаправляем обратно на главную страницу, чтобы пользователь увидел изменения
    return redirect(url_for('index'))

# --- Запуск ---
if __name__ == '__main__':
    # Инициализируем базу данных перед первым запуском
    init_db()
    # Запускаем Flask-сервер
    # debug=True позволяет автоматически перезагружать сервер при изменениях в коде
    app.run(debug=True, port=5000)
