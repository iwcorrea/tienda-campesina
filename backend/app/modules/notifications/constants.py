"""
Canales de notificación, tipos y mapeo de eventos a plantillas.
"""

# Canales disponibles (el único implementado actualmente es in_app)
NOTIFICATION_CHANNELS = {
    "in_app": "Notificación interna (campanita)",
    "email": "Correo electrónico (futuro)",
    "sms": "Mensaje de texto (futuro)",
    "whatsapp": "WhatsApp (futuro)",
}

# Tipos de notificación
NOTIFICATION_TYPES = {
    "order_created": "Pedido creado",
    "order_confirmed": "Pedido confirmado",
    "transport_assigned": "Transporte asignado",
    "delivered": "Entrega realizada",
    "payment_confirmed": "Pago confirmado",
    "document_generated": "Documento generado",
    "contact_request": "Solicitud de contacto",
    "contact_accepted": "Contacto aceptado",
}

# Estados de una notificación
NOTIFICATION_STATUS = {
    "pending": "Pendiente",
    "sent": "Enviada",
    "read": "Leída",
    "failed": "Fallida",
}