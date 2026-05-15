from .dispatcher import EventDispatcher

def register_all_listeners(dispatcher: EventDispatcher):
    """Importa y registra todos los listeners de cada módulo."""
    from app.modules.notifications.listeners import register as register_notifications
    from app.modules.chat.listeners import register as register_chat

    register_notifications(dispatcher)
    register_chat(dispatcher)
    # Futuros módulos agregarán aquí su register