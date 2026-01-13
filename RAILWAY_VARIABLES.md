# Переменные окружения для Railway

## Скопируйте и добавьте в Railway:

В Railway откройте ваш проект → выберите сервис → вкладка **"Variables"** → нажмите **"New Variable"** и добавьте каждую переменную:

```
BOT_TOKEN=8506244542:AAHFZAl9YSz-eQ1qKDQQMtP6S7SnwbZJaj4
ADMIN_IDS=236217645
DATABASE_URL=sqlite:///bot_database.db
WORK_START_HOUR=9
WORK_END_HOUR=18
WORK_DAYS=1,2,3,4,5
```

## Пошаговая инструкция:

1. Откройте ваш проект на Railway: https://railway.com/project/0177079e-b17b-4c2c-86a5-4459109d5a44

2. Если еще нет сервиса, создайте "New Service" → "Empty Service"

3. Перейдите на вкладку **"Variables"**

4. Нажмите **"New Variable"** и добавьте каждую переменную отдельно:

   - **Name:** `BOT_TOKEN`
   - **Value:** `8506244542:AAHFZAl9YSz-eQ1qKDQQMtP6S7SnwbZJaj4`

   - **Name:** `ADMIN_IDS`
   - **Value:** `236217645`

   - **Name:** `DATABASE_URL`
   - **Value:** `sqlite:///bot_database.db`

   - **Name:** `WORK_START_HOUR`
   - **Value:** `9`

   - **Name:** `WORK_END_HOUR`
   - **Value:** `18`

   - **Name:** `WORK_DAYS`
   - **Value:** `1,2,3,4,5`

5. После добавления всех переменных, Railway автоматически перезапустит сервис

6. Проверьте логи в разделе "Logs" - должны быть сообщения о запуске бота

7. Найдите вашего бота в Telegram и отправьте `/start` - он должен ответить!

## Важно:

- ✅ Токен и ID уже указаны выше
- ✅ Не показывайте токен никому - это как пароль
- ✅ После добавления переменных бот должен запуститься автоматически
