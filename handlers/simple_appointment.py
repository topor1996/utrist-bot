from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database import create_appointment
from keyboards.main_menu import main_menu_keyboard
from config import ADMIN_IDS, COMPANY_PHONE
import re

# Состояния для упрощенной записи
SIMPLE_APPOINTMENT_STATES = {
    'waiting_name': 1,
    'waiting_phone': 2,
    'waiting_email': 3,
}

def validate_email(email: str) -> bool:
    """Проверка валидности email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """Проверка валидности телефона"""
    # Убираем все нецифровые символы кроме +
    cleaned = re.sub(r'[^\d+]', '', phone)
    # Проверяем, что есть хотя бы 10 цифр
    digits = re.sub(r'[^\d]', '', cleaned)
    return len(digits) >= 10

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
    
    if text == '🏠 Главное меню':
        user_data.clear()
        await update.message.reply_text(
            "🏠 Главное меню",
            reply_markup=main_menu_keyboard()
        )
        return
    
    if state == SIMPLE_APPOINTMENT_STATES['waiting_name']:
        if len(text.strip()) < 3:
            await update.message.reply_text(
                "❌ Пожалуйста, введите ваше полное имя (минимум 3 символа):"
            )
            return
        
        user_data['simple_appointment']['client_name'] = text.strip()
        user_data['simple_appointment_state'] = SIMPLE_APPOINTMENT_STATES['waiting_phone']
        
        await update.message.reply_text(
            """
📞 Отлично! Теперь введите ваш **номер телефона**:

Можно в любом формате, например:
• +7 (812) 123-45-67
• 8 (812) 123-45-67
• 8121234567
""",
            parse_mode='Markdown'
        )
    
    elif state == SIMPLE_APPOINTMENT_STATES['waiting_phone']:
        if not validate_phone(text):
            await update.message.reply_text(
                "❌ Пожалуйста, введите корректный номер телефона (минимум 10 цифр):"
            )
            return
        
        user_data['simple_appointment']['client_phone'] = text.strip()
        user_data['simple_appointment_state'] = SIMPLE_APPOINTMENT_STATES['waiting_email']
        
        await update.message.reply_text(
            """
📧 Отлично! Теперь введите ваш **email адрес**:

Например: ivanov@example.com
""",
            parse_mode='Markdown'
        )
    
    elif state == SIMPLE_APPOINTMENT_STATES['waiting_email']:
        if not validate_email(text):
            await update.message.reply_text(
                "❌ Пожалуйста, введите корректный email адрес (например: ivanov@example.com):"
            )
            return
        
        user_data['simple_appointment']['client_email'] = text.strip()
        
        # Создаем заявку
        appointment_id = await create_appointment(
            user_id=update.effective_user.id,
            service_type=user_data['simple_appointment']['service_type'],
            client_name=user_data['simple_appointment']['client_name'],
            client_phone=user_data['simple_appointment']['client_phone'],
            client_email=user_data['simple_appointment']['client_email']
        )
        
        # Отправляем уведомление администраторам
        appointment_info = f"""
📋 **Новая заявка на услугу**

🆔 ID: {appointment_id}
📝 Услуга: {user_data['simple_appointment']['service_type']}
👤 ФИО: {user_data['simple_appointment']['client_name']}
📞 Телефон: {user_data['simple_appointment']['client_phone']}
📧 Email: {user_data['simple_appointment']['client_email']}
⏰ Дата создания: {update.message.date.strftime('%d.%m.%Y %H:%M')}
"""
        
        for admin_id in ADMIN_IDS:
            try:
                from keyboards.admin import appointment_actions_keyboard
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=appointment_info,
                    parse_mode='Markdown',
                    reply_markup=appointment_actions_keyboard(appointment_id)
                )
            except Exception as e:
                print(f"Ошибка отправки уведомления админу {admin_id}: {e}")
        
        # Отправляем красивое сообщение клиенту
        thank_you_text = f"""
✅ **Спасибо за вашу заявку!**

Ваша заявка на услугу **"{user_data['simple_appointment']['service_type']}"** успешно принята.

📋 **Ваши данные:**
👤 ФИО: {user_data['simple_appointment']['client_name']}
📞 Телефон: {user_data['simple_appointment']['client_phone']}
📧 Email: {user_data['simple_appointment']['client_email']}

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
        
        await update.message.reply_text(
            thank_you_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        user_data.clear()
