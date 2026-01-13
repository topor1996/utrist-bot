from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def services_keyboard():
    """Меню выбора категории услуг"""
    keyboard = [
        [KeyboardButton('👔 Юридическим лицам')],
        [KeyboardButton('💼 Предпринимателям')],
        [KeyboardButton('👤 Физическим лицам')],
        [KeyboardButton('🏠 Главное меню')]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def legal_entities_keyboard():
    """Услуги для юридических лиц"""
    keyboard = [
        [KeyboardButton('📝 Регистрация ООО')],
        [KeyboardButton('💳 Расчетный счет')],
        [KeyboardButton('📊 Бухгалтерские услуги')],
        [KeyboardButton('📄 Изменения в устав, ЕГРЮЛ')],
        [KeyboardButton('⚖️ Досудебная работа')],
        [KeyboardButton('🏛️ Судебное сопровождение')],
        [KeyboardButton('📋 Составление договоров')],
        [KeyboardButton('💬 Консультации юриста')],
        [KeyboardButton('📦 Абонентское обслуживание')],
        [KeyboardButton('🔍 Анализ бизнеса')],
        [KeyboardButton('🔙 Назад к услугам'), KeyboardButton('🏠 Главное меню')]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def entrepreneurs_keyboard():
    """Услуги для предпринимателей"""
    keyboard = [
        [KeyboardButton('📝 Регистрация ИП')],
        [KeyboardButton('📄 Изменение ЕГРИП')],
        [KeyboardButton('🗑️ Ликвидация ИП')],
        [KeyboardButton('💳 Расчетный счет для ИП')],
        [KeyboardButton('📊 Налоговые отчеты')],
        [KeyboardButton('💬 Юридические консультации')],
        [KeyboardButton('📋 Договорная работа')],
        [KeyboardButton('🏛️ Судебное сопровождение')],
        [KeyboardButton('📦 Абонентское обслуживание')],
        [KeyboardButton('🔙 Назад к услугам'), KeyboardButton('🏠 Главное меню')]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def individuals_keyboard():
    """Услуги для физических лиц"""
    keyboard = [
        [KeyboardButton('💬 Консультации юриста')],
        [KeyboardButton('📝 Составление исковых заявлений')],
        [KeyboardButton('📊 Налоговые декларации 3-НДФЛ')],
        [KeyboardButton('📝 Регистрация ИП')],
        [KeyboardButton('🛡️ Защита прав потребителей')],
        [KeyboardButton('🏠 Сделки с недвижимостью')],
        [KeyboardButton('💻 Онлайн-консультация')],
        [KeyboardButton('🔙 Назад к услугам'), KeyboardButton('🏠 Главное меню')]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def service_info_keyboard(service_name: str):
    """Кнопки для информации об услуге"""
    keyboard = [
        [InlineKeyboardButton('📞 Записаться на консультацию', callback_data=f'appoint_{service_name}')],
        [InlineKeyboardButton('🔙 Назад', callback_data='back_services')]
    ]
    return InlineKeyboardMarkup(keyboard)
