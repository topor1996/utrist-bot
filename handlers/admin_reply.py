from telegram import Update
from telegram.ext import ContextTypes
from database import is_admin, get_question_by_id, update_question_status
import logging

logger = logging.getLogger(__name__)

async def admin_reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ответа администратора на вопрос"""
    user_data = context.user_data
    
    # Проверяем, идет ли процесс ответа на вопрос (быстрая проверка)
    if 'replying_to_question' not in user_data:
        # Не обрабатываем, пусть другие обработчики попробуют
        # В python-telegram-bot, если обработчик ничего не делает (не отправляет сообщения),
        # обработка продолжается к следующему обработчику
        logger.debug(f"admin_reply_handler: нет replying_to_question, пропускаем сообщение")
        return
    
    user_id = update.effective_user.id
    
    # Проверяем, является ли пользователь администратором
    if not await is_admin(user_id):
        # Если не администратор, но есть replying_to_question, очищаем (на всякий случай)
        user_data.pop('replying_to_question', None)
        user_data.pop('replying_to_user', None)
        logger.debug(f"admin_reply_handler: пользователь {user_id} не администратор, пропускаем сообщение")
        return
    
    question_id = user_data.get('replying_to_question')
    target_user_id = user_data.get('replying_to_user')
    reply_text = update.message.text
    
    if not question_id or not target_user_id:
        await update.message.reply_text("❌ Ошибка: не найдена информация о вопросе.")
        user_data.pop('replying_to_question', None)
        user_data.pop('replying_to_user', None)
        return
    
    try:
        # Получаем информацию о вопросе
        question = await get_question_by_id(question_id)
        if not question:
            await update.message.reply_text("❌ Вопрос не найден.")
            user_data.pop('replying_to_question', None)
            user_data.pop('replying_to_user', None)
            return
        
        # Отправляем ответ пользователю
        try:
            answer_message = f"""
💬 **Ответ на ваш вопрос:**

{reply_text}

---
Ваш вопрос: {question['question_text']}
"""
            await context.bot.send_message(
                chat_id=target_user_id,
                text=answer_message,
                parse_mode='Markdown'
            )
            
            # Отмечаем вопрос как отвеченный
            await update_question_status(question_id, 'answered')
            
            # Подтверждаем администратору
            await update.message.reply_text(
                f"✅ Ответ отправлен пользователю!\n\nВопрос #{question_id} отмечен как отвеченный."
            )
            
            logger.info(f"Администратор {user_id} ответил на вопрос #{question_id} пользователю {target_user_id}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки ответа пользователю {target_user_id}: {e}")
            await update.message.reply_text(
                f"❌ Ошибка отправки ответа: {e}\n\nВозможно, пользователь заблокировал бота."
            )
        
        # Очищаем состояние
        user_data.pop('replying_to_question', None)
        user_data.pop('replying_to_user', None)
        
    except Exception as e:
        logger.error(f"Ошибка обработки ответа администратора: {e}")
        await update.message.reply_text("❌ Произошла ошибка при отправке ответа.")
        user_data.pop('replying_to_question', None)
        user_data.pop('replying_to_user', None)
