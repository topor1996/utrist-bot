from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database import create_appointment
from keyboards.main_menu import main_menu_keyboard, cancel_keyboard
from config import ADMIN_IDS, COMPANY_PHONE
from utils.validators import validate_phone as validate_phone_util, validate_email as validate_email_util
import logging

logger = logging.getLogger(__name__)

# Состояния для упрощенной записи
SIMPLE_APPOINTMENT_STATES = {
    'waiting_name': 1,
    'waiting_phone': 2,
    'waiting_email': 3,
    'waiting_confirm': 4,
}

async def start_simple_appointment(update: Update, context: ContextTypes.DEFAULT_TYPE, service_type: str):
    """Начало упрощенного процесса записи"""
    user_data = context.user_data
    user_data['simple_appointment'] = {'service_type': service_type}
    user_data['simple_appointment_state'] = SIMPLE_APPOINTMENT_STATES['waiting_name']
    
    text = f"""
📝 Заявка на услугу: {service_type}

Для оформления заявки нам нужна следующая информация:

👤 **ФИО** (полное имя)
📞 **Номер телефона**
📧 **Email адрес**

Начнем с вашего имени. Пожалуйста, введите ваше **полное ФИО**:
"""
    
    await update.message.reply_text(
        text,
        parse_mode='Markdown'
    )

async def process_simple_appointment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка шагов упрощенной записи"""
    user_data = context.user_data
    state = user_data.get('simple_appointment_state', 0)
    text = update.message.text
    
    logger.info(f"process_simple_appointment вызван: state={state}, text='{text[:50]}', user_data keys={list(user_data.keys())}")
    
    # Если нет активного процесса записи, не обрабатываем
    # В python-telegram-bot, если обработчик ничего не делает (не отправляет сообщения),
    # обработка продолжается к следующему обработчику.
    # Просто выходим без обработки - это позволит service_detail_handler обработать сообщение
    if state == 0:
        # Не обрабатываем, пусть другие обработчики попробуют
        logger.info(f"process_simple_appointment: state=0, пропускаем сообщение '{text[:50]}'")
        # Просто return без значения - обработка продолжится к следующему обработчику
        return
    
    logger.info(f"process_simple_appointment: обрабатываем сообщение, state={state}, text={text[:50]}")
    
    # Проверяем отмену записи или возврат в главное меню ПЕРЕД обработкой состояния
    if text in ['🏠 Главное меню', '🔙 Главное меню', '❌ Отменить запись']:
        user_data.clear()
        if text == '❌ Отменить запись':
            await update.message.reply_text(
                "❌ Запись отменена.\n\n🏠 Главное меню",
                reply_markup=main_menu_keyboard()
            )
        else:
            await update.message.reply_text(
                "🏠 Главное меню",
                reply_markup=main_menu_keyboard()
            )
        return
    
    if state == SIMPLE_APPOINTMENT_STATES['waiting_name']:
        logger.info(f"Обрабатываем ФИО: '{text}'")
        if len(text.strip()) < 3:
            logger.warning(f"ФИО слишком короткое: '{text}'")
            await update.message.reply_text(
                "❌ Пожалуйста, введите ваше полное имя (минимум 3 символа):"
            )
            return
        
        # Убеждаемся, что simple_appointment существует
        if 'simple_appointment' not in user_data:
            logger.error("simple_appointment не найден в user_data!")
            user_data['simple_appointment'] = {}
        
        user_data['simple_appointment']['client_name'] = text.strip()
        user_data['simple_appointment_state'] = SIMPLE_APPOINTMENT_STATES['waiting_phone']
        
        logger.info(f"ФИО получено: {text.strip()}, переходим к телефону. user_data = {user_data}")
        logger.info(f"Новое состояние: {user_data.get('simple_appointment_state')}")
        
        try:
            await update.message.reply_text(
                """
📞 Отлично! Теперь введите ваш **номер телефона**:

