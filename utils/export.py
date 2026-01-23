"""
Экспорт данных в CSV для администраторов
"""
import csv
import io
from datetime import date, datetime
from typing import List, Dict, Optional

from database import get_all_appointments, get_all_questions


STATUS_NAMES = {
    'pending': 'Ожидает',
    'confirmed': 'Подтверждена',
    'cancelled': 'Отменена',
    'completed': 'Завершена',
    'payment_sent': 'В оплате',
    'new': 'Новый',
    'answered': 'Отвечен',
    'closed': 'Закрыт'
}


async def export_appointments_csv(
    status: str = None,
    date_from: date = None,
    date_to: date = None
) -> tuple[io.BytesIO, str]:
    """
    Экспорт заявок в CSV файл

    Returns:
        tuple: (BytesIO объект с данными, имя файла)
    """
    appointments = await get_all_appointments(status, date_from, date_to)

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    # Заголовки
    writer.writerow([
        'ID',
        'Дата создания',
        'ФИО клиента',
        'Телефон',
        'Email',
        'Услуга',
        'Дата записи',
        'Время записи',
        'Комментарий',
        'Статус'
    ])

    # Данные
    for apt in appointments:
        writer.writerow([
            apt['id'],
            apt.get('created_at', ''),
            apt['client_name'],
            apt['client_phone'],
            apt.get('client_email', ''),
            apt['service_type'],
            apt.get('appointment_date', ''),
            apt.get('appointment_time', ''),
            apt.get('comment', ''),
            STATUS_NAMES.get(apt['status'], apt['status'])
        ])

    # Конвертируем в bytes с BOM для корректного открытия в Excel
    content = output.getvalue()
    bytes_io = io.BytesIO()
    bytes_io.write('\ufeff'.encode('utf-8'))  # BOM для Excel
    bytes_io.write(content.encode('utf-8'))
    bytes_io.seek(0)

    # Генерируем имя файла
    today = datetime.now().strftime('%Y-%m-%d')
    filename = f"appointments_{today}.csv"

    return bytes_io, filename


async def export_questions_csv(status: str = None) -> tuple[io.BytesIO, str]:
    """
    Экспорт вопросов в CSV файл

    Returns:
        tuple: (BytesIO объект с данными, имя файла)
    """
    questions = await get_all_questions(status)

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    # Заголовки
    writer.writerow([
        'ID',
        'Дата создания',
        'ФИО клиента',
        'Телефон',
        'Вопрос',
        'Статус'
    ])

    # Данные
    for q in questions:
        writer.writerow([
            q['id'],
            q.get('created_at', ''),
            q.get('client_name', ''),
            q.get('client_phone', ''),
            q['question_text'],
            STATUS_NAMES.get(q['status'], q['status'])
        ])

    # Конвертируем в bytes с BOM
    content = output.getvalue()
    bytes_io = io.BytesIO()
    bytes_io.write('\ufeff'.encode('utf-8'))
    bytes_io.write(content.encode('utf-8'))
    bytes_io.seek(0)

    today = datetime.now().strftime('%Y-%m-%d')
    filename = f"questions_{today}.csv"

    return bytes_io, filename


def format_history_entry(entry: Dict) -> str:
    """Форматирование записи истории для отображения"""
    old_status = STATUS_NAMES.get(entry.get('old_status'), entry.get('old_status') or 'новая')
    new_status = STATUS_NAMES.get(entry['new_status'], entry['new_status'])
    created_at = entry.get('created_at', '')

    # Форматируем дату
    if created_at:
        try:
            if isinstance(created_at, str):
                dt = datetime.fromisoformat(created_at)
                created_at = dt.strftime('%d.%m.%Y %H:%M')
        except (ValueError, TypeError):
            pass

    text = f"• {created_at}: {old_status} → {new_status}"

    if entry.get('comment'):
        text += f" ({entry['comment']})"

    return text
