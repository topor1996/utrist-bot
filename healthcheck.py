"""
Health Check сервер для мониторинга состояния бота
Запускается параллельно с основным ботом
"""
import asyncio
from aiohttp import web
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Глобальные переменные для отслеживания состояния
bot_started_at: datetime | None = None
last_update_at: datetime | None = None
is_healthy = False


def set_bot_started():
    """Вызывается при старте бота"""
    global bot_started_at, is_healthy
    bot_started_at = datetime.now()
    is_healthy = True


def set_bot_stopped():
    """Вызывается при остановке бота"""
    global is_healthy
    is_healthy = False


def update_last_activity():
    """Обновляет время последней активности"""
    global last_update_at
    last_update_at = datetime.now()


async def health_handler(request):
    """Обработчик /health эндпоинта"""
    if not is_healthy:
        return web.json_response(
            {"status": "unhealthy", "message": "Bot is not running"},
            status=503
        )

    uptime = None
    if bot_started_at:
        uptime = (datetime.now() - bot_started_at).total_seconds()

    return web.json_response({
        "status": "healthy",
        "started_at": bot_started_at.isoformat() if bot_started_at else None,
        "uptime_seconds": uptime,
        "last_activity": last_update_at.isoformat() if last_update_at else None,
    })


async def ready_handler(request):
    """Обработчик /ready эндпоинта (для Kubernetes)"""
    if is_healthy:
        return web.json_response({"status": "ready"})
    return web.json_response({"status": "not ready"}, status=503)


async def start_health_server(port: int = 8080):
    """Запускает HTTP сервер для health check"""
    app = web.Application()
    app.router.add_get('/health', health_handler)
    app.router.add_get('/ready', ready_handler)
    app.router.add_get('/', health_handler)  # Для удобства

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

    logger.info(f"Health check server started on port {port}")

    return runner


async def stop_health_server(runner):
    """Останавливает HTTP сервер"""
    await runner.cleanup()
    logger.info("Health check server stopped")
