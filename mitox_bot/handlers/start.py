# handlers/start.py

import os
import sys
from telebot import TeleBot
from keyboards.inline import create_main_menu_keyboard
from handlers.messages import MESSAGES

def register_start_handler(bot: TeleBot):
    """Регистрирует обработчик для команды /start."""
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        """
        Отправляет приветственное сообщение и гарантирует, что пользователь есть в БД.
        """

        
        welcome_text = MESSAGES['welcome'].format(name=message.from_user.first_name)
        keyboard = create_main_menu_keyboard()

        bot.send_message(
            message.chat.id,
            text=welcome_text,
            reply_markup=keyboard,
            parse_mode='html'
        )
