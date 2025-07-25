# mitox_bot/main.py
import telebot
from telebot import types
import config
import jwt
import datetime
import time
import sys
import os

# --- Настройка путей для импорта ---
# Это нужно, чтобы бот мог найти папку data/, которая может лежать в родительской директории
# Добавляем родительскую директорию в путь поиска модулей
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)
    from data.database import init_db, ensure_user
except ImportError:
    # Если импорт не удался, возможно, структура уже плоская
    from data.database import init_db, ensure_user


from handlers.start import register_start_handler
from handlers.feedback import show_feedback_menu
from handlers.navigation import return_to_main_menu
from handlers.about import show_about_menu, show_links_menu
from handlers.messages import MESSAGES

bot = telebot.TeleBot(config.BOT_TOKEN)

# --- Handlers ---
register_start_handler(bot)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    bot.answer_callback_query(call.id)
    
    # НОВАЯ ЛОГИКА ДЛЯ ДНЕВНИКА
    if call.data == "open_diary":
        bot.answer_callback_query(call.id, "Генерирую ссылку для входа...")
        try:
            # 1. Убедимся, что пользователь есть в базе
            ensure_user(call.from_user.id, call.from_user.username, call.from_user.first_name)
            
            # 2. Создаем "билет" (JWT токен)
            payload = {
                'telegram_id': call.from_user.id,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5) # Токен живет 5 минут
            }
            token = jwt.encode(payload, config.JWT_SECRET_KEY, algorithm='HS256')
            
            # 3. Формируем ссылку для входа на Flask-сайт
            login_url = f"{config.FLASK_APP_URL}/login_with_token?token={token}"
            
            # 4. Отправляем кнопку со ссылкой
            keyboard = types.InlineKeyboardMarkup()
            login_button = types.InlineKeyboardButton(
    text="✅ Войти в дневник", 
    web_app=types.WebAppInfo(url=login_url) # <--- Специальная кнопка Mini App
)
            keyboard.add(login_button)
            
            bot.send_message(
                call.message.chat.id,
                "Ваша персональная ссылка для входа готова. Она действует 5 минут.",
                reply_markup=keyboard
            )
        except Exception as e:
            print(f"Ошибка при создании токена: {e}")
            bot.send_message(call.message.chat.id, "Не удалось создать ссылку для входа. Попробуйте снова.")
        return

    if call.data == "back_to_main_menu":
        return_to_main_menu(bot, call)
    elif call.data == "feedback":
        show_feedback_menu(bot, call)
    elif call.data == "about_project_menu":
        show_about_menu(bot, call)
    elif call.data == "show_links":
        show_links_menu(bot, call)
    elif call.data == "articles_menu":
        bot.answer_callback_query(call.id, MESSAGES['articles_soon'], show_alert=True)
    elif call.data == "show_team":
        bot.answer_callback_query(call.id, MESSAGES['team_info'], show_alert=True)

# --- Startup ---
if __name__ == '__main__':
    init_db()
    print("Бот запущен...")
    
    # ИЗМЕНЕНИЕ: Добавляем бесконечный цикл для отказоустойчивости
    while True:
        try:
            print("Запускаю главный цикл обработки сообщений (polling)...")
            bot.polling(none_stop=True)
        except Exception as e:
            # Если произошла любая ошибка, выводим ее в консоль
            print(f"\n!!! КРИТИЧЕСКАЯ ОШИБКА В ГЛАВНОМ ЦИКЛЕ !!!")
            print(f"Ошибка: {e}")
            print("Перезапускаю бот через 5 секунд...")
            time.sleep(5) # Ждем 5 секунд перед перезапуском
