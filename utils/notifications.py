"""
Модуль для отправки уведомлений клиентам
"""
import logging
from telegram import Bot
from telegram.error import TelegramError

logger = logging.getLogger(__name__)


async def notify_client_status_change(bot: Bot, user_id: int, appointment: dict, new_status: str):
    """
    Отправить уведомление клиенту об изменении статуса заявки

    Args:
        bot: экземпляр бота для отправки сообщений
        user_id: telegram ID клиента
        appointment: данные заявки
        new_status: новый статус заявки
    """
    if not user_id:
        logger.warning(f"Не удалось отправить уведомление: user_id не указан")
        return False

    # Формируем сообщение в зависимости от статуса
    status_messages = {
        'confirmed': (
            "✅ **Ваша заявка подтверждена!**\n\n"
            f"📝 **Услуга:** {appointment.get('service_type', 'не указана')}\n"
            f"👤 **ФИО:** {appointment.get('client_name', 'не указано')}\n"
        ),
        'cancelled': (
            "❌ **Ваша заявка отменена**\n\n"
            f"📝 **Услуга:** {appointment.get('service_type', 'не указана')}\n"
            f"👤 **ФИО:** {appointment.get('client_name', 'не указано')}\n"
        ),
        'completed': (
            "✔️ **Ваша заявка выполнена!**\n\n"
            f"📝 **Услуга:** {appointment.get('service_type', 'не указана')}\n"
            "Спасибо, что воспользовались нашими услугами!\n"
        ),
        'payment_sent': (
            "💳 **Вам отправлен счёт на оплату**\n\n"
            f"📝 **Услуга:** {appointment.get('service_type', 'не указана')}\n"
        ),
    }

    base_msg = status_messages.get(new_status)
    if not base_msg:
        logger.warning(f"Неизвестный статус для уведомления: {new_status}")
        return False

    msg = base_msg

    # Добавляем дату/время если есть
    if appointment.get('appointment_date'):
        msg += f"📅 **Дата:** {appointment['appointment_date']}\n"
    if appointment.get('appointment_time'):
        msg += f"⏰ **Время:** {appointment['appointment_time']}\n"

    # Добавляем контактную информацию
    if new_status == 'confirmed':
        msg += "\n📍 **Адрес:** Санкт-Петербург, Удельный пр., д. 5, оф. 406 (2 этаж)\n"
        msg += "📞 **Телефон:** +7 (812) 309-95-42\n"
        msg += "\nЖдём вас!"

    elif new_status == 'cancelled':
        msg += "\nЕсли у вас есть вопросы, свяжитесь с нами:\n"
        msg += "📞 +7 (812) 309-95-42"

    try:
        await bot.send_message(
            chat_id=user_id,
            text=msg,
            parse_mode='Markdown'
        )
        logger.info(f"Уведомление отправлено клиенту {user_id} о статусе {new_status}")
        return True
    except TelegramError as e:
        logger.error(f"Ошибка отправки уведомления клиенту {user_id}: {e}")
        return False
