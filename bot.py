#!/usr/bin/env python3
"""
Telegram бот для юридической компании "Ваш юрист"
"""

import asyncio
import signal
import sys
import time
import logging
from telegram import Update
from telegram.error import Conflict
from telegram.ext import (
    Application,
    ApplicationHandlerStop,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    ConversationHandler
)

from config import BOT_TOKEN
from database import init_db
from middleware import rate_limit_middleware
from healthcheck import set_bot_started, set_bot_stopped, update_last_activity, start_health_server, stop_health_server
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
    my_appointments_handler,
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
    help_handler,
    menu_handler,
)
from scheduler import start_reminder_scheduler, stop_reminder_scheduler
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
    
    # Хранилище для health check runner и планировщика
    health_runner = None
    reminder_task = None

    # Инициализация БД и health check
    async def post_init(app: Application) -> None:
        nonlocal health_runner, reminder_task
        await init_db()
        logger.info("База данных инициализирована")

        # Запускаем health check сервер
        try:
            health_runner = await start_health_server(port=8080)
            set_bot_started()
        except Exception as e:
            logger.warning(f"Не удалось запустить health check сервер: {e}")

        # Запускаем планировщик напоминаний
        try:
            reminder_task = start_reminder_scheduler(app)
            logger.info("Планировщик напоминаний запущен")
        except Exception as e:
            logger.warning(f"Не удалось запустить планировщик напоминаний: {e}")

    application.post_init = post_init

    # Graceful shutdown
    async def post_shutdown(app: Application) -> None:
        nonlocal health_runner, reminder_task
        set_bot_stopped()
        if reminder_task:
            stop_reminder_scheduler(reminder_task)
        if health_runner:
            await stop_health_server(health_runner)
        logger.info("Бот остановлен корректно")

    application.post_shutdown = post_shutdown

    # Rate limiting middleware - первый обработчик для защиты от спама
    async def rate_limit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик для проверки rate limit"""
        # Обновляем время последней активности для health check
        update_last_activity()

        if await rate_limit_middleware(update, context):
            # Если лимит превышен, прерываем обработку
            raise ApplicationHandlerStop()

    application.add_handler(MessageHandler(filters.ALL, rate_limit_handler), group=-1)

    # Обработчик команды /start
    application.add_handler(CommandHandler("start", start_handler))

    # Команды /help и /menu
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(CommandHandler("menu", menu_handler))
    
    # Обработчик главного меню (ДОЛЖЕН БЫТЬ ПЕРЕД unified_message_handler!)
    # Обрабатывает оба варианта: "🏠 Главное меню" и "🔙 Главное меню"
    application.add_handler(MessageHandler(filters.Regex("^(🏠 Главное меню|🔙 Главное меню)$"), main_menu_handler))
    
    # Обработчик контактов и о компании
    application.add_handler(MessageHandler(filters.Regex("^📍 Контакты$"), contacts_handler))
    application.add_handler(MessageHandler(filters.Regex("^ℹ️ О компании$"), about_handler))

    # Обработчик "Мои записи"
    application.add_handler(MessageHandler(filters.Regex("^📝 Мои записи$"), my_appointments_handler))
    
    # Обработчик админ-панели (ДОЛЖЕН БЫТЬ ПЕРЕД универсальным обработчиком услуг!)
    application.add_handler(MessageHandler(filters.Regex("^🔐 Админ-панель$"), admin_handler))
    application.add_handler(MessageHandler(
        filters.Regex("^(📋 Новые заявки|📁 Все заявки|📅 Календарь записей|📊 Статистика|📥 Экспорт данных)$"),
        admin_commands_handler
    ))
    
    # Обработчики услуг
    application.add_handler(MessageHandler(filters.Regex("^📋 Наши услуги$"), services_handler))
    application.add_handler(MessageHandler(filters.Regex("^👔 Юридическим лицам$"), legal_entities_handler))
    application.add_handler(MessageHandler(filters.Regex("^💼 Предпринимателям$"), entrepreneurs_handler))
    application.add_handler(MessageHandler(filters.Regex("^👤 Физическим лицам$"), individuals_handler))
    application.add_handler(MessageHandler(filters.Regex("^🔙 Назад к услугам$"), services_handler))
    
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
    
    # Обработчик вопросов (ConversationHandler) - ДОЛЖЕН БЫТЬ ПЕРЕД unified_message_handler!
    # ConversationHandler имеет приоритет и обрабатывает сообщения, если активен процесс вопроса
    question_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^❓ Задать вопрос$"), question_handler)],
        states={
            QUESTION_STATES['waiting_question']: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^(🏠 Главное меню|🔙 Главное меню)$"), process_question)
            ],
        },
        fallbacks=[MessageHandler(filters.Regex("^(🏠 Главное меню|🔙 Главное меню)$"), main_menu_handler)],
    )
    application.add_handler(question_conv)
    
    # Команда /admin для администраторов
    application.add_handler(CommandHandler("admin", admin_handler))
    
    # Универсальный обработчик сообщений
    # Объединяет логику process_simple_appointment и service_detail_handler
    # Сначала проверяет, идет ли процесс записи, затем обрабатывает выбор услуги
    # НО: не обрабатывает сообщения, если идет процесс вопроса (question_state != 0)
    application.add_handler(MessageHandler(
        filters.TEXT &
        ~filters.COMMAND &
        ~filters.Regex("^(🏠 Главное меню|🔙 Главное меню|📋 Наши услуги|👔 Юридическим лицам|💼 Предпринимателям|👤 Физическим лицам|🔙 Назад к услугам|📍 Контакты|ℹ️ О компании|📞 Записаться на консультацию|📝 Мои записи|❓ Задать вопрос|🔐 Админ-панель|📋 Новые заявки|📁 Все заявки|📅 Календарь записей|📊 Статистика|📥 Экспорт данных)$"),
        unified_message_handler
    ))
    
    # Callback для админ-панели (admin_, appt_, q_, export_, allappt_)
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^(admin_|appt_|q_|export_|allappt_)"))
    
    # Принудительный сброс сессии и удаление webhook перед запуском
    import httpx
    logger.info("Сброс сессии Telegram API...")

    def reset_telegram_session():
        """Сбрасывает сессию Telegram API"""
        with httpx.Client(timeout=30.0) as client:
            # Удаляем webhook и сбрасываем pending updates
            resp = client.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook",
                params={"drop_pending_updates": True}
            )
            logger.info(f"deleteWebhook: {resp.json()}")

            # Делаем несколько коротких getUpdates чтобы "перехватить" сессию
            for i in range(3):
                try:
                    resp = client.post(
                        f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
                        params={"offset": -1, "timeout": 1}
                    )
                    data = resp.json()
                    if data.get('ok'):
                        logger.info(f"getUpdates #{i+1}: OK")
                    else:
                        logger.warning(f"getUpdates #{i+1}: {data}")
                except Exception as e:
                    logger.warning(f"getUpdates #{i+1} error: {e}")
                time.sleep(1)

    try:
        reset_telegram_session()
    except Exception as e:
        logger.warning(f"Ошибка сброса сессии: {e}")

    # Ждём чтобы Telegram API освободил старую сессию
    # 10 секунд обычно достаточно для завершения предыдущего polling
    startup_delay = 10
    logger.info(f"Ожидание {startup_delay} секунд перед запуском polling...")
    time.sleep(startup_delay)

    # Повторный сброс перед запуском
    try:
        reset_telegram_session()
    except Exception as e:
        logger.warning(f"Ошибка повторного сброса сессии: {e}")

    # Запуск бота с обработкой сигналов для graceful shutdown
    logger.info("Бот запущен")

    # run_polling уже обрабатывает SIGINT и SIGTERM корректно
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,  # Игнорируем сообщения, пришедшие пока бот был выключен
        close_loop=False  # Не закрываем event loop автоматически
    )


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Получен сигнал завершения (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)
