"""
Утилиты для валидации данных
"""
import re


def normalize_phone(phone: str) -> str:
    """
    Нормализует номер телефона - убирает все кроме цифр.
    Возвращает только цифры.
    """
    return re.sub(r'\D', '', phone)


def validate_phone(phone: str) -> tuple[bool, str]:
    """
    Валидирует российский номер телефона.

    Принимает форматы:
    - +7XXXXXXXXXX (11 цифр с +7)
    - 8XXXXXXXXXX (11 цифр с 8)
    - 9XXXXXXXXXX (10 цифр, начиная с 9)
    - 7XXXXXXXXXX (11 цифр с 7)

    Возвращает кортеж: (is_valid, normalized_phone или error_message)
    """
    # Убираем все кроме цифр
    digits = normalize_phone(phone)

    # Проверяем длину
    if len(digits) < 10:
        return False, "Номер слишком короткий. Введите полный номер телефона."

    if len(digits) > 11:
        return False, "Номер слишком длинный. Проверьте правильность ввода."

    # Если 10 цифр и начинается с 9 - добавляем 7
    if len(digits) == 10 and digits.startswith('9'):
        digits = '7' + digits

    # Если 11 цифр и начинается с 8 - заменяем на 7
    if len(digits) == 11 and digits.startswith('8'):
        digits = '7' + digits[1:]

    # Проверяем что номер начинается с 7 и следующая цифра 9
    if len(digits) == 11:
        if not digits.startswith('7'):
            return False, "Российский номер должен начинаться с +7 или 8."
        if digits[1] != '9':
            return False, "Номер мобильного телефона должен начинаться с 9."
    elif len(digits) == 10:
        if not digits.startswith('9'):
            return False, "Номер мобильного телефона должен начинаться с 9."
        digits = '7' + digits
    else:
        return False, "Неверный формат номера телефона."

    # Форматируем номер для отображения
    formatted = f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"

    return True, formatted


def validate_email(email: str) -> tuple[bool, str]:
    """
    Простая валидация email адреса.

    Возвращает кортеж: (is_valid, normalized_email или error_message)
    """
    email = email.strip().lower()

    # Базовая проверка формата
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(pattern, email):
        return False, "Неверный формат email. Пример: name@example.com"

    return True, email