Можно в любом формате, например:
• +7 (812) 123-45-67
• 8 (812) 123-45-67
• 8121234567
""",
                parse_mode='Markdown',
                reply_markup=cancel_keyboard()
            )
            logger.info("Запрос на телефон отправлен успешно")
        except Exception as e:
            logger.error(f"Ошибка отправки запроса на телефон: {e}")
            import traceback
            logger.error(traceback.format_exc())
        return  # Явный return после обработки ФИО

    elif state == SIMPLE_APPOINTMENT_STATES['waiting_phone']:
        is_valid, result = validate_phone_util(text)
        if not is_valid:
            await update.message.reply_text(
                f"❌ {result}\n\nПожалуйста, введите корректный номер телефона:",
                reply_markup=cancel_keyboard()
            )
            return  # Возвращаемся, ждем повторного ввода

        # result содержит отформатированный номер
        user_data['simple_appointment']['client_phone'] = result
        user_data['simple_appointment_state'] = SIMPLE_APPOINTMENT_STATES['waiting_email']

        logger.info(f"Телефон получен: {result}, переходим к email. user_data = {user_data}")
        
        await update.message.reply_text(
            """
📧 Отлично! Теперь введите ваш **email адрес**:

Например: ivanov@example.com
""",
            parse_mode='Markdown',
            reply_markup=cancel_keyboard()
        )
        return  # Переход к вводу email

    elif state == SIMPLE_APPOINTMENT_STATES['waiting_email']:
        is_valid, result = validate_email_util(text)
        if not is_valid:
            await update.message.reply_text(
                f"❌ {result}\n\nПожалуйста, введите корректный email адрес:",
                reply_markup=cancel_keyboard()
            )
            return  # Возвращаемся, ждем повторного ввода

        # result содержит нормализованный email
        user_data['simple_appointment']['client_email'] = result
        user_data['simple_appointment_state'] = SIMPLE_APPOINTMENT_STATES['waiting_confirm']
        
        logger.info(f"Email введен, показываем подтверждение. user_data = {user_data}")
        
        # Показываем данные для подтверждения
        confirm_text = f"""
✅ **Проверьте ваши данные:**

📝 Услуга: {user_data['simple_appointment']['service_type']}
👤 ФИО: {user_data['simple_appointment']['client_name']}
📞 Телефон: {user_data['simple_appointment']['client_phone']}
📧 Email: {user_data['simple_appointment']['client_email']}

