from .start import start_handler, main_menu_handler
from .services import services_handler, legal_entities_handler, entrepreneurs_handler, individuals_handler
from .appointment import appointment_handler, appointment_callback_handler
from .question import question_handler
from .admin import admin_handler, admin_callback_handler
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
    'question_handler',
    'admin_handler',
    'admin_callback_handler',
    'contacts_handler',
    'about_handler',
]
