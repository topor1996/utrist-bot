from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, date, time, timedelta
from database import create_appointment, get_appointments_by_date, get_user_appointments, update_appointment_status, get_appointment_by_id
from keyboards.main_menu import main_menu_keyboard, back_to_main_keyboard
from keyboards.admin import appointment_actions_keyboard
from config import WORK_START_HOUR, WORK_END_HOUR, WORK_DAYS, ADMIN_IDS
from database import is_admin
import calendar

# Состояния для записи
APPOINTMENT_STATES = {
    'waiting_service': 1,
    'waiting_name': 2,
    'waiting_phone': 3,
    'waiting_date': 4,
    'waiting_time': 5,
    'waiting_comment': 6,
}

def get_available_times(appointment_date: date, existing_appointments: list) -> list:
    """Получить доступное время для записи"""
    booked_times = set()
    for apt in existing_appointments:
        apt_time = apt['appointment_time']
        if isinstance(apt_time, str):
            booked_times.add(datetime.strptime(apt_time, '%H:%M:%S').time())
        else:
            booked_times.add(apt_time)
    available = []
    
    for hour in range(WORK_START_HOUR, WORK_END_HOUR):
        for minute in [0, 30]:  # Записи каждые 30 минут
            t = time(hour, minute)
            if t not in booked_times:
                available.append(t)
    
    return available

def generate_calendar(year: int, month: int, selected_date: date = None) -> list:
    """Генерация календаря для выбора даты"""
    cal = calendar.monthcalendar(year, month)
    keyboard = []
    
    # Заголовок с месяцем
    month_names = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                   'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
    header = f"{month_names[month-1]} {year}"
    
    # Дни недели
    weekdays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    keyboard.append([f"📅 {header}"])
    keyboard.append(weekdays)
    
    # Дни месяца
    today = date.today()
    for week in cal:
        row = []
        for day in week:
            if day == 0:
                row.append(' ')
            else:
                d = date(year, month, day)
                if d < today:
                    row.append(' ')
                elif d.weekday() + 1 not in WORK_DAYS:
                    row.append(' ')
                else:
                    marker = '✅' if selected_date and d == selected_date else ''
                    row.append(f"{marker}{day}")
        keyboard.append(row)
    
    # Навигация
    nav_row = []
    if month > 1 or year > today.year:
        nav_row.append('◀️')
    else:
        nav_row.append(' ')
    nav_row.append('Сегодня')
    if month < 12:
        nav_row.append('▶️')
    else:
        nav_row.append(' ')
    keyboard.append(nav_row)
    
    return keyboard

async def appointment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало процесса записи"""
    user_data = context.user_data
    user_data['appointment'] = {}
    user_data['appointment_state'] = APPOINTMENT_STATES['waiting_service']
    
    text = """
📞 Запись на консультацию

