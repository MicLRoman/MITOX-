# handlers/navigation.py

from telebot import TeleBot
from telebot.types import CallbackQuery
from telebot.apihelper import ApiTelegramException
from keyboards.inline import create_main_menu_keyboard
from handlers.messages import MESSAGES

def return_to_main_menu(bot: TeleBot, call: CallbackQuery):
    """
    Возвращает пользователя в главное меню, редактируя текущее сообщение.
    """
    try:
        welcome_text = MESSAGES['welcome'].format(name=call.from_user.first_name)
        keyboard = create_main_menu_keyboard()

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=welcome_text,
            reply_markup=keyboard,
            parse_mode='html'
        )
    except ApiTelegramException as e:
        # Эта ошибка возникает, если сообщение не изменилось.
        # Мы можем ее просто проигнорировать.
        if "message is not modified" in str(e):
            pass
        else:
            # В случае других ошибок - выводим их в консоль.
            print(f"Произошла ошибка при возврате в главное меню: {e}")

