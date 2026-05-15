from .dispatcher import EventDispatcher

def register_all_listeners(dispatcher: EventDispatcher):
    from app.modules.notifications.listeners import register as register_notifications
    from app.modules.documents.listeners import register as register_documents
    from app.modules.chat.listeners import register as register_chat

    register_notifications(dispatcher)
    register_documents(dispatcher)
    register_chat(dispatcher)          # ← reactivado sin riesgos