from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_keyboard():
    """Главное меню"""
    keyboard = [
        [KeyboardButton('📋 Наши услуги')],
        [KeyboardButton('📞 Записаться на консультацию')],
        [KeyboardButton('❓ Задать вопрос')],
        [KeyboardButton('ℹ️ О компании'), KeyboardButton('📍 Контакты')],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def back_to_main_keyboard():
    """Кнопка возврата в главное меню"""
    keyboard = [[KeyboardButton('🏠 Главное меню')]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def cancel_keyboard():
    """Клавиатура с кнопкой отмены для процесса записи"""
    keyboard = [[KeyboardButton('❌ Отменить запись')]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def contact_keyboard():
    """Клавиатура с контактами"""
    keyboard = [
        [KeyboardButton('📞 Позвонить', request_contact=False)],
        [KeyboardButton('🏠 Главное меню')]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
