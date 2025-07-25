import telebot
from telebot import types
import config
import json
import jwt
import datetime
import os
import sys
import time

# --- НАСТРОЙКА ПУТЕЙ И ПЛАНИРОВЩИКА ---
# Добавляем родительскую директорию в путь, чтобы найти папку data/
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from apscheduler.schedulers.background import BackgroundScheduler
from data.database import init_db, ensure_user, get_active_reminders
from handlers.start import register_start_handler
from handlers.feedback import show_feedback_menu
from handlers.navigation import return_to_main_menu
from handlers.about import show_about_menu, show_links_menu
from handlers.messages import MESSAGES

# --- ИНИЦИАЛИЗАЦИЯ ---
bot = telebot.TeleBot(config.BOT_TOKEN)

# --- УПРАВЛЕНИЕ НАПОМИНАНИЯМИ ---
# Используем кэш в памяти, чтобы не отправлять дубликаты в течение дня.
# Ключ: (telegram_id, reminder_time), Значение: дата последней отправки.
sent_reminders_cache = {}
# Дата, когда кэш был в последний раз очищен.
cache_last_cleared_date = datetime.date.today()

# --- ФОНОВАЯ ЗАДАЧА (SCHEDULER) ---
def check_reminders():
    """Проверяет и отправляет напоминания, если их время наступило или прошло не более минуты назад."""
    global sent_reminders_cache, cache_last_cleared_date
    
    today = datetime.date.today()
    # Очищаем кэш раз в день, чтобы напоминания работали на следующий день
    if today != cache_last_cleared_date:
        sent_reminders_cache.clear()
        cache_last_cleared_date = today
        print(f"[{datetime.datetime.now()}] Кэш напоминаний очищен на новую дату: {today}")

    try:
        active_reminders = get_active_reminders()
        now = datetime.datetime.now()

        for telegram_id, complex_name, reminder_time_str in active_reminders:
            try:
                # Преобразуем время из строки в объект datetime для сегодняшней даты
                reminder_hour, reminder_minute = map(int, reminder_time_str.split(':'))
                reminder_dt = now.replace(hour=reminder_hour, minute=reminder_minute, second=0, microsecond=0)
                
                # Считаем разницу в секундах
                time_difference = (now - reminder_dt).total_seconds()
                
                # Проверяем, что время наступило, но прошло не более 60 секунд
                if 0 <= time_difference < 60:
                    reminder_key = (telegram_id, reminder_time_str)
                    
                    # Если мы еще не отправляли это напоминание сегодня, отправляем
                    if sent_reminders_cache.get(reminder_key) != today:
                        message_text = f"⏰ **Напоминание!**\n\nНе забудьте принять комплекс «{complex_name}»."
                        bot.send_message(telegram_id, message_text, parse_mode='Markdown')
                        
                        # Запоминаем, что отправили сегодня
                        sent_reminders_cache[reminder_key] = today
                        print(f"Отправлено напоминание по '{complex_name}' пользователю {telegram_id}")

            except Exception as e:
                print(f"Ошибка обработки напоминания для {telegram_id}: {e}")
    except Exception as e:
        print(f"Критическая ошибка в потоке планировщика: {e}")


# --- ОБРАБОТЧИКИ TELEGRAM ---
register_start_handler(bot) # Обработчик /start

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    """Обрабатывает все нажатия на inline-кнопки."""
    bot.answer_callback_query(call.id)

    if call.data == "open_diary":
        try:
            payload = {
                'telegram_id': call.from_user.id,
                'username': call.from_user.username,
                'first_name': call.from_user.first_name,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
            }
            token = jwt.encode(payload, config.JWT_SECRET_KEY, algorithm='HS256')
            login_url = f"{config.FLASK_APP_URL}/login_with_token?token={token}"
            
            keyboard = types.InlineKeyboardMarkup()
            login_button = types.InlineKeyboardButton(
                text="✅ Войти в дневник",
                web_app=types.WebAppInfo(url=login_url)
            )
            keyboard.add(login_button)
            
            bot.send_message(
                call.message.chat.id,
                "Ваша персональная ссылка для входа готова. Она действительна 5 минут.",
                reply_markup=keyboard
            )
        except Exception as e:
            print(f"Ошибка при создании токена: {e}")
            bot.send_message(call.message.chat.id, "Произошла ошибка при создании ссылки. Попробуйте снова.")
        return
    
    # Старая логика для других кнопок
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


# --- ЗАПУСК ---
if __name__ == '__main__':
    print("Инициализация базы данных...")
    init_db()
    
    print("Запуск планировщика напоминаний...")
    scheduler = BackgroundScheduler(timezone="Europe/Riga") 
    scheduler.add_job(check_reminders, 'interval', seconds=55) # Проверяем чуть чаще, чем раз в минуту
    scheduler.start()

    print("Telegram-бот запущен...")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Критическая ошибка в главном цикле бота: {e}")
            time.sleep(5)
