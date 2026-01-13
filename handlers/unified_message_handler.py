"""
Универсальный обработчик сообщений
Объединяет логику process_simple_appointment и service_detail_handler
"""
from telegram import Update
from telegram.ext import ContextTypes
import logging
from .simple_appointment import process_simple_appointment, SIMPLE_APPOINTMENT_STATES
from .services import service_detail_handler

logger = logging.getLogger(__name__)

async def unified_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Универсальный обработчик сообщений - сначала проверяет процесс записи, потом выбор услуги"""
    user_data = context.user_data
    state = user_data.get('simple_appointment_state', 0)
    question_state = user_data.get('question_state', 0)
    
    logger.info(f"unified_message_handler вызван: state={state}, question_state={question_state}, text='{update.message.text[:50]}'")
    
    # Если идет процесс вопроса, НЕ обрабатываем - пусть ConversationHandler обработает
    if question_state != 0:
        logger.info(f"unified_message_handler: идет процесс вопроса (question_state={question_state}), пропускаем")
        return
    
    # Если идет процесс записи, обрабатываем через process_simple_appointment
    if state != 0:
        logger.info(f"unified_message_handler: идет процесс записи (state={state}), обрабатываем через process_simple_appointment")
        return await process_simple_appointment(update, context)
    
    # Если нет процесса записи, обрабатываем через service_detail_handler
    logger.info(f"unified_message_handler: нет процесса записи, обрабатываем через service_detail_handler")
    return await service_detail_handler(update, context)
