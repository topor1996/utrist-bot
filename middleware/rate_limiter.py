"""
Rate Limiter middleware для защиты от спама
"""
import time
import logging
from collections import defaultdict
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# Настройки rate limiting
MAX_MESSAGES_PER_MINUTE = 20  # Максимум сообщений в минуту
MAX_MESSAGES_PER_SECOND = 3   # Максимум сообщений в секунду
BLOCK_DURATION = 60           # Блокировка на 60 секунд при превышении лимита

# Хранилище для отслеживания сообщений пользователей
user_message_times: dict[int, list[float]] = defaultdict(list)
blocked_users: dict[int, float] = {}


def is_rate_limited(user_id: int) -> bool:
    """Проверяет, превышен ли лимит сообщений для пользователя"""
    current_time = time.time()

    # Проверяем, заблокирован ли пользователь
    if user_id in blocked_users:
        if current_time < blocked_users[user_id]:
            return True
        else:
            # Разблокируем пользователя
            del blocked_users[user_id]
            user_message_times[user_id] = []

    # Получаем историю сообщений пользователя
    message_times = user_message_times[user_id]

    # Удаляем старые записи (старше 1 минуты)
    message_times = [t for t in message_times if current_time - t < 60]
    user_message_times[user_id] = message_times

    # Проверяем лимит в секунду
    recent_messages = [t for t in message_times if current_time - t < 1]
    if len(recent_messages) >= MAX_MESSAGES_PER_SECOND:
        logger.warning(f"Rate limit exceeded (per second) for user {user_id}")
        blocked_users[user_id] = current_time + BLOCK_DURATION
        return True

    # Проверяем лимит в минуту
    if len(message_times) >= MAX_MESSAGES_PER_MINUTE:
        logger.warning(f"Rate limit exceeded (per minute) for user {user_id}")
        blocked_users[user_id] = current_time + BLOCK_DURATION
        return True

    # Добавляем текущее сообщение
    message_times.append(current_time)
    user_message_times[user_id] = message_times

    return False


async def rate_limit_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Middleware для проверки rate limit.
    Возвращает True если нужно заблокировать обработку, False если можно продолжить.
    """
    if not update.effective_user:
        return False

    user_id = update.effective_user.id

    if is_rate_limited(user_id):
        # Отправляем предупреждение только один раз при блокировке
        if user_id in blocked_users:
            block_end = blocked_users[user_id]
            remaining = int(block_end - time.time())
            if remaining > 55:  # Только что заблокировали
                try:
                    if update.message:
                        await update.message.reply_text(
                            f"⚠️ Слишком много сообщений. Подождите {remaining} секунд."
                        )
                except Exception as e:
                    logger.warning(f"Не удалось отправить предупреждение о rate limit: {e}")
        return True

    return False
