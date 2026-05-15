from .dispatcher import EventDispatcher

def register_all_listeners(dispatcher: EventDispatcher):
    from app.modules.notifications.listeners import register as register_notifications
    # Chat listeners se registrarán en Tarea 4
    # from app.modules.chat.listeners import register as register_chat

    register_notifications(dispatcher)
    # register_chat(dispatcher)