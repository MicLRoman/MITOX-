# main.py

import telebot
import config
import json
from data.database import init_db, add_complex 
from handlers.start import register_start_handler
from handlers.feedback import show_feedback_menu
from handlers.navigation import return_to_main_menu
from handlers.about import show_about_menu, show_links_menu
from handlers.messages import MESSAGES

# --- Инициализация ---
bot = telebot.TeleBot(config.BOT_TOKEN)

# --- Регистрация обработчиков ---
register_start_handler(bot)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    bot.answer_callback_query(call.id)
    
    if call.data == "back_to_main_menu":
        return_to_main_menu(bot, call)
    
    # НОВЫЙ ОБРАБОТЧИК ДЛЯ КНОПКИ ОБНОВЛЕНИЯ
    elif call.data == "refresh_main_menu":
        # Просто вызываем функцию возврата в главное меню,
        # она перерисует сообщение с новой клавиатурой
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


@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    print("Получены данные из Web App:", message.web_app_data.data)
    try:
        complex_data = json.loads(message.web_app_data.data)
        add_complex(message.from_user.id, complex_data)
        bot.send_message(
            message.chat.id,
            f"✅ Комплекс «<b>{complex_data['name']}</b>» успешно сохранен!",
            parse_mode='html'
        )
    except Exception as e:
        print(f"Ошибка обработки данных из Web App: {e}")
        bot.send_message(
            message.chat.id,
            "Произошла ошибка при сохранении данных."
        )


# --- Запуск бота ---
if __name__ == '__main__':
    init_db()
    print("Бот запущен...")
    bot.polling(none_stop=True)
