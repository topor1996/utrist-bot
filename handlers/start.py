from telegram import Update
from telegram.ext import ContextTypes
from database import add_user, is_admin
from keyboards.main_menu import main_menu_keyboard

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    # Добавляем пользователя в БД
    await add_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    # Проверяем, является ли пользователь администратором
    is_user_admin = await is_admin(user.id)
    
    welcome_text = f"""
👋 Добро пожаловать, {user.first_name}!

Я бот юридической компании "Ваш юрист" в Санкт-Петербурге.

Я помогу вам:
• Узнать о наших услугах
• Записаться на консультацию
• Задать вопрос
• Получить контакты

Выберите действие из меню ниже 👇
"""
    
    # Если админ, показываем кнопку админ-панели
    if is_user_admin:
        from telegram import ReplyKeyboardMarkup, KeyboardButton
        keyboard = [
            [KeyboardButton('📋 Наши услуги')],
            [KeyboardButton('📞 Записаться на консультацию')],
            [KeyboardButton('❓ Задать вопрос')],
            [KeyboardButton('ℹ️ О компании'), KeyboardButton('📍 Контакты')],
            [KeyboardButton('🔐 Админ-панель')],
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    else:
        reply_markup = main_menu_keyboard()
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup
    )

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик возврата в главное меню"""
    user = update.effective_user
    is_user_admin = await is_admin(user.id)
    
    if is_user_admin:
        from telegram import ReplyKeyboardMarkup, KeyboardButton
        keyboard = [
            [KeyboardButton('📋 Наши услуги')],
            [KeyboardButton('📞 Записаться на консультацию')],
            [KeyboardButton('❓ Задать вопрос')],
            [KeyboardButton('ℹ️ О компании'), KeyboardButton('📍 Контакты')],
            [KeyboardButton('🔐 Админ-панель')],
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    else:
        reply_markup = main_menu_keyboard()
    
    await update.message.reply_text(
        "🏠 Главное меню",
        reply_markup=reply_markup
    )
