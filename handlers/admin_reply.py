from telegram import Update
from telegram.ext import ContextTypes
from database import is_admin, get_question_by_id, update_question_status, get_appointment_by_id, update_appointment_status
import logging

logger = logging.getLogger(__name__)


async def admin_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик процесса отправки в оплату"""
    user_data = context.user_data

    # Проверяем, идет ли процесс оплаты
    if 'payment_state' not in user_data:
        return

    user_id = update.effective_user.id

    # Проверяем, является ли пользователь администратором
    if not await is_admin(user_id):
        user_data.pop('payment_state', None)
        user_data.pop('payment_appointment_id', None)
        user_data.pop('payment_user_id', None)
        user_data.pop('payment_amount', None)
        user_data.pop('payment_service', None)
        user_data.pop('payment_client_name', None)
        return

    payment_state = user_data.get('payment_state')
    text = update.message.text.strip()

    # Проверка на отмену
    if text == '/admin':
        _clear_payment_state(user_data)
        return

    if payment_state == 'waiting_amount':
        # Ожидаем сумму
        try:
            # Убираем пробелы, запятые, точки из числа
            amount_str = text.replace(' ', '').replace(',', '.').replace('₽', '').replace('руб', '').replace('р', '')
            amount = float(amount_str)

            if amount <= 0:
                await update.message.reply_text(
                    "❌ Сумма должна быть больше 0. Введите сумму ещё раз:"
                )
                return

            # Сохраняем сумму и переходим к запросу ссылки
            user_data['payment_amount'] = amount
            user_data['payment_state'] = 'waiting_link'

            await update.message.reply_text(
                f"💰 Сумма: {amount:,.0f} ₽\n\n"
                f"Теперь введите ссылку на оплату:\n"
                f"(или введите 'skip' чтобы отправить без ссылки)\n\n"
                f"Для отмены нажмите /admin"
            )

        except ValueError:
            await update.message.reply_text(
                "❌ Некорректная сумма. Введите число (например: 7000):"
            )

    elif payment_state == 'waiting_link':
        # Ожидаем ссылку на оплату
        appointment_id = user_data.get('payment_appointment_id')
        target_user_id = user_data.get('payment_user_id')
        amount = user_data.get('payment_amount')
        service = user_data.get('payment_service', 'Услуга')
        client_name = user_data.get('payment_client_name', 'Клиент')

        if not appointment_id or not target_user_id or not amount:
            await update.message.reply_text("❌ Ошибка: потеряны данные заявки. Начните заново.")
            _clear_payment_state(user_data)
            return

        # Проверяем, это ссылка или skip
        payment_link = None
        if text.lower() != 'skip':
            # Проверяем, похоже ли на ссылку
            if text.startswith('http://') or text.startswith('https://'):
                payment_link = text
            else:
                await update.message.reply_text(
                    "❌ Это не похоже на ссылку. Введите ссылку, начинающуюся с http:// или https://\n"
                    "(или 'skip' чтобы отправить без ссылки):"
                )
                return

        try:
            # Формируем сообщение для клиента
            if payment_link:
                client_message = f"""
💳 **Оплата услуги**

📝 Услуга: {service}
💰 Сумма к оплате: {amount:,.0f} ₽

👉 Ссылка для оплаты:
{payment_link}

После оплаты мы свяжемся с вами для подтверждения.
"""
            else:
                client_message = f"""
💳 **Оплата услуги**

📝 Услуга: {service}
💰 Сумма к оплате: {amount:,.0f} ₽

Для оплаты свяжитесь с нами:
📞 8 (812) 985-95-74
"""

            # Отправляем клиенту
            await context.bot.send_message(
                chat_id=target_user_id,
                text=client_message,
                parse_mode='Markdown'
            )

            # Обновляем статус заявки
            await update_appointment_status(appointment_id, 'payment_sent')

            # Подтверждаем администратору
            await update.message.reply_text(
                f"✅ Счёт на оплату отправлен клиенту!\n\n"
                f"📋 Заявка #{appointment_id}\n"
                f"👤 Клиент: {client_name}\n"
                f"💰 Сумма: {amount:,.0f} ₽\n"
                f"{'🔗 Ссылка: ' + payment_link if payment_link else '📞 Без ссылки (клиенту отправлен телефон)'}"
            )

            logger.info(f"Администратор {user_id} отправил счёт на {amount} руб. клиенту {target_user_id} по заявке #{appointment_id}")

        except Exception as e:
            logger.error(f"Ошибка отправки счёта клиенту {target_user_id}: {e}")
            await update.message.reply_text(
                f"❌ Ошибка отправки: {e}\n\nВозможно, пользователь заблокировал бота."
            )

        # Очищаем состояние
        _clear_payment_state(user_data)


def _clear_payment_state(user_data):
    """Очистка состояния оплаты"""
    user_data.pop('payment_state', None)
    user_data.pop('payment_appointment_id', None)
    user_data.pop('payment_user_id', None)
    user_data.pop('payment_amount', None)
    user_data.pop('payment_service', None)
    user_data.pop('payment_client_name', None)

async def admin_reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ответа администратора на вопрос"""
    user_data = context.user_data
    
    # Проверяем, идет ли процесс ответа на вопрос (быстрая проверка)
    if 'replying_to_question' not in user_data:
        # Не обрабатываем, пусть другие обработчики попробуют
        # В python-telegram-bot, если обработчик ничего не делает (не отправляет сообщения),
        # обработка продолжается к следующему обработчику
        # НО: если мы просто return, обработка может не продолжиться
        # Поэтому мы НЕ должны регистрировать этот обработчик для всех сообщений
        # Вместо этого, он должен быть только для администраторов, которые отвечают на вопросы
        # Но так как мы не можем динамически менять фильтры, просто возвращаемся
        logger.debug(f"admin_reply_handler: нет replying_to_question, пропускаем сообщение '{update.message.text[:50] if update.message else 'N/A'}'")
        # ВАЖНО: не возвращаемся, просто ничего не делаем - это позволит следующему обработчику обработать сообщение
        # Но на самом деле, если мы здесь, значит unified_message_handler уже обработал сообщение
        # Поэтому мы просто ничего не делаем
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
