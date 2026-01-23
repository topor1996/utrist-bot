from telegram import Update, InputFile
from telegram.ext import ContextTypes
from database import (
    is_admin, get_pending_appointments, get_new_questions, get_appointments_by_date,
    update_appointment_status, update_question_status, get_appointment_by_id, get_question_by_id,
    get_appointment_history
)
from keyboards.admin import (
    admin_keyboard, appointments_list_keyboard, questions_list_keyboard,
    appointment_actions_keyboard, question_actions_keyboard, export_keyboard
)
from keyboards.main_menu import main_menu_keyboard
from utils.export import export_appointments_csv, export_questions_csv, format_history_entry
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)

async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик админ-панели"""
    user_id = update.effective_user.id
    
    if not await is_admin(user_id):
        await update.message.reply_text(
            "❌ У вас нет доступа к админ-панели.",
            reply_markup=main_menu_keyboard()
        )
        return
    
    text = """
🔐 Админ-панель

Выберите действие:
"""
    await update.message.reply_text(
        text,
        reply_markup=admin_keyboard()
    )

async def admin_commands_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команд админа"""
    user_id = update.effective_user.id
    
    if not await is_admin(user_id):
        return
    
    text = update.message.text
    
    if text == '📋 Новые заявки':
        appointments = await get_pending_appointments()
        questions = await get_new_questions()
        
        if not appointments and not questions:
            await update.message.reply_text(
                "✅ Нет новых заявок и вопросов.",
                reply_markup=admin_keyboard()
            )
            return
        
        msg = f"📋 Новые заявки:\n\n"
        msg += f"📞 Записи на консультацию: {len(appointments)}\n"
        msg += f"❓ Вопросы: {len(questions)}\n\n"
        msg += "Используйте кнопки ниже для просмотра:"
        
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = [
            [InlineKeyboardButton('📞 Записи', callback_data='appt_list')],
            [InlineKeyboardButton('❓ Вопросы', callback_data='q_list')],
            [InlineKeyboardButton('🔙 Назад', callback_data='admin_back')]
        ]
        
        await update.message.reply_text(
            msg,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif text == '📅 Календарь записей':
        today = date.today()
        week_appointments = []
        
        for i in range(7):
            check_date = today + timedelta(days=i)
            appointments = await get_appointments_by_date(check_date)
            if appointments:
                week_appointments.extend(appointments)
        
        if not week_appointments:
            await update.message.reply_text(
                "📅 На ближайшую неделю нет записей.",
                reply_markup=admin_keyboard()
            )
            return
        
        msg = "📅 Записи на ближайшую неделю:\n\n"
        for apt in sorted(week_appointments, key=lambda x: (x['appointment_date'], x['appointment_time'])):
            msg += f"📅 {apt['appointment_date']} {apt['appointment_time']}\n"
            msg += f"   {apt['client_name']} - {apt['client_phone']}\n"
            msg += f"   {apt['service_type']}\n\n"
        
        await update.message.reply_text(
            msg,
            reply_markup=admin_keyboard()
        )
    
    elif text == '📊 Статистика':
        appointments = await get_pending_appointments()
        questions = await get_new_questions()

        msg = f"""
📊 Статистика

📞 Ожидающих записей: {len(appointments)}
❓ Новых вопросов: {len(questions)}
"""
        await update.message.reply_text(
            msg,
            reply_markup=admin_keyboard()
        )

    elif text == '📥 Экспорт данных':
        await update.message.reply_text(
            "📥 **Экспорт данных**\n\nВыберите, что экспортировать:",
            parse_mode='Markdown',
            reply_markup=export_keyboard()
        )

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback от админ-кнопок"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not await is_admin(user_id):
        await query.answer("❌ Нет доступа", show_alert=True)
        return
    
    data = query.data
    logger.info(f"admin_callback_handler вызван с data: {data}")
    
    if data == 'admin_back':
        await query.edit_message_text(
            "🔐 Админ-панель",
            reply_markup=None
        )
        await query.message.reply_text(
            "Выберите действие:",
            reply_markup=admin_keyboard()
        )
    
    elif data == 'appt_list':
        appointments = await get_pending_appointments()
        if not appointments:
            await query.edit_message_text(
                "✅ Нет новых записей на консультацию.",
                reply_markup=None
            )
            return
        
        await query.edit_message_text(
            "📞 Записи на консультацию:",
            reply_markup=appointments_list_keyboard(appointments, page=0)
        )
    
    elif data.startswith('appt_page_'):
        # Обработка пагинации списка заявок
        page = int(data.split('_')[-1])
        appointments = await get_pending_appointments()
        if not appointments:
            await query.edit_message_text(
                "✅ Нет новых записей на консультацию.",
                reply_markup=None
            )
            return
        
        await query.edit_message_text(
            f"📞 Записи на консультацию (страница {page + 1}):",
            reply_markup=appointments_list_keyboard(appointments, page=page)
        )
    
    elif data.startswith('appt_detail_'):
        try:
            appointment_id = int(data.split('_')[-1])
            logger.info(f"Запрос деталей заявки с ID: {appointment_id}")
        except (ValueError, IndexError) as e:
            logger.error(f"Ошибка парсинга ID заявки из '{data}': {e}")
            await query.answer("❌ Ошибка: неверный ID заявки", show_alert=True)
            return
        
        appointment = await get_appointment_by_id(appointment_id)
        logger.info(f"Заявка получена из БД: {appointment is not None}, данные: {appointment}")
        
        if not appointment:
            logger.warning(f"Заявка с ID {appointment_id} не найдена в БД")
            await query.answer("❌ Заявка не найдена", show_alert=True)
            return
        
        # Формируем сообщение с деталями заявки
        msg = f"""📋 **Заявка #{appointment_id}**

📝 **Услуга:** {appointment['service_type']}
👤 **ФИО:** {appointment['client_name']}
📞 **Телефон:** {appointment['client_phone']}
📧 **Email:** {appointment.get('client_email', 'не указан')}
"""
        
        # Дата и время (могут быть None для упрощенных заявок)
        if appointment.get('appointment_date'):
            msg += f"📅 **Дата:** {appointment['appointment_date']}\n"
        if appointment.get('appointment_time'):
            msg += f"⏰ **Время:** {appointment['appointment_time']}\n"
        
        if appointment.get('comment'):
            msg += f"💬 **Комментарий:** {appointment['comment']}\n"
        
        # Статус
        status_emoji = {
            'pending': '⏳',
            'confirmed': '✅',
            'cancelled': '❌',
            'completed': '✔️',
            'payment_sent': '💳'
        }.get(appointment['status'], '❓')

        status_text = {
            'pending': 'Ожидает',
            'confirmed': 'Подтверждена',
            'cancelled': 'Отменена',
            'completed': 'Завершена',
            'payment_sent': 'Отправлена в оплату'
        }.get(appointment['status'], appointment['status'])
        
        msg += f"\n{status_emoji} **Статус:** {status_text}"
        
        # Дата создания
        created_at = appointment.get('created_at', 'неизвестно')
        if created_at and isinstance(created_at, str):
            # Если это строка из БД, можно форматировать
            msg += f"\n⏰ **Создана:** {created_at}"
        elif created_at:
            msg += f"\n⏰ **Создана:** {created_at}"
        
        try:
            await query.edit_message_text(
                msg,
                parse_mode='Markdown',
                reply_markup=appointment_actions_keyboard(appointment_id)
            )
        except Exception as e:
            # Если ошибка с Markdown, пробуем без него
            logger.error(f"Ошибка отправки деталей заявки: {e}")
            await query.edit_message_text(
                msg.replace('*', ''),
                reply_markup=appointment_actions_keyboard(appointment_id)
            )
    
    elif data.startswith('appt_confirm_'):
        try:
            appointment_id = int(data.split('_')[-1])
            logger.info(f"Подтверждение заявки с ID: {appointment_id}")
        except (ValueError, IndexError) as e:
            logger.error(f"Ошибка парсинга ID заявки из '{data}': {e}")
            await query.answer("❌ Ошибка: неверный ID заявки", show_alert=True)
            return

        await update_appointment_status(appointment_id, 'confirmed', changed_by=user_id)
        appointment = await get_appointment_by_id(appointment_id)
        
        if not appointment:
            await query.answer("❌ Заявка не найдена", show_alert=True)
            return
        
        # Формируем сообщение с правильной информацией
        msg = f"✅ **Запись подтверждена**\n\n"
        msg += f"👤 **ФИО:** {appointment['client_name']}\n"
        msg += f"📝 **Услуга:** {appointment['service_type']}\n"
        msg += f"📞 **Телефон:** {appointment['client_phone']}\n"
        
        if appointment.get('client_email'):
            msg += f"📧 **Email:** {appointment['client_email']}\n"
        
        if appointment.get('appointment_date') and appointment.get('appointment_time'):
            msg += f"📅 **Дата:** {appointment['appointment_date']}\n"
            msg += f"⏰ **Время:** {appointment['appointment_time']}\n"
        else:
            msg += f"📅 **Дата/время:** не указаны (заявка без конкретного времени)\n"
        
        try:
            await query.edit_message_text(
                msg,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения о подтверждении: {e}")
            await query.edit_message_text(
                msg.replace('*', '')
            )
    
    elif data.startswith('appt_cancel_'):
        try:
            appointment_id = int(data.split('_')[-1])
            logger.info(f"Отмена заявки с ID: {appointment_id}")
        except (ValueError, IndexError) as e:
            logger.error(f"Ошибка парсинга ID заявки из '{data}': {e}")
            await query.answer("❌ Ошибка: неверный ID заявки", show_alert=True)
            return

        await update_appointment_status(appointment_id, 'cancelled', changed_by=user_id)
        appointment = await get_appointment_by_id(appointment_id)
        
        if not appointment:
            await query.answer("❌ Заявка не найдена", show_alert=True)
            return
        
        # Формируем сообщение с правильной информацией
        msg = f"❌ **Запись отменена**\n\n"
        msg += f"👤 **ФИО:** {appointment['client_name']}\n"
        msg += f"📝 **Услуга:** {appointment['service_type']}\n"
        msg += f"📞 **Телефон:** {appointment['client_phone']}\n"
        
        if appointment.get('client_email'):
            msg += f"📧 **Email:** {appointment['client_email']}\n"
        
        if appointment.get('appointment_date') and appointment.get('appointment_time'):
            msg += f"📅 **Дата:** {appointment['appointment_date']}\n"
            msg += f"⏰ **Время:** {appointment['appointment_time']}\n"
        
        try:
            await query.edit_message_text(
                msg,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения об отмене: {e}")
            await query.edit_message_text(
                msg.replace('*', '')
            )
    
    elif data.startswith('appt_call_'):
        # Показать телефон клиента
        try:
            appointment_id = int(data.split('_')[-1])
            appointment = await get_appointment_by_id(appointment_id)
            if appointment:
                await query.answer(f"📞 Телефон: {appointment['client_phone']}", show_alert=True)
            else:
                await query.answer("❌ Заявка не найдена", show_alert=True)
        except (ValueError, IndexError) as e:
            logger.error(f"Ошибка парсинга ID заявки из '{data}': {e}")
            await query.answer("❌ Ошибка: неверный ID заявки", show_alert=True)
    
    elif data.startswith('q_call_'):
        # Показать телефон клиента для вопроса
        try:
            question_id = int(data.split('_')[-1])
            question = await get_question_by_id(question_id)
            if question and question.get('client_phone'):
                await query.answer(f"📞 Телефон: {question['client_phone']}", show_alert=True)
            else:
                await query.answer("❌ Телефон не указан", show_alert=True)
        except (ValueError, IndexError) as e:
            logger.error(f"Ошибка парсинга ID вопроса из '{data}': {e}")
            await query.answer("❌ Ошибка: неверный ID вопроса", show_alert=True)
    
    elif data == 'q_list':
        questions = await get_new_questions()
        if not questions:
            await query.edit_message_text(
                "✅ Нет новых вопросов.",
                reply_markup=None
            )
            return
        
        await query.edit_message_text(
            "❓ Новые вопросы:",
            reply_markup=questions_list_keyboard(questions, page=0)
        )
    
    elif data.startswith('q_page_'):
        # Обработка пагинации списка вопросов
        page = int(data.split('_')[-1])
        questions = await get_new_questions()
        if not questions:
            await query.edit_message_text(
                "✅ Нет новых вопросов.",
                reply_markup=None
            )
            return
        
        await query.edit_message_text(
            f"❓ Новые вопросы (страница {page + 1}):",
            reply_markup=questions_list_keyboard(questions, page=page)
        )
    
    elif data.startswith('q_detail_'):
        question_id = int(data.split('_')[-1])
        question = await get_question_by_id(question_id)
        
        msg = f"""
❓ Вопрос #{question_id}

👤 Имя: {question['client_name'] or 'не указано'}
📞 Телефон: {question['client_phone'] or 'не указан'}
💬 Вопрос: {question['question_text']}
📊 Статус: {question['status']}
"""
        await query.edit_message_text(
            msg,
            reply_markup=question_actions_keyboard(question_id)
        )
    
    elif data.startswith('q_answered_'):
        question_id = int(data.split('_')[-1])
        await update_question_status(question_id, 'answered')
        question = await get_question_by_id(question_id)
        await query.edit_message_text(
            f"✅ Вопрос отмечен как отвеченный\n\n{question['question_text'][:50]}..."
        )
    
    elif data.startswith('q_close_'):
        question_id = int(data.split('_')[-1])
        await update_question_status(question_id, 'closed')
        question = await get_question_by_id(question_id)
        await query.edit_message_text(
            f"❌ Вопрос закрыт\n\n{question['question_text'][:50]}..."
        )
    
    elif data.startswith('appt_payment_'):
        # Начинаем процесс отправки в оплату
        try:
            appointment_id = int(data.split('_')[-1])
            appointment = await get_appointment_by_id(appointment_id)

            if not appointment:
                await query.answer("❌ Заявка не найдена", show_alert=True)
                return

            # Сохраняем данные для оплаты в контексте
            context.user_data['payment_appointment_id'] = appointment_id
            context.user_data['payment_user_id'] = appointment['user_id']
            context.user_data['payment_state'] = 'waiting_amount'
            context.user_data['payment_service'] = appointment['service_type']
            context.user_data['payment_client_name'] = appointment['client_name']

            await query.edit_message_text(
                f"💳 **Отправка в оплату**\n\n"
                f"📋 Заявка #{appointment_id}\n"
                f"👤 Клиент: {appointment['client_name']}\n"
                f"📝 Услуга: {appointment['service_type']}\n\n"
                f"Введите сумму к оплате (только число, например: 7000):\n\n"
                f"Для отмены нажмите /admin",
                parse_mode='Markdown'
            )
            await query.answer("Введите сумму к оплате")
        except (ValueError, IndexError) as e:
            logger.error(f"Ошибка парсинга ID заявки из '{data}': {e}")
            await query.answer("❌ Ошибка: неверный ID заявки", show_alert=True)

    elif data.startswith('q_reply_'):
        # Начинаем процесс ответа на вопрос
        try:
            question_id = int(data.split('_')[-1])
            question = await get_question_by_id(question_id)

            if not question:
                await query.answer("❌ Вопрос не найден", show_alert=True)
                return

            # Сохраняем ID вопроса в контексте администратора
            context.user_data['replying_to_question'] = question_id
            context.user_data['replying_to_user'] = question['user_id']

            await query.edit_message_text(
                f"💬 **Ответ на вопрос #{question_id}**\n\n"
                f"Вопрос: {question['question_text']}\n\n"
                f"Напишите ваш ответ. Он будет отправлен пользователю в личные сообщения.\n\n"
                f"Для отмены нажмите /admin",
                parse_mode='Markdown'
            )
            await query.answer("Напишите ответ на вопрос")
        except (ValueError, IndexError) as e:
            logger.error(f"Ошибка парсинга ID вопроса из '{data}': {e}")
            await query.answer("❌ Ошибка: неверный ID вопроса", show_alert=True)

    # История изменений заявки
    elif data.startswith('appt_history_'):
        try:
            appointment_id = int(data.split('_')[-1])
            history = await get_appointment_history(appointment_id)
            appointment = await get_appointment_by_id(appointment_id)

            if not appointment:
                await query.answer("❌ Заявка не найдена", show_alert=True)
                return

            msg = f"📜 **История заявки #{appointment_id}**\n\n"
            msg += f"👤 {appointment['client_name']}\n"
            msg += f"📝 {appointment['service_type']}\n\n"

            if history:
                msg += "**Изменения статуса:**\n"
                for entry in history:
                    msg += format_history_entry(entry) + "\n"
            else:
                msg += "_История изменений пуста_"

            from telegram import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = [[InlineKeyboardButton('🔙 Назад к заявке', callback_data=f'appt_detail_{appointment_id}')]]

            await query.edit_message_text(
                msg,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except (ValueError, IndexError) as e:
            logger.error(f"Ошибка парсинга ID заявки из '{data}': {e}")
            await query.answer("❌ Ошибка: неверный ID заявки", show_alert=True)

    # Экспорт данных
    elif data == 'export_appointments_all':
        await query.answer("⏳ Формирую файл...")
        try:
            file_data, filename = await export_appointments_csv()
            await query.message.reply_document(
                document=InputFile(file_data, filename=filename),
                caption="📥 Все заявки"
            )
            await query.edit_message_text("✅ Файл экспортирован", reply_markup=None)
        except Exception as e:
            logger.error(f"Ошибка экспорта: {e}")
            await query.edit_message_text(f"❌ Ошибка экспорта: {e}", reply_markup=None)

    elif data == 'export_appointments_pending':
        await query.answer("⏳ Формирую файл...")
        try:
            file_data, filename = await export_appointments_csv(status='pending')
            await query.message.reply_document(
                document=InputFile(file_data, filename=filename),
                caption="📥 Ожидающие заявки"
            )
            await query.edit_message_text("✅ Файл экспортирован", reply_markup=None)
        except Exception as e:
            logger.error(f"Ошибка экспорта: {e}")
            await query.edit_message_text(f"❌ Ошибка экспорта: {e}", reply_markup=None)

    elif data == 'export_appointments_confirmed':
        await query.answer("⏳ Формирую файл...")
        try:
            file_data, filename = await export_appointments_csv(status='confirmed')
            await query.message.reply_document(
                document=InputFile(file_data, filename=filename),
                caption="📥 Подтверждённые заявки"
            )
            await query.edit_message_text("✅ Файл экспортирован", reply_markup=None)
        except Exception as e:
            logger.error(f"Ошибка экспорта: {e}")
            await query.edit_message_text(f"❌ Ошибка экспорта: {e}", reply_markup=None)

    elif data == 'export_questions':
        await query.answer("⏳ Формирую файл...")
        try:
            file_data, filename = await export_questions_csv()
            await query.message.reply_document(
                document=InputFile(file_data, filename=filename),
                caption="📥 Все вопросы"
            )
            await query.edit_message_text("✅ Файл экспортирован", reply_markup=None)
        except Exception as e:
            logger.error(f"Ошибка экспорта: {e}")
            await query.edit_message_text(f"❌ Ошибка экспорта: {e}", reply_markup=None)