from .dispatcher import EventDispatcher

def register_all_listeners(dispatcher: EventDispatcher):
    from app.modules.notifications.listeners import register as register_notifications
    from app.modules.documents.listeners import register as register_documents
    from app.modules.chat.listeners import register as register_chat
    from app.modules.orders.listeners import register as register_orders
    from app.modules.transport.listeners import register as register_transport
    from app.modules.billing.listeners import register as register_billing

    register_notifications(dispatcher)
    register_documents(dispatcher)
    register_chat(dispatcher)
    register_orders(dispatcher)
    register_transport(dispatcher)
    register_billing(dispatcher)