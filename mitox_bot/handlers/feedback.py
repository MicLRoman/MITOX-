# handlers/feedback.py

from telebot import TeleBot
from telebot.types import CallbackQuery
from telebot.apihelper import ApiTelegramException
from keyboards.inline import create_feedback_keyboard
from handlers.messages import MESSAGES

def show_feedback_menu(bot: TeleBot, call: CallbackQuery):
    print("A0")
    """
    Редактирует сообщение, показывая меню обратной связи.
    """
    try:
        print("A1")
        keyboard = create_feedback_keyboard()
        print("A2")
        feedback_text = MESSAGES['feedback']
        print("A3")

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=feedback_text,
            reply_markup=keyboard,
            parse_mode='html'
        )
        print("A4")
    except ApiTelegramException as e:
        if "message is not modified" in str(e):
            print("DFGHJK")
        else:
            print(f"Произошла ошибка при показе меню обратной связи: {e}")

