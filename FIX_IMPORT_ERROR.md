# Исправление ошибки импорта на Railway

## Проблема:
```
ImportError: cannot import name 'process_appointment' from 'handlers'
```

## Причина:
На Railway загружена старая версия файла `handlers/__init__.py` без экспорта `process_appointment`.

## Решение:

### Вариант 1: Через GitHub (если подключен)

1. Убедитесь, что изменения закоммичены:
   ```bash
   cd /Users/t1/Desktop/work/utrist-bot
   git status
   git add handlers/__init__.py
   git commit -m "Fix import error: add process_appointment"
   git push
   ```

2. Railway автоматически перезапустит деплой

### Вариант 2: Прямая загрузка файла

1. Откройте Railway → ваш проект → Settings
2. Перейдите в Source
3. Загрузите обновленный файл `handlers/__init__.py`

Или загрузите всю папку `handlers/` заново.

### Вариант 3: Проверьте содержимое файла на Railway

Убедитесь, что файл `handlers/__init__.py` на Railway содержит:

```python
from .start import start_handler, main_menu_handler
from .services import services_handler, legal_entities_handler, entrepreneurs_handler, individuals_handler
from .appointment import appointment_handler, appointment_callback_handler, process_appointment
from .question import question_handler, process_question
from .admin import admin_handler, admin_commands_handler, admin_callback_handler
from .contacts import contacts_handler, about_handler

__all__ = [
    'start_handler',
    'main_menu_handler',
    'services_handler',
    'legal_entities_handler',
    'entrepreneurs_handler',
    'individuals_handler',
    'appointment_handler',
    'appointment_callback_handler',
    'process_appointment',  # ← Должна быть эта строка
    'question_handler',
    'process_question',  # ← И эта строка
    'admin_handler',
    'admin_commands_handler',
    'admin_callback_handler',
    'contacts_handler',
    'about_handler',
]
```

## Быстрое решение:

Скопируйте содержимое файла `handlers/__init__.py` из локальной папки и замените на Railway.
