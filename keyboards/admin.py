from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def admin_keyboard():
    """Админ-панель"""
    keyboard = [
        [KeyboardButton('📋 Новые заявки')],
        [KeyboardButton('📅 Календарь записей')],
        [KeyboardButton('📊 Статистика')],
        [KeyboardButton('🏠 Главное меню')]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def appointments_list_keyboard(appointments: list, page: int = 0, per_page: int = 5):
    """Список записей с пагинацией"""
    keyboard = []
    start = page * per_page
    end = start + per_page
    
    for appointment in appointments[start:end]:
        date_str = appointment['appointment_date']
        time_str = appointment['appointment_time']
        name = appointment['client_name']
        keyboard.append([
            InlineKeyboardButton(
                f"{date_str} {time_str} - {name}",
                callback_data=f"appt_detail_{appointment['id']}"
            )
        ])
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton('◀️ Назад', callback_data=f'appt_page_{page-1}'))
    if end < len(appointments):
        nav_buttons.append(InlineKeyboardButton('Вперед ▶️', callback_data=f'appt_page_{page+1}'))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton('🔙 Назад', callback_data='admin_back')])
    
    return InlineKeyboardMarkup(keyboard)

def questions_list_keyboard(questions: list, page: int = 0, per_page: int = 5):
    """Список вопросов с пагинацией"""
    keyboard = []
    start = page * per_page
    end = start + per_page
    
    for question in questions[start:end]:
        text = question['question_text'][:30] + '...' if len(question['question_text']) > 30 else question['question_text']
        keyboard.append([
            InlineKeyboardButton(
                text,
                callback_data=f"q_detail_{question['id']}"
            )
        ])
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton('◀️ Назад', callback_data=f'q_page_{page-1}'))
    if end < len(questions):
        nav_buttons.append(InlineKeyboardButton('Вперед ▶️', callback_data=f'q_page_{page+1}'))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton('🔙 Назад', callback_data='admin_back')])
    
    return InlineKeyboardMarkup(keyboard)

def appointment_actions_keyboard(appointment_id: int):
    """Действия с записью"""
    keyboard = [
        [
            InlineKeyboardButton('✅ Подтвердить', callback_data=f'appt_confirm_{appointment_id}'),
            InlineKeyboardButton('❌ Отменить', callback_data=f'appt_cancel_{appointment_id}')
        ],
        [InlineKeyboardButton('📞 Позвонить', callback_data=f'appt_call_{appointment_id}')],
        [InlineKeyboardButton('🔙 Назад', callback_data='appt_list')]
    ]
    return InlineKeyboardMarkup(keyboard)

def question_actions_keyboard(question_id: int):
    """Действия с вопросом"""
    keyboard = [
        [
            InlineKeyboardButton('✅ Отвечено', callback_data=f'q_answered_{question_id}'),
            InlineKeyboardButton('❌ Закрыть', callback_data=f'q_close_{question_id}')
        ],
        [InlineKeyboardButton('📞 Позвонить', callback_data=f'q_call_{question_id}')],
        [InlineKeyboardButton('🔙 Назад', callback_data='q_list')]
    ]
    return InlineKeyboardMarkup(keyboard)
