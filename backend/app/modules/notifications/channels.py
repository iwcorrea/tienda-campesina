"""
Simulación de canales de envío.
Actualmente solo in_app está implementado.
"""
from app.modules.notifications.model import Notificacion

def enviar_in_app(db, notificacion: Notificacion):
    """Marca la notificación como enviada (queda disponible en la campanita)."""
    notificacion.estado = "sent"
    from datetime import datetime, timezone
    notificacion.fecha_envio = datetime.now(timezone.utc)
    db.commit()

def enviar_email_placeholder(notificacion: Notificacion):
    """Futuro envío de email."""
    pass

def enviar_sms_placeholder(notificacion: Notificacion):
    """Futuro envío de SMS."""
    pass

def enviar_whatsapp_placeholder(notificacion: Notificacion):
    """Futuro envío de WhatsApp."""
    pass