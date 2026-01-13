from telegram import Update
from telegram.ext import ContextTypes
from database import create_question
from keyboards.main_menu import main_menu_keyboard, back_to_main_keyboard
from config import ADMIN_IDS

# Состояния для вопроса
QUESTION_STATES = {
    'waiting_question': 1,
    'waiting_name': 2,
    'waiting_phone': 3,
}

async def question_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало процесса вопроса"""
    user_data = context.user_data
    user_data['question'] = {}
    user_data['question_state'] = QUESTION_STATES['waiting_question']
    
    await update.message.reply_text(
        "❓ Задайте ваш вопрос:\n\nОпишите вашу ситуацию или задайте вопрос, и мы обязательно ответим.",
        reply_markup=back_to_main_keyboard()
    )

async def process_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка шагов вопроса"""
    user_data = context.user_data
    state = user_data.get('question_state', 0)
    text = update.message.text
    
    if text == '🏠 Главное меню':
        user_data.clear()
        await update.message.reply_text(
            "🏠 Главное меню",
            reply_markup=main_menu_keyboard()
        )
        return
    
    if state == QUESTION_STATES['waiting_question']:
        user_data['question']['question_text'] = text
        user_data['question_state'] = QUESTION_STATES['waiting_name']
        await update.message.reply_text(
            "👤 Введите ваше имя:",
            reply_markup=back_to_main_keyboard()
        )
    
    elif state == QUESTION_STATES['waiting_name']:
        user_data['question']['client_name'] = text
        user_data['question_state'] = QUESTION_STATES['waiting_phone']
        await update.message.reply_text(
            "📞 Введите ваш телефон (или отправьте 'пропустить'):",
            reply_markup=back_to_main_keyboard()
        )
    
    elif state == QUESTION_STATES['waiting_phone']:
        phone = None if text.lower() in ['пропустить', 'skip', ''] else text
        user_data['question']['client_phone'] = phone
        
        # Создаем вопрос
        question_id = await create_question(
            user_id=update.effective_user.id,
            question_text=user_data['question']['question_text'],
            client_name=user_data['question']['client_name'],
            client_phone=phone
        )
        
        # Отправляем уведомление администраторам
        question_info = f"""
❓ Новый вопрос от клиента

ID: {question_id}
Имя: {user_data['question']['client_name']}
Телефон: {phone or 'не указан'}
Вопрос: {user_data['question']['question_text']}
"""
        
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(chat_id=admin_id, text=question_info)
            except:
                pass
        
        await update.message.reply_text(
            """
✅ Ваш вопрос отправлен!

Мы свяжемся с вами в ближайшее время.

Спасибо за обращение!
""",
            reply_markup=main_menu_keyboard()
        )
        
        user_data.clear()
