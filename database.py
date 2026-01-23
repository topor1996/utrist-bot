import sqlite3
import aiosqlite
from datetime import datetime, date, time
from typing import List, Optional, Dict
from config import DATABASE_URL

# Инициализация базы данных
async def init_db():
    """Инициализация базы данных"""
    async with aiosqlite.connect(DATABASE_URL.replace('sqlite:///', '')) as db:
        with open('database/init.sql', 'r', encoding='utf-8') as f:
            await db.executescript(f.read())
        await db.commit()

# Работа с пользователями
async def add_user(telegram_id: int, username: str = None, first_name: str = None, last_name: str = None):
    """Добавить пользователя"""
    async with aiosqlite.connect(DATABASE_URL.replace('sqlite:///', '')) as db:
        await db.execute(
            """INSERT OR IGNORE INTO users (telegram_id, username, first_name, last_name) 
               VALUES (?, ?, ?, ?)""",
            (telegram_id, username, first_name, last_name)
        )
        await db.commit()

async def update_user_phone(telegram_id: int, phone: str):
    """Обновить телефон пользователя"""
    async with aiosqlite.connect(DATABASE_URL.replace('sqlite:///', '')) as db:
        await db.execute(
            "UPDATE users SET phone = ? WHERE telegram_id = ?",
            (phone, telegram_id)
        )
        await db.commit()

