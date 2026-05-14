"""
Servicio de dominio para pedidos agrícolas.
Contiene la lógica de negocio pura, sin dependencias HTTP.
"""
import uuid
from sqlalchemy.orm import Session
from app.models import Pedido
from app.modules.orders.constants import ORDER_STATES
from app.modules.orders.validators import validar_transicion
from app.modules.orders.events import registrar_evento

def crear_pedido(
    db: Session,
    comprador_email: str,
) -> Pedido:
    """Crea un pedido en estado draft."""
    pedido = Pedido(
        id=str(uuid.uuid4()),
        comprador_email=comprador_email,
        estado="draft",
    )
    db.add(pedido)
    db.commit()
    db.refresh(pedido)
    registrar_evento(db, pedido.id, "order_created", usuario_email=comprador_email, estado_nuevo="draft")
    return pedido

def avanzar_estado(
    db: Session,
    pedido: Pedido,
    nuevo_estado: str,
    usuario_email: str = "",
    metadata: str = ""
) -> bool:
    """Intenta avanzar el pedido al nuevo estado, validando la transición."""
    if not validar_transicion(pedido.estado, nuevo_estado):
        raise ValueError(f"No se puede pasar de '{pedido.estado}' a '{nuevo_estado}'")
    estado_anterior = pedido.estado
    pedido.estado = nuevo_estado
    db.commit()
    # Mapear el nuevo estado al tipo de evento correspondiente
    tipo_evento = f"order_{nuevo_estado}" if f"order_{nuevo_estado}" in [
        "order_confirmed", "order_cancelled", "order_completed", "order_verified", "order_disputed"
    ] else "note_added"
    registrar_evento(
        db,
        pedido.id,
        tipo_evento,
        usuario_email=usuario_email,
        estado_anterior=estado_anterior,
        estado_nuevo=nuevo_estado,
        metadata_extra=metadata,
    )
    return True