from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from data.service_categories import (
    INDIVIDUALS_CATEGORIES,
    ENTREPRENEURS_CATEGORIES,
    LEGAL_ENTITIES_CATEGORIES
)


def services_keyboard():
    """Меню выбора категории услуг"""
    keyboard = [
        [KeyboardButton('👔 Юридическим лицам')],
        [KeyboardButton('💼 Предпринимателям')],
        [KeyboardButton('👤 Физическим лицам')],
        [KeyboardButton('🏠 Главное меню')]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def subcategory_keyboard(category_type: str) -> InlineKeyboardMarkup:
    """
    Inline клавиатура с подкатегориями услуг.
    category_type: 'individuals', 'entrepreneurs', 'legal_entities'
    """
    categories_map = {
        'individuals': INDIVIDUALS_CATEGORIES,
        'entrepreneurs': ENTREPRENEURS_CATEGORIES,
        'legal_entities': LEGAL_ENTITIES_CATEGORIES,
    }

    categories = categories_map.get(category_type, {})
    keyboard = []

    for subcat_id, subcat_data in categories.items():
        keyboard.append([
            InlineKeyboardButton(
                subcat_data['name'],
                callback_data=f"subcat_{category_type}_{subcat_id}"
            )
        ])

    keyboard.append([InlineKeyboardButton('🔙 Назад к категориям', callback_data='back_to_categories')])

    return InlineKeyboardMarkup(keyboard)


def services_list_keyboard(category_type: str, subcategory: str) -> InlineKeyboardMarkup:
    """
    Inline клавиатура со списком услуг подкатегории.
    """
    categories_map = {
        'individuals': INDIVIDUALS_CATEGORIES,
        'entrepreneurs': ENTREPRENEURS_CATEGORIES,
        'legal_entities': LEGAL_ENTITIES_CATEGORIES,
    }

    categories = categories_map.get(category_type, {})
    services = categories.get(subcategory, {}).get('services', [])

    keyboard = []
    for service in services:
        # Укорачиваем callback_data (макс 64 байта)
        # Используем индекс услуги
        service_idx = services.index(service)
        keyboard.append([
            InlineKeyboardButton(
                service,
                callback_data=f"svc_{category_type}_{subcategory}_{service_idx}"
            )
        ])

    keyboard.append([InlineKeyboardButton('🔙 Назад', callback_data=f"back_subcat_{category_type}")])

    return InlineKeyboardMarkup(keyboard)


# Сохраняем старые функции для обратной совместимости (используются в других частях бота)
def legal_entities_keyboard():
    """Услуги для юридических лиц (reply keyboard для совместимости)"""
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
    """Услуги для предпринимателей (reply keyboard для совместимости)"""
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
    """Услуги для физических лиц (reply keyboard для совместимости)"""
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
