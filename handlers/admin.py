from telegram import Update
from telegram.ext import ContextTypes
from database import is_admin, get_pending_appointments, get_new_questions, get_appointments_by_date
from keyboards.admin import admin_keyboard, appointments_list_keyboard, questions_list_keyboard, appointment_actions_keyboard, question_actions_keyboard
from keyboards.main_menu import main_menu_keyboard
from datetime import date, timedelta
from database import update_appointment_status, update_question_status, get_appointment_by_id, get_question_by_id

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
        from database import get_pending_appointments, get_new_questions
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

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback от админ-кнопок"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not await is_admin(user_id):
        await query.answer("❌ Нет доступа", show_alert=True)
        return
    
    data = query.data
    
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
            reply_markup=appointments_list_keyboard(appointments)
        )
    
    elif data.startswith('appt_detail_'):
        appointment_id = int(data.split('_')[-1])
        appointment = await get_appointment_by_id(appointment_id)
        
        msg = f"""
📋 Запись #{appointment_id}

👤 Имя: {appointment['client_name']}
📞 Телефон: {appointment['client_phone']}
📅 Дата: {appointment['appointment_date']}
⏰ Время: {appointment['appointment_time']}
📝 Услуга: {appointment['service_type']}
💬 Комментарий: {appointment['comment'] or 'нет'}
📊 Статус: {appointment['status']}
"""
        await query.edit_message_text(
            msg,
            reply_markup=appointment_actions_keyboard(appointment_id)
        )
    
    elif data.startswith('appt_confirm_'):
        appointment_id = int(data.split('_')[-1])
        await update_appointment_status(appointment_id, 'confirmed')
        appointment = await get_appointment_by_id(appointment_id)
        await query.edit_message_text(
            f"✅ Запись подтверждена\n\n{appointment['client_name']} - {appointment['appointment_date']} {appointment['appointment_time']}"
        )
    
    elif data.startswith('appt_cancel_'):
        appointment_id = int(data.split('_')[-1])
        await update_appointment_status(appointment_id, 'cancelled')
        appointment = await get_appointment_by_id(appointment_id)
        await query.edit_message_text(
            f"❌ Запись отменена\n\n{appointment['client_name']} - {appointment['appointment_date']} {appointment['appointment_time']}"
        )
    
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
            reply_markup=questions_list_keyboard(questions)
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
