# keyboards/inline.py
from telebot import types
import config

def create_main_menu_keyboard():
    """Создает главную клавиатуру."""
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    # Кнопка для дневника теперь просто отправляет сигнал боту
    mini_app_button = types.InlineKeyboardButton(
        text="📝 Дневник приема БАД",
        callback_data="open_diary"
    )
    channel_button = types.InlineKeyboardButton(text="📢 Наш канал", url=config.CHANNEL_URL)
    articles_button = types.InlineKeyboardButton(text="📄 Статьи", callback_data="articles_menu")
    about_button = types.InlineKeyboardButton(text="ℹ️ Подробнее о проекте", callback_data="about_project_menu")
    feedback_button = types.InlineKeyboardButton(text="💬 Обратная связь", callback_data="feedback")
    
    keyboard.add(mini_app_button, channel_button, articles_button, about_button, feedback_button)
    return keyboard

# ... (Остальные клавиатуры можно оставить как есть) ...
def create_about_project_keyboard():
    """Создает клавиатуру для раздела 'Подробнее о проекте'."""
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    site_button = types.InlineKeyboardButton(text="Наш сайт", url=config.SITE_URL)
    team_button = types.InlineKeyboardButton(text="Команда", callback_data="show_team")
    links_button = types.InlineKeyboardButton(text="Явки", callback_data="show_links")
    
    back_button = types.InlineKeyboardButton(
        text="⬅️ Назад в главное меню",
        callback_data="back_to_main_menu"
    )

    keyboard.add(site_button, team_button)
    keyboard.add(links_button)
    keyboard.add(back_button)
    return keyboard

def create_links_keyboard():
    """Создает клавиатуру для раздела 'Явки'."""
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    vk_button = types.InlineKeyboardButton(text="VK", url=config.VK_URL)
    inst_button = types.InlineKeyboardButton(text="Instagram", url=config.INST_URL)
    
    back_button = types.InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data="about_project_menu" # Возврат в меню "О проекте"
    )
    
    keyboard.add(vk_button, inst_button, back_button)
    return keyboard


def create_feedback_keyboard():
    """Создает клавиатуру для раздела 'Обратная связь'."""
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = []

    if hasattr(config, 'FEEDBACK_TG_USERNAME') and config.FEEDBACK_TG_USERNAME:
        tg_button = types.InlineKeyboardButton(
            text="💬 ТГ",
            url=f"https://t.me/{config.FEEDBACK_TG_USERNAME}"
        )
        buttons.append(tg_button)
    
    back_button = types.InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data="back_to_main_menu"
    )

    if buttons:
        keyboard.add(*buttons)
    
    keyboard.add(back_button)
    return keyboard
