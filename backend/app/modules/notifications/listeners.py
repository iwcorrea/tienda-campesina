from sqlalchemy.orm import Session
from app.events.dispatcher import EventDispatcher
from app.events.payloads import OrderBasePayload, PaymentConfirmedPayload
from app.modules.notifications.service import crear_notificacion

def _on_order_created(payload: OrderBasePayload, db: Session):
    # Notificar al vendedor (asociación) que recibió un nuevo pedido
    vendedor_email = payload.extra.get("vendedor_email", "")
    if vendedor_email:
        crear_notificacion(
            db,
            usuario_email=vendedor_email,
            tipo_evento="order_created",
            referencia_pedido_id=payload.pedido_id,
            datos_extra={"comprador_email": payload.usuario_email}
        )
    # Notificar al comprador
    crear_notificacion(
        db,
        usuario_email=payload.usuario_email,
        tipo_evento="order_created",
        referencia_pedido_id=payload.pedido_id,
        datos_extra={"comprador_email": payload.usuario_email}
    )

def _on_payment_confirmed(payload: PaymentConfirmedPayload, db: Session):
    # Notificar al vendedor
    crear_notificacion(
        db,
        usuario_email=payload.vendedor_email,
        tipo_evento="payment_received",
        referencia_pedido_id=payload.pedido_id,
        datos_extra={
            "monto_total": payload.monto_total,
            "comision_plataforma": payload.comision_plataforma,
        }
    )
    # Notificar al comprador
    crear_notificacion(
        db,
        usuario_email=payload.usuario_email,
        tipo_evento="payment_confirmed",
        referencia_pedido_id=payload.pedido_id,
        datos_extra={"monto_total": payload.monto_total}
    )
    # Notificar al transportista si aplica
    if payload.transportista_email and payload.costo_envio > 0:
        from app.services.pago_service import COMISION_PLATAFORMA
        comision_envio = int(payload.costo_envio * COMISION_PLATAFORMA / 100)
        monto_transportista = payload.costo_envio - comision_envio
        crear_notificacion(
            db,
            usuario_email=payload.transportista_email,
            tipo_evento="transport_payment_paid",
            referencia_pedido_id=payload.pedido_id,
            datos_extra={"monto_transportista": monto_transportista}
        )

def _on_document_generated(payload: OrderBasePayload, db: Session):
    # Notificar al generador
    crear_notificacion(
        db,
        usuario_email=payload.usuario_email,
        tipo_evento="document_generated",
        referencia_pedido_id=payload.pedido_id,
        datos_extra={"tipo": payload.extra.get("tipo", "documento")}
    )

def register(dispatcher: EventDispatcher):
    dispatcher.register("order_created", _on_order_created)
    dispatcher.register("payment_confirmed", _on_payment_confirmed)
    dispatcher.register("document_generated", _on_document_generated)