Если все верно, нажмите кнопку "Отправить заявку" ниже.
"""
        
        keyboard = [
            [InlineKeyboardButton('✅ Отправить заявку', callback_data='submit_appointment')],
            [InlineKeyboardButton('❌ Отменить', callback_data='cancel_appointment')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            confirm_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

        logger.info("Сообщение с кнопками отправлено")
        return  # Явный return после обработки email

    elif state == SIMPLE_APPOINTMENT_STATES['waiting_confirm']:
        # Это не должно происходить, но на всякий случай
        await update.message.reply_text(
            "Пожалуйста, используйте кнопки для подтверждения заявки."
        )
        return


async def submit_appointment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик отправки заявки"""
    query = update.callback_query
    await query.answer("Отправляем заявку...")
    
    user_data = context.user_data
    appointment_data = user_data.get('simple_appointment', {})
    
    logger.info(f"submit_appointment_callback вызван")
    logger.info(f"user_data = {user_data}")
    logger.info(f"appointment_data = {appointment_data}")
    
    if not appointment_data:
        logger.error("appointment_data пустой!")
        await query.edit_message_text("❌ Ошибка: данные заявки не найдены. Пожалуйста, начните заново.")
        return
    
    # Проверяем, что все данные есть
    required_fields = ['service_type', 'client_name', 'client_phone', 'client_email']
    missing_fields = [field for field in required_fields if not appointment_data.get(field)]
    
    logger.info(f"Проверка полей. missing_fields = {missing_fields}")
    logger.info(f"appointment_data keys = {list(appointment_data.keys())}")
    
    if missing_fields:
        error_msg = f"❌ Ошибка: не заполнены поля: {', '.join(missing_fields)}. Пожалуйста, начните заново."
        logger.error(error_msg)
        await query.edit_message_text(error_msg)
        return
    
    try:
        logger.info(f"Создаем заявку с данными: {appointment_data}")
        # Создаем заявку
        appointment_id = await create_appointment(
            user_id=query.from_user.id,
            service_type=appointment_data['service_type'],
            client_name=appointment_data['client_name'],
            client_phone=appointment_data['client_phone'],
            client_email=appointment_data['client_email']
        )
        logger.info(f"Заявка создана с ID: {appointment_id}")
    except Exception as e:
        import traceback
        logger.error(f"Ошибка создания заявки: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        await query.edit_message_text(
            "❌ Произошла ошибка при создании заявки. Пожалуйста, попробуйте позже или свяжитесь с нами по телефону."
        )
        return
    
    # Отправляем уведомление администраторам
    from datetime import datetime
    appointment_info = f"""
📋 **Новая заявка на услугу**

🆔 ID: {appointment_id}
📝 Услуга: {appointment_data['service_type']}
👤 ФИО: {appointment_data['client_name']}
📞 Телефон: {appointment_data['client_phone']}
📧 Email: {appointment_data['client_email']}
⏰ Дата создания: {datetime.now().strftime('%d.%m.%Y %H:%M')}
"""
    
    # Отправляем уведомление администраторам
    notification_sent = False
    for admin_id in ADMIN_IDS:
        try:
            from keyboards.admin import appointment_actions_keyboard
            await context.bot.send_message(
                chat_id=admin_id,
                text=appointment_info,
                parse_mode='Markdown',
                reply_markup=appointment_actions_keyboard(appointment_id)
            )
            notification_sent = True
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления админу {admin_id}: {e}")
    
    if not notification_sent and ADMIN_IDS:
        logger.warning(f"ВНИМАНИЕ: Уведомление администраторам не отправлено! Проверьте ADMIN_IDS в настройках.")
    
    # Отправляем красивое сообщение клиенту
    thank_you_text = f"""
✅ **Спасибо за вашу заявку!**

Ваша заявка на услугу **"{appointment_data['service_type']}"** успешно принята.

📋 **Ваши данные:**
👤 ФИО: {appointment_data['client_name']}
📞 Телефон: {appointment_data['client_phone']}
📧 Email: {appointment_data['client_email']}

Наш специалист свяжется с вами в ближайшее время для уточнения деталей.

Если у вас есть срочный вопрос, вы можете позвонить нам по телефону {COMPANY_PHONE}

Спасибо, что выбрали нас! 🙏
"""
    
    # Кнопки
    phone_clean = COMPANY_PHONE.replace(" ", "").replace("(", "").replace(")", "").replace("-", "")
    keyboard = [
        [InlineKeyboardButton('📞 Позвонить', url=f'tel:{phone_clean}')],
        [InlineKeyboardButton('🔙 Назад к услугам', callback_data='back_to_services')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Редактируем сообщение с благодарностью (вместо двух сообщений)
    try:
        await query.edit_message_text(
            thank_you_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        logger.info("Сообщение 'Спасибо' отправлено клиенту")
    except Exception as e:
        logger.error(f"Ошибка редактирования сообщения: {e}")
        # Пробуем отправить как новое сообщение
        try:
            await query.message.reply_text(
                thank_you_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        except Exception as e2:
            logger.error(f"Ошибка отправки сообщения клиенту: {e2}")
            # Пытаемся отправить хотя бы простое сообщение
            try:
                await query.message.reply_text(
                    "✅ Спасибо за вашу заявку! Наш специалист свяжется с вами в ближайшее время."
                )
            except Exception as e3:
                logger.error(f"Критическая ошибка: не удалось отправить fallback сообщение: {e3}")
    
    user_data.clear()
    logger.info("Заявка успешно обработана, user_data очищен")

async def cancel_appointment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик отмены заявки"""
    query = update.callback_query
    await query.answer()

    context.user_data.clear()

    from keyboards.services import services_keyboard

    # Редактируем сообщение с информацией об отмене
    await query.edit_message_text(
        "❌ Заявка отменена.\n\nВыберите категорию услуг в меню ниже.",
        reply_markup=None
    )

    # Показываем клавиатуру с категориями
    await query.message.reply_text(
        "Выберите категорию:",
        reply_markup=services_keyboard()
    )
