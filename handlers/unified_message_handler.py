"""
Универсальный обработчик сообщений
Объединяет логику process_simple_appointment и service_detail_handler
Также обрабатывает ответы администратора на вопросы и процесс оплаты
"""
from telegram import Update
from telegram.ext import ContextTypes
import logging
from .simple_appointment import process_simple_appointment, SIMPLE_APPOINTMENT_STATES
from .services import service_detail_handler
from .admin_reply import admin_reply_handler, admin_payment_handler

logger = logging.getLogger(__name__)

async def unified_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Универсальный обработчик сообщений - сначала проверяет процесс записи, потом выбор услуги"""
    user_data = context.user_data
    state = user_data.get('simple_appointment_state', 0)
    question_state = user_data.get('question_state', 0)

    logger.info(f"unified_message_handler вызван: state={state}, question_state={question_state}, text='{update.message.text[:50]}'")

    # Проверяем, идет ли процесс оплаты (администратор вводит сумму/ссылку)
    if 'payment_state' in user_data:
        logger.info(f"unified_message_handler: обнаружен процесс оплаты, передаем в admin_payment_handler")
        return await admin_payment_handler(update, context)

    # Сначала проверяем, идет ли процесс ответа администратора на вопрос
    if 'replying_to_question' in user_data:
        logger.info(f"unified_message_handler: обнаружен процесс ответа администратора, передаем в admin_reply_handler")
        return await admin_reply_handler(update, context)
    
    # Если идет процесс вопроса, НЕ обрабатываем - пусть ConversationHandler обработает
    # ConversationHandler должен быть ПЕРЕД unified_message_handler, поэтому он обработает сообщение первым
    # Но на всякий случай проверяем question_state
    if question_state != 0:
        logger.info(f"unified_message_handler: идет процесс вопроса (question_state={question_state}), пропускаем - пусть ConversationHandler обработает")
        # Не обрабатываем - ConversationHandler должен обработать это сообщение
        # В python-telegram-bot, если обработчик ничего не делает (не отправляет сообщения),
        # обработка продолжается к следующему обработчику
        return
    
    # Если идет процесс записи, обрабатываем через process_simple_appointment
    if state != 0:
        logger.info(f"unified_message_handler: идет процесс записи (state={state}), обрабатываем через process_simple_appointment")
        result = await process_simple_appointment(update, context)
        logger.info(f"unified_message_handler: process_simple_appointment вернул {result}")
        return result
    
    # Если нет процесса записи, обрабатываем через service_detail_handler
    logger.info(f"unified_message_handler: нет процесса записи, обрабатываем через service_detail_handler")
    result = await service_detail_handler(update, context)
    logger.info(f"unified_message_handler: service_detail_handler вернул {result}")
    return result
