"""
Планировщик напоминаний о записях
Запускается в фоне и проверяет, какие напоминания нужно отправить
"""
import asyncio
import logging
from datetime import datetime, timedelta, date, time as dt_time
from telegram import Bot
from telegram.error import TelegramError

from database import (
    get_pending_reminders,
    mark_reminder_sent,
    get_appointments_for_reminder,
    create_reminder
)
from config import BOT_TOKEN

logger = logging.getLogger(__name__)


async def send_reminder(bot: Bot, reminder: dict):
    """Отправить напоминание пользователю"""
    try:
        user_id = reminder['user_id']
        client_name = reminder['client_name']
        service_type = reminder['service_type']
        appt_date = reminder['appointment_date']
        appt_time = reminder['appointment_time']
        reminder_type = reminder['reminder_type']

        if reminder_type == 'day_before':
            message = f"""
🔔 **Напоминание о записи**

{client_name}, напоминаем вам о записи на завтра!

📝 **Услуга:** {service_type}
📅 **Дата:** {appt_date}
⏰ **Время:** {appt_time or 'уточняется'}

📍 Адрес: Санкт-Петербург, Удельный пр., д. 5, оф. 406 (2 этаж)
📞 Телефон: 8 (812) 985-95-74

Если вы не сможете прийти, пожалуйста, сообщите нам заранее.
"""
        else:
            message = f"""
🔔 **Напоминание о записи**

{client_name}, ваша консультация начнётся через час!

📝 **Услуга:** {service_type}
⏰ **Время:** {appt_time}

📍 Адрес: Санкт-Петербург, Удельный пр., д. 5, оф. 406 (2 этаж)
"""

        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode='Markdown'
        )

        await mark_reminder_sent(reminder['id'], 'sent')
        logger.info(f"Напоминание #{reminder['id']} отправлено пользователю {user_id}")

    except TelegramError as e:
        logger.error(f"Ошибка отправки напоминания #{reminder['id']}: {e}")
        await mark_reminder_sent(reminder['id'], 'failed')


async def process_reminders(bot: Bot):
    """Обработать все ожидающие напоминания"""
    try:
        reminders = await get_pending_reminders()

        for reminder in reminders:
            await send_reminder(bot, reminder)
            await asyncio.sleep(0.1)  # Небольшая задержка между отправками

    except Exception as e:
        logger.error(f"Ошибка обработки напоминаний: {e}")


async def schedule_reminders_for_tomorrow():
    """Создать напоминания для записей на завтра"""
    try:
        tomorrow = date.today() + timedelta(days=1)
        appointments = await get_appointments_for_reminder(tomorrow)

        for appointment in appointments:
            # Напоминание за день (сегодня в 18:00)
            today = date.today()
            scheduled_at = datetime.combine(today, dt_time(18, 0))

            # Если уже позже 18:00, ставим на текущее время + 5 минут
            if datetime.now() >= scheduled_at:
                scheduled_at = datetime.now() + timedelta(minutes=5)

            await create_reminder(
                appointment_id=appointment['id'],
                reminder_type='day_before',
                scheduled_at=scheduled_at
            )
            logger.info(f"Создано напоминание для записи #{appointment['id']} на {scheduled_at}")

    except Exception as e:
        logger.error(f"Ошибка создания напоминаний: {e}")


async def reminder_loop(bot: Bot):
    """Основной цикл планировщика напоминаний"""
    logger.info("Планировщик напоминаний запущен")

    while True:
        try:
            # Проверяем и отправляем напоминания каждые 5 минут
            await process_reminders(bot)

            # Раз в час проверяем, нужно ли создать новые напоминания
            current_minute = datetime.now().minute
            if current_minute < 5:  # В начале каждого часа
                await schedule_reminders_for_tomorrow()

        except Exception as e:
            logger.error(f"Ошибка в цикле напоминаний: {e}")

        await asyncio.sleep(300)  # 5 минут


def start_reminder_scheduler(application) -> asyncio.Task:
    """Запустить планировщик напоминаний"""
    bot = application.bot
    return asyncio.create_task(reminder_loop(bot))


def stop_reminder_scheduler(task: asyncio.Task):
    """Остановить планировщик напоминаний"""
    if task and not task.done():
        task.cancel()
        logger.info("Планировщик напоминаний остановлен")
