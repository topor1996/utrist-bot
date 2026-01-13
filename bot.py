#!/usr/bin/env python3
"""
Telegram бот для юридической компании "Ваш юрист"
"""

import asyncio
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    ConversationHandler
)

from config import BOT_TOKEN
from database import init_db
from handlers import (
    start_handler,
    main_menu_handler,
    services_handler,
    legal_entities_handler,
    entrepreneurs_handler,
    individuals_handler,
    service_detail_handler,
    service_callback_handler,
    appointment_handler,
    process_appointment,
    process_simple_appointment,
    SIMPLE_APPOINTMENT_STATES,
    submit_appointment_callback,
    cancel_appointment_callback,
    question_handler,
    process_question,
    admin_handler,
    admin_commands_handler,
    admin_callback_handler,
    admin_reply_handler,
    contacts_handler,
    about_handler,
    unified_message_handler,
)
from handlers.appointment import APPOINTMENT_STATES
from handlers.question import QUESTION_STATES

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Основная функция запуска бота"""
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Инициализация БД
    async def post_init(app: Application) -> None:
        await init_db()
        logger.info("База данных инициализирована")
    
    application.post_init = post_init
    
    # Обработчик команды /start
    application.add_handler(CommandHandler("start", start_handler))
    
    # Обработчик главного меню
    application.add_handler(MessageHandler(filters.Regex("^🏠 Главное меню$"), main_menu_handler))
    
    # Обработчик контактов и о компании
    application.add_handler(MessageHandler(filters.Regex("^📍 Контакты$"), contacts_handler))
    application.add_handler(MessageHandler(filters.Regex("^ℹ️ О компании$"), about_handler))
    
    # Обработчик админ-панели (ДОЛЖЕН БЫТЬ ПЕРЕД универсальным обработчиком услуг!)
    application.add_handler(MessageHandler(filters.Regex("^🔐 Админ-панель$"), admin_handler))
    application.add_handler(MessageHandler(
        filters.Regex("^(📋 Новые заявки|📅 Календарь записей|📊 Статистика)$"),
        admin_commands_handler
    ))
    
    # Обработчики услуг
    application.add_handler(MessageHandler(filters.Regex("^📋 Наши услуги$"), services_handler))
    application.add_handler(MessageHandler(filters.Regex("^👔 Юридическим лицам$"), legal_entities_handler))
    application.add_handler(MessageHandler(filters.Regex("^💼 Предпринимателям$"), entrepreneurs_handler))
    application.add_handler(MessageHandler(filters.Regex("^👤 Физическим лицам$"), individuals_handler))
    application.add_handler(MessageHandler(filters.Regex("^🔙 Назад к услугам$"), services_handler))
    
    # Обработчик ответа администратора на вопрос (ДОЛЖЕН БЫТЬ ПЕРЕД универсальным обработчиком!)
    # Проверяет, идет ли процесс ответа на вопрос, и если да, обрабатывает ответ
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        admin_reply_handler
    ))
    
    # Универсальный обработчик сообщений
    # Объединяет логику process_simple_appointment и service_detail_handler
    # Сначала проверяет, идет ли процесс записи, затем обрабатывает выбор услуги
    application.add_handler(MessageHandler(
        filters.TEXT & 
        ~filters.COMMAND & 
        ~filters.Regex("^(🏠 Главное меню|📋 Наши услуги|👔 Юридическим лицам|💼 Предпринимателям|👤 Физическим лицам|🔙 Назад к услугам|📍 Контакты|ℹ️ О компании|📞 Записаться на консультацию|❓ Задать вопрос|🔐 Админ-панель|📋 Новые заявки|📅 Календарь записей|📊 Статистика)$"),
        unified_message_handler
    ))
    
    # Обработчик записи на консультацию (ConversationHandler)
    appointment_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📞 Записаться на консультацию$"), appointment_handler)],
        states={
            APPOINTMENT_STATES['waiting_service']: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_appointment)
            ],
            APPOINTMENT_STATES['waiting_name']: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_appointment)
            ],
            APPOINTMENT_STATES['waiting_phone']: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_appointment)
            ],
            APPOINTMENT_STATES['waiting_date']: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_appointment)
            ],
            APPOINTMENT_STATES['waiting_time']: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_appointment)
            ],
            APPOINTMENT_STATES['waiting_comment']: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_appointment)
            ],
        },
        fallbacks=[MessageHandler(filters.Regex("^🏠 Главное меню$"), main_menu_handler)],
    )
    application.add_handler(appointment_conv)
    
    # Callback для услуг
    application.add_handler(CallbackQueryHandler(service_callback_handler, pattern="^(start_appointment|back_to_services)$"))
    
    # Callback для отправки/отмены заявки
    application.add_handler(CallbackQueryHandler(submit_appointment_callback, pattern="^submit_appointment$"))
    application.add_handler(CallbackQueryHandler(cancel_appointment_callback, pattern="^cancel_appointment$"))
    
    # Обработчик вопросов (ConversationHandler)
    question_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^❓ Задать вопрос$"), question_handler)],
        states={
            QUESTION_STATES['waiting_question']: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_question)
            ],
        },
        fallbacks=[MessageHandler(filters.Regex("^🏠 Главное меню$"), main_menu_handler)],
    )
    application.add_handler(question_conv)
    
    # Обработчик админ-панели
    application.add_handler(CommandHandler("admin", admin_handler))
    application.add_handler(MessageHandler(filters.Regex("^🔐 Админ-панель$"), admin_handler))
    application.add_handler(MessageHandler(
        filters.Regex("^(📋 Новые заявки|📅 Календарь записей|📊 Статистика)$"),
        admin_commands_handler
    ))
    
    # Callback для админ-панели
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^(admin_|appt_|q_)"))
    
    # Запуск бота
    logger.info("Бот запущен")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
