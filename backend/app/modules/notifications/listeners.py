"""
Listeners que reaccionan a eventos del sistema y generan notificaciones.
Estas funciones son llamadas desde el dispatcher de eventos (events.py).
"""
from sqlalchemy.orm import Session
from app.modules.notifications.service import crear_notificacion
from app.models import Pedido

def on_order_created(db: Session, pedido_id: str, usuario_email: str, **kwargs):
    """Notifica a la asociación dueña de los productos del pedido."""
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        return
    # Notificar a cada asociación involucrada
    asociaciones = set()
    for item in pedido.items:
        if item.producto:
            asociaciones.add(item.producto.asociacion_email)
    for email_asoc in asociaciones:
        crear_notificacion(db, email_asoc, "order_created", pedido_id,
                           {"comprador_email": pedido.comprador_email, "pedido_id": pedido_id})

def on_order_confirmed(db: Session, pedido_id: str, usuario_email: str, **kwargs):
    """Notifica al comprador que su pedido fue aceptado."""
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if pedido:
        crear_notificacion(db, pedido.comprador_email, "order_confirmed", pedido_id,
                           {"pedido_id": pedido_id})

def on_transport_assigned(db: Session, pedido_id: str, usuario_email: str, **kwargs):
    """Notifica al comprador y al transportista."""
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if pedido:
        crear_notificacion(db, pedido.comprador_email, "transport_assigned", pedido_id,
                           {"pedido_id": pedido_id, "costo_envio": kwargs.get("costo_envio", 0)})
        # Transportista notificado en transporte_service directamente (ya existente)

def on_delivered(db: Session, pedido_id: str, usuario_email: str, **kwargs):
    """Notifica al comprador y a la asociación."""
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if pedido:
        crear_notificacion(db, pedido.comprador_email, "delivered", pedido_id,
                           {"pedido_id": pedido_id})
        # Notificar a la asociación
        for item in pedido.items:
            if item.producto:
                crear_notificacion(db, item.producto.asociacion_email, "delivered", pedido_id,
                                   {"pedido_id": pedido_id})
                break

def on_payment_confirmed(db: Session, pedido_id: str, usuario_email: str, **kwargs):
    """Notifica a la asociación y al comprador."""
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if pedido:
        crear_notificacion(db, pedido.comprador_email, "payment_confirmed", pedido_id,
                           {"pedido_id": pedido_id, "monto": kwargs.get("monto", 0)})
        for item in pedido.items:
            if item.producto:
                crear_notificacion(db, item.producto.asociacion_email, "payment_confirmed", pedido_id,
                                   {"pedido_id": pedido_id, "monto": kwargs.get("monto", 0)})
                break

def on_document_generated(db: Session, pedido_id: str, usuario_email: str, **kwargs):
    """Notifica al comprador y a la asociación."""
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if pedido:
        crear_notificacion(db, pedido.comprador_email, "document_generated", pedido_id,
                           {"pedido_id": pedido_id, "tipo_documento": kwargs.get("tipo_documento", "")})
        for item in pedido.items:
            if item.producto:
                crear_notificacion(db, item.producto.asociacion_email, "document_generated", pedido_id,
                                   {"pedido_id": pedido_id, "tipo_documento": kwargs.get("tipo_documento", "")})
                break