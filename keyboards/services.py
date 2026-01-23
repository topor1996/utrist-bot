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
        [KeyboardButton('📄 Изменения в устав, ЕГРЮЛ')],
        [KeyboardButton('💬 Консультации для юрлиц')],
        [KeyboardButton('📋 Составление договоров (юрлица)')],
        [KeyboardButton('🏛️ Судебное сопровождение (юрлица)')],
        [KeyboardButton('📄 Подача иска (юрлица)')],
        [KeyboardButton('⚖️ Апелляция и кассация (юрлица)')],
        [KeyboardButton('📊 Бухгалтерские услуги (юрлица)')],
        [KeyboardButton('🏷️ Регистрация товарного знака')],
        [KeyboardButton('🔙 Назад к услугам'), KeyboardButton('🏠 Главное меню')]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def entrepreneurs_keyboard():
    """Услуги для предпринимателей"""
    keyboard = [
        [KeyboardButton('💬 Юридические консультации')],
        [KeyboardButton('📝 Регистрация ИП (подробно)')],
        [KeyboardButton('📄 Изменение ЕГРИП')],
        [KeyboardButton('🗑️ Ликвидация ИП')],
        [KeyboardButton('💎 Регистрация ювелиров')],
        [KeyboardButton('📋 Регистрация в надзорных органах')],
        [KeyboardButton('🔒 Оператор персональных данных')],
        [KeyboardButton('🏷️ Регистрация товарного знака')],
        [KeyboardButton('💬 Консультации для ИП')],
        [KeyboardButton('📋 Составление договоров')],
        [KeyboardButton('👥 Оформление сотрудников')],
        [KeyboardButton('🏛️ Судебное сопровождение ИП')],
        [KeyboardButton('📄 Подача иска (ИП)')],
        [KeyboardButton('⚖️ Апелляция и кассация (ИП)')],
        [KeyboardButton('📊 Бухгалтерские услуги')],
        [KeyboardButton('🚗 Выезд к клиенту')],
        [KeyboardButton('🔙 Назад к услугам'), KeyboardButton('🏠 Главное меню')]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def individuals_keyboard():
    """Услуги для физических лиц"""
    keyboard = [
        [KeyboardButton('💬 Консультации юриста')],
        [KeyboardButton('📋 Составление исковых заявлений')],
        [KeyboardButton('🏛️ Судебное сопровождение')],
        [KeyboardButton('📄 Подача иска в суд')],
        [KeyboardButton('📋 Ознакомление с делом')],
        [KeyboardButton('📜 Получение решения суда')],
        [KeyboardButton('⚖️ Апелляция и кассация')],
        [KeyboardButton('📊 Налоговые декларации 3-НДФЛ')],
        [KeyboardButton('📑 Анализ документов')],
        [KeyboardButton('🏠 Сделки с недвижимостью')],
        [KeyboardButton('🏷️ Регистрация товарного знака')],
        [KeyboardButton('🚗 Выезд на проверку')],
        [KeyboardButton('📄 Ксерокопирование')],
        [KeyboardButton('⚡ Срочная подготовка')],
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
