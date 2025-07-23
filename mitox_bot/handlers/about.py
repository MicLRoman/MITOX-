# handlers/about.py

from telebot import TeleBot
from telebot.types import CallbackQuery
from telebot.apihelper import ApiTelegramException
from keyboards.inline import create_about_project_keyboard, create_links_keyboard
from handlers.messages import MESSAGES

def show_about_menu(bot: TeleBot, call: CallbackQuery):
    """Показывает меню 'Подробнее о проекте'."""
    try:
        keyboard = create_about_project_keyboard()
        text = MESSAGES['about_project']
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=text,
            reply_markup=keyboard,
            parse_mode='html'
        )
    except ApiTelegramException as e:
        if "message is not modified" not in str(e):
            print(f"Ошибка в show_about_menu: {e}")

def show_links_menu(bot: TeleBot, call: CallbackQuery):
    """Показывает меню с ссылками (явками)."""
    try:
        keyboard = create_links_keyboard()
        text = MESSAGES['links_info']
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=text,
            reply_markup=keyboard,
            parse_mode='html'
        )
    except ApiTelegramException as e:
        if "message is not modified" not in str(e):
            print(f"Ошибка в show_links_menu: {e}")
