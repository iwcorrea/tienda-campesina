from .dispatcher import EventDispatcher

def register_all_listeners(dispatcher: EventDispatcher):
    from app.modules.notifications.listeners import register as register_notifications
    from app.modules.documents.listeners import register as register_documents
    # Chat listeners se registrarán en el futuro

    register_notifications(dispatcher)
    register_documents(dispatcher)