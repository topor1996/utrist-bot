import os
from dotenv import load_dotenv

load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv('BOT_TOKEN', '')

# База данных
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///bot_database.db')

# Администраторы
ADMIN_IDS = [int(admin_id) for admin_id in os.getenv('ADMIN_IDS', '').split(',') if admin_id.strip()]

# Настройки работы
WORK_START_HOUR = int(os.getenv('WORK_START_HOUR', '9'))
WORK_END_HOUR = int(os.getenv('WORK_END_HOUR', '18'))
WORK_DAYS = [int(day) for day in os.getenv('WORK_DAYS', '1,2,3,4,5').split(',')]

# Контакты компании
COMPANY_PHONE = '+7 (812) 438-38-40'
COMPANY_WEBSITE = 'https://vash-urist.spb.ru'
