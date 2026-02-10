from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from keyboards.services import (
    services_keyboard,
    legal_entities_keyboard,
    entrepreneurs_keyboard,
    individuals_keyboard
)
from keyboards.main_menu import main_menu_keyboard, cancel_keyboard
from data.prices import get_service_info
import logging

logger = logging.getLogger(__name__)

async def services_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик раздела услуг"""
    text = """
📋 Наши услуги

Выберите категорию:
"""
    await update.message.reply_text(
        text,
        reply_markup=services_keyboard()
    )

async def legal_entities_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Услуги для юридических лиц"""
    text = """
👔 Услуги для юридических лиц:

• Регистрация ООО
• Открытие расчетного счета
• Бухгалтерские услуги
• Изменения в устав, ЕГРЮЛ
• Досудебная работа юриста
• Полное судебное сопровождение
• Помощь в исполнении судебных решений
• Составление и правовой анализ договоров
• Консультации юриста
• Абонентское юридическое обслуживание
• Анализ и оптимизация бизнеса

Выберите услугу или запишитесь на консультацию.
"""
    await update.message.reply_text(
        text,
        reply_markup=legal_entities_keyboard()
    )

async def entrepreneurs_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Услуги для предпринимателей"""
    text = """
💼 Услуги для предпринимателей:

• Регистрация ИП в Санкт-Петербурге
• Изменение ЕГРИП
• Ликвидация ИП
• Постановка на учет
• Юридические консультации
• Договорная работа
• Судебное сопровождение
• Бухгалтерские услуги
• Абонентское юридическое обслуживание
"""
    await update.message.reply_text(
        text,
        reply_markup=entrepreneurs_keyboard()
    )

async def individuals_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Услуги для физических лиц"""
    text = """
👤 Услуги для физических лиц:

• Консультации юриста
• Составление исковых заявлений, ведение дел в суде
• Налоговые декларации 3-НДФЛ, налоговый вычет
• Регистрация физического лица в качестве ИП
• Защита прав потребителей
• Сделки с недвижимостью
• Юридическая консультация on-line

Выберите услугу или запишитесь на консультацию.
"""
    await update.message.reply_text(
        text,
        reply_markup=individuals_keyboard()
    )

async def service_detail_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора конкретной услуги"""
    service_name = update.message.text
    
    # Проверяем, не идет ли процесс записи
    # ВАЖНО: проверяем ПЕРЕД любыми другими действиями
    state = context.user_data.get('simple_appointment_state', 0)
    simple_appointment = context.user_data.get('simple_appointment', {})
    
    logger.info(f"service_detail_handler вызван: service_name='{service_name}', state={state}, simple_appointment={simple_appointment}")
    
    # Если идет процесс записи, НЕ обрабатываем это сообщение
    # В python-telegram-bot обработчики вызываются по порядку.
    # Проблема: если обработчик вызывается, но ничего не делает, следующий обработчик может не вызваться.
    # Решение: используем фильтр на уровне MessageHandler, чтобы этот обработчик вообще не вызывался
    # во время процесса записи. Но так как мы не можем динамически менять фильтры,
    # просто выходим без обработки - это должно позволить обработке продолжиться.
    if state != 0:
        logger.info(f"service_detail_handler: пропускаем, идет процесс записи (state={state})")
        # В python-telegram-bot, если обработчик ничего не делает (не отправляет сообщения),
        # обработка должна продолжиться к следующему обработчику.
        # Но на практике это может не работать, поэтому лучше использовать другой подход.
        # Просто выходим без обработки
        return
    
    if simple_appointment:
        logger.info(f"service_detail_handler: пропускаем, есть активная заявка")
        return
    
    logger.info(f"service_detail_handler: обрабатываем выбор услуги: {service_name}")

    # Проверяем, является ли текст известной услугой
    from data.prices import SERVICE_PRICES
    if service_name not in SERVICE_PRICES:
        logger.info(f"service_detail_handler: '{service_name}' не является известной услугой, пропускаем")
        return

    # Сохраняем выбранную услугу в контексте
    context.user_data['selected_service'] = service_name
    logger.info(f"Услуга сохранена в контексте: {service_name}")

    # Получаем информацию об услуге из data/prices.py
    info_text = get_service_info(service_name)

    logger.info(f"Информация об услуге: длина текста={len(info_text)}")
    
    # Кнопки для действий
    keyboard = [
        [InlineKeyboardButton('📝 Оставить заявку', callback_data='start_appointment')],
        [InlineKeyboardButton('🔙 Назад к услугам', callback_data='back_to_services')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    logger.info(f"Отправляем описание услуги с кнопками: {service_name}")
    try:
        result = await update.message.reply_text(
            info_text,
            reply_markup=reply_markup
        )
        logger.info(f"Описание услуги отправлено успешно: {service_name}, message_id={result.message_id}")
    except Exception as e:
        logger.error(f"Ошибка отправки описания услуги '{service_name}': {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Пытаемся отправить хотя бы простое сообщение
        try:
            await update.message.reply_text(
                f"Услуга: {service_name}\n\nДля записи нажмите кнопку ниже.",
                reply_markup=reply_markup
            )
        except Exception as e2:
            logger.error(f"Критическая ошибка: не удалось отправить даже простое сообщение: {e2}")

async def service_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback от кнопок услуг"""
    query = update.callback_query
    await query.answer()
    
    logger.info(f"service_callback_handler вызван с data: {query.data}")
    
    if query.data == 'start_appointment':
        # Защита от двойного нажатия: если уже в процессе записи, игнорируем
        current_state = context.user_data.get('simple_appointment_state', 0)
        if current_state != 0:
            logger.info(f"service_callback_handler: уже в процессе записи (state={current_state}), игнорируем повторное нажатие")
            return

        # Получаем тип услуги из контекста
        service_type = context.user_data.get('selected_service', 'Консультация')
        logger.info(f"Начинаем процесс записи для услуги: {service_type}")

        # Запускаем упрощенный процесс записи
        from .simple_appointment import SIMPLE_APPOINTMENT_STATES

        text = (
            f"📝 Заявка на услугу: {service_type}\n\n"
            "Для оформления заявки нам нужна следующая информация:\n\n"
            "👤 ФИО (полное имя)\n"
            "📞 Номер телефона\n"
            "📧 Email адрес\n\n"
            "Начнем с вашего имени. Пожалуйста, введите ваше полное ФИО:"
        )

        logger.info(f"Отправляем запрос на ввод ФИО для услуги: {service_type}")

        # Сначала редактируем сообщение, потом устанавливаем состояние
        try:
            await query.edit_message_text(text)
        except Exception as e:
            logger.error(f"Ошибка редактирования сообщения: {e}")
            # Если не удалось отредактировать, отправляем новое
            try:
                await query.message.reply_text(text)
            except Exception as e2:
                logger.error(f"Ошибка отправки сообщения: {e2}")
                return

        # Устанавливаем состояние ПОСЛЕ успешной отправки сообщения
        context.user_data['simple_appointment'] = {'service_type': service_type}
        context.user_data['simple_appointment_state'] = SIMPLE_APPOINTMENT_STATES['waiting_name']

        logger.info(f"Запрос на ввод ФИО отправлен. user_data = {context.user_data}")
        return

    elif query.data == 'back_to_services':
        # Просто редактируем сообщение, убирая кнопки
        await query.edit_message_text(
            "📋 Наши услуги — выберите категорию в меню ниже",
            reply_markup=None
        )
        # Показываем клавиатуру с категориями
        await query.message.reply_text(
            "Выберите категорию:",
            reply_markup=services_keyboard()
        )
        return