Выберите тип услуги:
"""
    keyboard = [
        ['💬 Консультация юриста'],
        ['📝 Регистрация ИП/ООО'],
        ['📊 Бухгалтерские услуги'],
        ['⚖️ Судебное сопровождение'],
        ['📋 Составление документов'],
        ['🔙 Главное меню']
    ]
    
    from telegram import ReplyKeyboardMarkup, KeyboardButton
    reply_markup = ReplyKeyboardMarkup(
        [[KeyboardButton(btn) for btn in row] for row in keyboard],
        resize_keyboard=True
    )
    
    await update.message.reply_text(text, reply_markup=reply_markup)

async def process_appointment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка шагов записи"""
    user_data = context.user_data
    state = user_data.get('appointment_state', 0)
    text = update.message.text
    
    if text == '🔙 Главное меню':
        user_data.clear()
        await update.message.reply_text(
            "🏠 Главное меню",
            reply_markup=main_menu_keyboard()
        )
        return
    
    if state == APPOINTMENT_STATES['waiting_service']:
        user_data['appointment']['service_type'] = text
        user_data['appointment_state'] = APPOINTMENT_STATES['waiting_name']
        await update.message.reply_text(
            "👤 Введите ваше имя:",
            reply_markup=back_to_main_keyboard()
        )
    
    elif state == APPOINTMENT_STATES['waiting_name']:
        user_data['appointment']['client_name'] = text
        user_data['appointment_state'] = APPOINTMENT_STATES['waiting_phone']
        await update.message.reply_text(
            "📞 Введите ваш телефон:",
            reply_markup=back_to_main_keyboard()
        )
    
    elif state == APPOINTMENT_STATES['waiting_phone']:
        user_data['appointment']['client_phone'] = text
        user_data['appointment_state'] = APPOINTMENT_STATES['waiting_date']
        
        # Показываем календарь
        today = date.today()
        cal = generate_calendar(today.year, today.month)
        cal_text = "\n".join([" ".join(row) for row in cal])
        
        await update.message.reply_text(
            f"📅 Выберите дату:\n\n{cal_text}\n\nВведите число (например: 15):",
            reply_markup=back_to_main_keyboard()
        )
    
    elif state == APPOINTMENT_STATES['waiting_date']:
        try:
            day = int(text)
            today = date.today()
            
            # Проверяем, что день в текущем месяце
            try:
                selected_date = date(today.year, today.month, day)
            except ValueError:
                # Если день не существует в текущем месяце, пробуем следующий месяц
                if today.month == 12:
                    selected_date = date(today.year + 1, 1, day)
                else:
                    selected_date = date(today.year, today.month + 1, day)
            
            if selected_date < today:
                await update.message.reply_text("❌ Нельзя выбрать прошедшую дату. Введите число:")
                return
            
            if selected_date.weekday() + 1 not in WORK_DAYS:
                await update.message.reply_text("❌ В этот день мы не работаем. Введите другое число:")
                return
            
            user_data['appointment']['appointment_date'] = selected_date
            user_data['appointment_state'] = APPOINTMENT_STATES['waiting_time']
            
            # Получаем доступное время
            existing = await get_appointments_by_date(selected_date)
            available_times = get_available_times(selected_date, existing)
            
            if not available_times:
                await update.message.reply_text(
                    "❌ На эту дату нет свободного времени. Выберите другую дату:",
                    reply_markup=back_to_main_keyboard()
                )
                user_data['appointment_state'] = APPOINTMENT_STATES['waiting_date']
                return
            
            times_text = "\n".join([f"• {t.strftime('%H:%M')}" for t in available_times[:10]])
            await update.message.reply_text(
                f"⏰ Выберите время:\n\n{times_text}\n\nВведите время в формате ЧЧ:ММ (например: 14:30):",
                reply_markup=back_to_main_keyboard()
            )
        except ValueError:
            await update.message.reply_text("❌ Введите корректное число:")
    
    elif state == APPOINTMENT_STATES['waiting_time']:
        try:
            time_str = text.replace(':', '.')
            hour, minute = map(int, time_str.split('.'))
            selected_time = time(hour, minute)
            
            appointment_date = user_data['appointment']['appointment_date']
            existing = await get_appointments_by_date(appointment_date)
            available_times = get_available_times(appointment_date, existing)
            
            if selected_time not in available_times:
                await update.message.reply_text("❌ Это время занято. Выберите другое время:")
                return
            
            user_data['appointment']['appointment_time'] = selected_time
            user_data['appointment_state'] = APPOINTMENT_STATES['waiting_comment']
            
            await update.message.reply_text(
                "💬 Введите комментарий (или отправьте 'пропустить'):",
                reply_markup=back_to_main_keyboard()
            )
    
    elif state == APPOINTMENT_STATES['waiting_comment']:
        comment = None if text.lower() in ['пропустить', 'skip', ''] else text
        user_data['appointment']['comment'] = comment
        
        # Создаем запись
        appointment_id = await create_appointment(
            user_id=update.effective_user.id,
            service_type=user_data['appointment']['service_type'],
            client_name=user_data['appointment']['client_name'],
            client_phone=user_data['appointment']['client_phone'],
            appointment_date=user_data['appointment']['appointment_date'],
            appointment_time=user_data['appointment']['appointment_time'],
            comment=comment
        )
        
        # Отправляем уведомление администраторам
        appointment_info = f"""
📋 Новая заявка на консультацию

ID: {appointment_id}
Услуга: {user_data['appointment']['service_type']}
Имя: {user_data['appointment']['client_name']}
Телефон: {user_data['appointment']['client_phone']}
Дата: {user_data['appointment']['appointment_date']}
Время: {user_data['appointment']['appointment_time']}
Комментарий: {comment or 'нет'}
"""
        
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=appointment_info,
                    reply_markup=appointment_actions_keyboard(appointment_id)
                )
            except:
                pass
        
        await update.message.reply_text(
            f"""
✅ Запись успешно создана!

📅 Дата: {user_data['appointment']['appointment_date']}
⏰ Время: {user_data['appointment']['appointment_time']}
📞 Мы свяжемся с вами по телефону: {user_data['appointment']['client_phone']}

Спасибо за обращение!
""",
            reply_markup=main_menu_keyboard()
        )
        
        user_data.clear()

async def appointment_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback от кнопок админа"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith('appt_confirm_'):
        appointment_id = int(data.split('_')[-1])
        await update_appointment_status(appointment_id, 'confirmed')
        appointment = await get_appointment_by_id(appointment_id)
        await query.edit_message_text(
            f"✅ Запись подтверждена\n\n{appointment['client_name']} - {appointment['appointment_date']} {appointment['appointment_time']}"
        )
    
    elif data.startswith('appt_cancel_'):
        appointment_id = int(data.split('_')[-1])
        await update_appointment_status(appointment_id, 'cancelled')
        appointment = await get_appointment_by_id(appointment_id)
        await query.edit_message_text(
            f"❌ Запись отменена\n\n{appointment['client_name']} - {appointment['appointment_date']} {appointment['appointment_time']}"
        )
    
    elif data.startswith('appt_call_'):
        appointment_id = int(data.split('_')[-1])
        appointment = await get_appointment_by_id(appointment_id)
        await query.answer(f"Телефон: {appointment['client_phone']}", show_alert=True)
