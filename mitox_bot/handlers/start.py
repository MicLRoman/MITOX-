# handlers/start.py

from telebot import TeleBot
from keyboards.inline import create_main_menu_keyboard
from handlers.messages import MESSAGES
from data.database import add_user_if_not_exists # <-- Импортируем функцию

def register_start_handler(bot: TeleBot):
    """Регистрирует обработчик для команды /start."""
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        """
        Отправляет приветственное сообщение и добавляет пользователя в БД.
        """
        # Добавляем пользователя в БД, если его там еще нет
        add_user_if_not_exists(message.from_user.id)
        
        # Берем текст из словаря и форматируем его, подставляя имя пользователя
        welcome_text = MESSAGES['welcome'].format(name=message.from_user.first_name)

        keyboard = create_main_menu_keyboard()

        bot.send_message(
            message.chat.id,
            text=welcome_text,
            reply_markup=keyboard,
            parse_mode='html'
        )
