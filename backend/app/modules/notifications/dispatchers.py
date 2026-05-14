"""
Despachadores: deciden a través de qué canal(es) enviar la notificación
y ejecutan el envío.
"""
from sqlalchemy.orm import Session
from app.modules.notifications.model import Notificacion
from app.modules.notifications.channels import enviar_in_app

def despachar(db: Session, notificacion: Notificacion):
    """Envía la notificación por los canales configurados para ese tipo de evento."""
    # Por ahora, todas las notificaciones van por in_app.
    # En el futuro, se podría leer la preferencia del usuario.
    enviar_in_app(db, notificacion)