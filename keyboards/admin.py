from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def admin_keyboard():
    """Админ-панель"""
    keyboard = [
        [KeyboardButton('📋 Новые заявки'), KeyboardButton('📁 Все заявки')],
        [KeyboardButton('📅 Календарь записей')],
        [KeyboardButton('📊 Статистика')],
        [KeyboardButton('📥 Экспорт данных')],
        [KeyboardButton('🏠 Главное меню')]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def appointments_list_keyboard(appointments: list, page: int = 0, per_page: int = 5):
    """Список записей с пагинацией"""
    keyboard = []
    start = page * per_page
    end = start + per_page
    
    for appointment in appointments[start:end]:
        name = appointment['client_name']
        service = appointment['service_type'][:20] + '...' if len(appointment['service_type']) > 20 else appointment['service_type']
        # Формируем текст кнопки
        if appointment.get('appointment_date') and appointment.get('appointment_time'):
            button_text = f"{appointment['appointment_date']} {appointment['appointment_time']} - {name}"
        else:
            button_text = f"{name} - {service}"
        keyboard.append([
            InlineKeyboardButton(
                button_text,
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
        [InlineKeyboardButton('💳 Отправить в оплату', callback_data=f'appt_payment_{appointment_id}')],
        [
            InlineKeyboardButton('📞 Позвонить', callback_data=f'appt_call_{appointment_id}'),
            InlineKeyboardButton('📜 История', callback_data=f'appt_history_{appointment_id}')
        ],
        [InlineKeyboardButton('🔙 Назад', callback_data='appt_list')]
    ]
    return InlineKeyboardMarkup(keyboard)


def export_keyboard():
    """Клавиатура выбора типа экспорта"""
    keyboard = [
        [InlineKeyboardButton('📞 Экспорт заявок (все)', callback_data='export_appointments_all')],
        [InlineKeyboardButton('📞 Только ожидающие', callback_data='export_appointments_pending')],
        [InlineKeyboardButton('📞 Только подтверждённые', callback_data='export_appointments_confirmed')],
        [InlineKeyboardButton('❓ Экспорт вопросов', callback_data='export_questions')],
        [InlineKeyboardButton('🔙 Назад', callback_data='admin_back')]
    ]
    return InlineKeyboardMarkup(keyboard)

def question_actions_keyboard(question_id: int):
    """Действия с вопросом"""
    keyboard = [
        [InlineKeyboardButton('💬 Ответить', callback_data=f'q_reply_{question_id}')],
        [
            InlineKeyboardButton('✅ Отвечено', callback_data=f'q_answered_{question_id}'),
            InlineKeyboardButton('❌ Закрыть', callback_data=f'q_close_{question_id}')
        ],
        [InlineKeyboardButton('📞 Позвонить', callback_data=f'q_call_{question_id}')],
        [InlineKeyboardButton('🔙 Назад', callback_data='q_list')]
    ]
    return InlineKeyboardMarkup(keyboard)


def all_appointments_filter_keyboard():
    """Клавиатура фильтрации всех заявок по статусу"""
    keyboard = [
        [InlineKeyboardButton('📋 Все заявки', callback_data='allappt_filter_all')],
        [
            InlineKeyboardButton('⏳ Ожидающие', callback_data='allappt_filter_pending'),
            InlineKeyboardButton('✅ Подтверждённые', callback_data='allappt_filter_confirmed')
        ],
        [
            InlineKeyboardButton('💳 В оплате', callback_data='allappt_filter_payment_sent'),
            InlineKeyboardButton('✔️ Завершённые', callback_data='allappt_filter_completed')
        ],
        [InlineKeyboardButton('❌ Отменённые', callback_data='allappt_filter_cancelled')],
        [InlineKeyboardButton('🔙 Назад', callback_data='admin_back')]
    ]
    return InlineKeyboardMarkup(keyboard)


def all_appointments_list_keyboard(appointments: list, page: int = 0, per_page: int = 5, status_filter: str = 'all'):
    """Список всех записей с пагинацией (для раздела 'Все заявки')"""
    keyboard = []
    start = page * per_page
    end = start + per_page

    # Эмодзи статусов
    status_emoji = {
        'pending': '⏳',
        'confirmed': '✅',
        'cancelled': '❌',
        'completed': '✔️',
        'payment_sent': '💳'
    }

    for appointment in appointments[start:end]:
        name = appointment['client_name']
        status = appointment.get('status', 'pending')
        emoji = status_emoji.get(status, '❓')

        # Формируем текст кнопки
        if appointment.get('appointment_date') and appointment.get('appointment_time'):
            button_text = f"{emoji} {appointment['appointment_date']} - {name}"
        else:
            service = appointment['service_type'][:15] + '...' if len(appointment['service_type']) > 15 else appointment['service_type']
            button_text = f"{emoji} {name} - {service}"

        keyboard.append([
            InlineKeyboardButton(
                button_text,
                callback_data=f"allappt_detail_{appointment['id']}"
            )
        ])

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton('◀️ Назад', callback_data=f'allappt_page_{status_filter}_{page-1}'))
    if end < len(appointments):
        nav_buttons.append(InlineKeyboardButton('Вперед ▶️', callback_data=f'allappt_page_{status_filter}_{page+1}'))

    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([InlineKeyboardButton('🔍 Фильтр', callback_data='allappt_filters')])
    keyboard.append([InlineKeyboardButton('🔙 Назад', callback_data='admin_back')])

    return InlineKeyboardMarkup(keyboard)


def all_appointment_actions_keyboard(appointment_id: int, current_status: str):
    """Действия с записью в разделе 'Все заявки' (с учётом текущего статуса)"""
    keyboard = []

    # Показываем действия в зависимости от статуса
    if current_status == 'pending':
        keyboard.append([
            InlineKeyboardButton('✅ Подтвердить', callback_data=f'allappt_confirm_{appointment_id}'),
            InlineKeyboardButton('❌ Отменить', callback_data=f'allappt_cancel_{appointment_id}')
        ])
    elif current_status == 'confirmed':
        keyboard.append([
            InlineKeyboardButton('✔️ Завершить', callback_data=f'allappt_complete_{appointment_id}'),
            InlineKeyboardButton('❌ Отменить', callback_data=f'allappt_cancel_{appointment_id}')
        ])
    elif current_status == 'payment_sent':
        keyboard.append([
            InlineKeyboardButton('✅ Подтвердить', callback_data=f'allappt_confirm_{appointment_id}'),
            InlineKeyboardButton('✔️ Завершить', callback_data=f'allappt_complete_{appointment_id}')
        ])

    # Кнопка оплаты доступна для всех статусов кроме отменённых
    if current_status not in ('cancelled',):
        keyboard.append([InlineKeyboardButton('💳 Отправить в оплату', callback_data=f'allappt_payment_{appointment_id}')])

    keyboard.append([
        InlineKeyboardButton('📞 Позвонить', callback_data=f'allappt_call_{appointment_id}'),
        InlineKeyboardButton('📜 История', callback_data=f'allappt_history_{appointment_id}')
    ])
    keyboard.append([InlineKeyboardButton('🔙 К списку', callback_data='allappt_back_to_list')])

    return InlineKeyboardMarkup(keyboard)