# Работа с записями
async def create_appointment(
    user_id: int,
    service_type: str,
    client_name: str,
    client_phone: str,
    client_email: str = None,
    appointment_date: date = None,
    appointment_time: time = None,
    comment: str = None
) -> int:
    """Создать запись на консультацию"""
    async with aiosqlite.connect(DATABASE_URL.replace('sqlite:///', '')) as db:
        cursor = await db.execute(
            """INSERT INTO appointments 
               (user_id, service_type, client_name, client_phone, client_email, appointment_date, appointment_time, comment)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, service_type, client_name, client_phone, client_email, appointment_date, appointment_time, comment)
        )
        await db.commit()
        return cursor.lastrowid

async def get_appointments_by_date(appointment_date: date) -> List[Dict]:
    """Получить записи на конкретную дату"""
    async with aiosqlite.connect(DATABASE_URL.replace('sqlite:///', '')) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT * FROM appointments 
               WHERE appointment_date = ? AND status != 'cancelled'
               ORDER BY appointment_time""",
            (appointment_date,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_user_appointments(user_id: int) -> List[Dict]:
    """Получить записи пользователя"""
    async with aiosqlite.connect(DATABASE_URL.replace('sqlite:///', '')) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT * FROM appointments 
               WHERE user_id = ? AND status != 'cancelled'
               ORDER BY appointment_date DESC, appointment_time DESC""",
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_appointment_by_id(appointment_id: int) -> Optional[Dict]:
    """Получить запись по ID"""
    async with aiosqlite.connect(DATABASE_URL.replace('sqlite:///', '')) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM appointments WHERE id = ?",
            (appointment_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def update_appointment_status(appointment_id: int, status: str, changed_by: int = None, comment: str = None):
    """Обновить статус записи с записью в историю"""
    async with aiosqlite.connect(DATABASE_URL.replace('sqlite:///', '')) as db:
        # Получаем текущий статус
        async with db.execute(
            "SELECT status FROM appointments WHERE id = ?",
            (appointment_id,)
        ) as cursor:
            row = await cursor.fetchone()
            old_status = row[0] if row else None

        # Обновляем статус
        await db.execute(
            "UPDATE appointments SET status = ? WHERE id = ?",
            (status, appointment_id)
        )

        # Записываем в историю
        await db.execute(
            """INSERT INTO appointment_status_history
               (appointment_id, old_status, new_status, changed_by, comment)
               VALUES (?, ?, ?, ?, ?)""",
            (appointment_id, old_status, status, changed_by, comment)
        )

        await db.commit()

async def get_pending_appointments() -> List[Dict]:
    """Получить все ожидающие записи"""
    async with aiosqlite.connect(DATABASE_URL.replace('sqlite:///', '')) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT * FROM appointments 
               WHERE status = 'pending'
               ORDER BY created_at DESC""",
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

# Работа с вопросами
async def create_question(user_id: int, question_text: str, client_name: str = None, client_phone: str = None) -> int:
    """Создать вопрос от клиента"""
    async with aiosqlite.connect(DATABASE_URL.replace('sqlite:///', '')) as db:
        cursor = await db.execute(
            """INSERT INTO questions (user_id, question_text, client_name, client_phone)
               VALUES (?, ?, ?, ?)""",
            (user_id, question_text, client_name, client_phone)
        )
        await db.commit()
        return cursor.lastrowid

async def get_new_questions() -> List[Dict]:
    """Получить новые вопросы"""
    async with aiosqlite.connect(DATABASE_URL.replace('sqlite:///', '')) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT * FROM questions 
               WHERE status = 'new'
               ORDER BY created_at DESC""",
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_question_by_id(question_id: int) -> Optional[Dict]:
    """Получить вопрос по ID"""
    async with aiosqlite.connect(DATABASE_URL.replace('sqlite:///', '')) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM questions WHERE id = ?",
            (question_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def update_question_status(question_id: int, status: str):
    """Обновить статус вопроса"""
    async with aiosqlite.connect(DATABASE_URL.replace('sqlite:///', '')) as db:
        await db.execute(
            "UPDATE questions SET status = ? WHERE id = ?",
            (status, question_id)
        )
        await db.commit()

# Работа с администраторами
async def is_admin(telegram_id: int) -> bool:
    """Проверить, является ли пользователь администратором"""
    from config import ADMIN_IDS
    if telegram_id in ADMIN_IDS:
        return True
    async with aiosqlite.connect(DATABASE_URL.replace('sqlite:///', '')) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM admins WHERE telegram_id = ?",
            (telegram_id,)
        ) as cursor:
            count = await cursor.fetchone()
            return count[0] > 0

async def add_admin(telegram_id: int):
    """Добавить администратора"""
    async with aiosqlite.connect(DATABASE_URL.replace('sqlite:///', '')) as db:
        await db.execute(
            "INSERT OR IGNORE INTO admins (telegram_id) VALUES (?)",
            (telegram_id,)
        )
        await db.commit()


# История статусов
async def get_appointment_history(appointment_id: int) -> List[Dict]:
    """Получить историю изменений статуса заявки"""
    async with aiosqlite.connect(DATABASE_URL.replace('sqlite:///', '')) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT * FROM appointment_status_history
               WHERE appointment_id = ?
               ORDER BY created_at DESC""",
            (appointment_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


# Работа с напоминаниями
async def create_reminder(appointment_id: int, reminder_type: str, scheduled_at: datetime) -> int:
    """Создать напоминание"""
    async with aiosqlite.connect(DATABASE_URL.replace('sqlite:///', '')) as db:
        cursor = await db.execute(
            """INSERT INTO reminders (appointment_id, reminder_type, scheduled_at)
               VALUES (?, ?, ?)""",
            (appointment_id, reminder_type, scheduled_at.isoformat())
        )
        await db.commit()
        return cursor.lastrowid


async def get_pending_reminders() -> List[Dict]:
    """Получить напоминания, которые нужно отправить"""
    async with aiosqlite.connect(DATABASE_URL.replace('sqlite:///', '')) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT r.*, a.user_id, a.client_name, a.service_type,
                      a.appointment_date, a.appointment_time, a.status as appointment_status
               FROM reminders r
               JOIN appointments a ON r.appointment_id = a.id
               WHERE r.status = 'pending'
               AND r.scheduled_at <= datetime('now')
               AND a.status NOT IN ('cancelled', 'completed')
               ORDER BY r.scheduled_at""",
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def mark_reminder_sent(reminder_id: int, status: str = 'sent'):
    """Отметить напоминание как отправленное"""
    async with aiosqlite.connect(DATABASE_URL.replace('sqlite:///', '')) as db:
        await db.execute(
            """UPDATE reminders
               SET status = ?, sent_at = datetime('now')
               WHERE id = ?""",
            (status, reminder_id)
        )
        await db.commit()


# Экспорт данных
async def get_all_appointments(
    status: str = None,
    date_from: date = None,
    date_to: date = None
) -> List[Dict]:
    """Получить все заявки с фильтрацией для экспорта"""
    async with aiosqlite.connect(DATABASE_URL.replace('sqlite:///', '')) as db:
        db.row_factory = aiosqlite.Row

        query = "SELECT * FROM appointments WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)
        if date_from:
            query += " AND (appointment_date >= ? OR appointment_date IS NULL)"
            params.append(date_from.isoformat())
        if date_to:
            query += " AND (appointment_date <= ? OR appointment_date IS NULL)"
            params.append(date_to.isoformat())

        query += " ORDER BY created_at DESC"

        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_all_questions(status: str = None) -> List[Dict]:
    """Получить все вопросы с фильтрацией для экспорта"""
    async with aiosqlite.connect(DATABASE_URL.replace('sqlite:///', '')) as db:
        db.row_factory = aiosqlite.Row

        query = "SELECT * FROM questions WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY created_at DESC"

        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_appointments_for_reminder(target_date: date) -> List[Dict]:
    """Получить заявки на определённую дату для создания напоминаний"""
    async with aiosqlite.connect(DATABASE_URL.replace('sqlite:///', '')) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT a.* FROM appointments a
               LEFT JOIN reminders r ON a.id = r.appointment_id AND r.reminder_type = 'day_before'
               WHERE a.appointment_date = ?
               AND a.status IN ('pending', 'confirmed')
               AND r.id IS NULL""",
            (target_date.isoformat(),)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
