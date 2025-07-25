import os
import jwt
import datetime
from flask import Flask, render_template, request, redirect, url_for, session
# Убеждаемся, что можем импортировать из родительской папки
try:
    from data.database import get_user_complexes, add_complex, init_db, ensure_user, update_complex, delete_complex
except ImportError:
    import sys
    # Добавляем родительскую директорию в путь, чтобы найти папку data/
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)
    from data.database import get_user_complexes, add_complex, init_db, ensure_user, update_complex, delete_complex

import config

app = Flask(__name__)
# Устанавливаем секретный ключ для сессий Flask
app.secret_key = config.JWT_SECRET_KEY

@app.route('/')
def index():
    """Главная страница, отображает дневник, если пользователь авторизован."""
    if 'telegram_id' not in session:
        return "Добро пожаловать! Пожалуйста, войдите через вашего Telegram-бота.", 401
    
    user_session_data = session.get('user_session', {})
    complexes = get_user_complexes(session['telegram_id'])
    return render_template('diary.html', complexes=complexes, user_session=user_session_data)

@app.route('/login_with_token')
def login_with_token():
    """Обрабатывает вход по токену от Telegram-бота."""
    token = request.args.get('token')
    if not token:
        return "Ошибка: Токен отсутствует.", 400
    try:
        # Декодируем токен, чтобы получить данные пользователя
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=['HS256'])
        telegram_id = payload['telegram_id']
        
        # Убедимся, что пользователь существует в БД на случай, если это его первый вход.
        # Это также обновит его имя и никнейм, если они изменились.
        ensure_user(telegram_id, payload.get('username'), payload.get('first_name'))
        
        # Сохраняем данные пользователя в сессию прямо из токена. Это надежнее.
        session['telegram_id'] = telegram_id
        session['user_session'] = {
            'username': payload.get('username'),
            'first_name': payload.get('first_name')
        }
        
        return redirect(url_for('index'))
    except jwt.ExpiredSignatureError:
        return "Ошибка: Срок действия токена истек. Пожалуйста, получите новую ссылку в боте.", 401
    except jwt.InvalidTokenError:
        return "Ошибка: Неверный токен.", 401


def _process_complex_form(form):
    """Вспомогательная функция для сбора данных о комплексе из формы."""
    # request.form.get('reminder_enabled') вернет 'on', если чекбокс отмечен, и None, если нет.
    reminder_enabled = 1 if form.get('reminder_enabled') == 'on' else 0
    
    complex_data = {
        'name': form.get('complex_name'),
        'supplements': [],
        'reminder_enabled': reminder_enabled,
        'reminder_time': form.get('reminder_time') if reminder_enabled else None
    }
    
    names = form.getlist('supplement_name')
    dosages = form.getlist('supplement_dosage')

    for name, dosage in zip(names, dosages):
        if name and dosage:
            complex_data['supplements'].append({'name': name, 'dosage': dosage})

    print(f"DEBUG (Flask): Обработка формы. Данные для БД: {complex_data}")
            
    return complex_data


@app.route('/add_complex', methods=['POST'])
def add_new_complex():
    """Обрабатывает форму добавления нового комплекса."""
    if 'telegram_id' not in session:
        return "Ошибка: Вы не авторизованы.", 401
    
    complex_data = _process_complex_form(request.form)
    add_complex(session['telegram_id'], complex_data)
    
    return redirect(url_for('index'))

@app.route('/edit_complex/<int:complex_id>', methods=['POST'])
def edit_existing_complex(complex_id):
    """Обрабатывает форму редактирования существующего комплекса."""
    if 'telegram_id' not in session:
        return "Ошибка: Вы не авторизованы.", 401
    
    complex_data = _process_complex_form(request.form)
    update_complex(complex_id, complex_data)
    
    return redirect(url_for('index'))

@app.route('/delete_complex/<int:complex_id>', methods=['POST'])
def delete_existing_complex(complex_id):
    """Обрабатывает запрос на удаление комплекса."""
    if 'telegram_id' not in session:
        return "Ошибка: Вы не авторизованы.", 401

    delete_complex(complex_id)
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    # При запуске убедимся, что база данных инициализирована
    try:
        init_db()
    except Exception as e:
        print(f"Error initializing database from Flask app: {e}")
    app.run(host='0.0.0.0', port=5000, debug=True)
