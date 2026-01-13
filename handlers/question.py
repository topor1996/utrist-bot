from telegram import Update
from telegram.ext import ContextTypes
from database import create_question
from keyboards.main_menu import main_menu_keyboard, back_to_main_keyboard
from config import ADMIN_IDS
import logging

logger = logging.getLogger(__name__)

# Состояния для вопроса
QUESTION_STATES = {
    'waiting_question': 1,
}

async def question_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало процесса вопроса"""
    # ConversationHandler сам управляет состоянием, но для unified_message_handler нужно установить question_state
    user_data = context.user_data
    user_data['question_state'] = QUESTION_STATES['waiting_question']
    
    await update.message.reply_text(
        "❓ Задайте ваш вопрос:\n\nОпишите вашу ситуацию или задайте вопрос, и мы обязательно ответим.",
        reply_markup=back_to_main_keyboard()
    )
    # Возвращаем состояние для ConversationHandler
    return QUESTION_STATES['waiting_question']

async def process_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка вопроса"""
    from telegram.ext import ConversationHandler
    user_data = context.user_data
    text = update.message.text
    
    if text in ['🏠 Главное меню', '🔙 Главное меню']:
        user_data.clear()
        await update.message.reply_text(
            "🏠 Главное меню",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
    
    # Обрабатываем вопрос
        # Получаем имя пользователя из Telegram профиля
        user = update.effective_user
        client_name = user.first_name or "Пользователь"
        if user.last_name:
            client_name += f" {user.last_name}"
        
        # Создаем вопрос
        try:
            question_id = await create_question(
                user_id=user.id,
                question_text=text,
                client_name=client_name,
                client_phone=None
            )
            
            logger.info(f"Создан вопрос #{question_id} от пользователя {user.id}")
            
            # Отправляем уведомление администраторам
            question_info = f"""
❓ Новый вопрос от клиента

ID: {question_id}
👤 Имя: {client_name}
💬 Вопрос: {text}
"""
            
            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_message(chat_id=admin_id, text=question_info)
                except Exception as e:
                    logger.error(f"Ошибка отправки уведомления администратору {admin_id}: {e}")
            
            await update.message.reply_text(
                """
✅ Ваш вопрос отправлен!

Мы свяжемся с вами в ближайшее время.

Спасибо за обращение!
""",
                reply_markup=main_menu_keyboard()
            )
            
            user_data.clear()
            # Завершаем ConversationHandler
            return ConversationHandler.END
        except Exception as e:
            logger.error(f"Ошибка создания вопроса: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при отправке вопроса. Попробуйте позже.",
                reply_markup=main_menu_keyboard()
            )
            user_data.clear()
            return ConversationHandler.END