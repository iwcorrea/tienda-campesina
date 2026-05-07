import math
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session, selectinload

from app.models.pedido import Pedido


def listar_pedidos(
    db: Session,
    pagina: int = 1,
    por_pagina: int = 10,
    comprador_id: Optional[int] = None,
    productor_id: Optional[int] = None,
    estado: Optional[str] = None,
) -> Tuple[List[Pedido], int]:
    """
    Lista pedidos con relaciones necesarias cargadas eagerly:
    - detalles (y su producto)
    - productor
    - comprador
    Filtros opcionales por comprador, productor, estado.
    Retorna (pedidos, total).
    """
    query = db.query(Pedido).options(
        selectinload(Pedido.detalles).selectinload(DetallePedido.producto),
        selectinload(Pedido.productor),
        selectinload(Pedido.comprador),
    )

    if comprador_id:
        query = query.filter(Pedido.comprador_id == comprador_id)
    if productor_id:
        query = query.filter(Pedido.productor_id == productor_id)
    if estado:
        query = query.filter(Pedido.estado == estado)

    total = query.count()
    offset = (pagina - 1) * por_pagina
    pedidos = query.order_by(Pedido.fecha_creacion.desc()).offset(offset).limit(por_pagina).all()
    return pedidos, total


def obtener_pedido_por_id(db: Session, pedido_id: int) -> Optional[Pedido]:
    """Pedido individual con las mismas relaciones cargadas."""
    return (
        db.query(Pedido)
        .options(
            selectinload(Pedido.detalles).selectinload(DetallePedido.producto),
            selectinload(Pedido.productor),
            selectinload(Pedido.comprador),
        )
        .filter(Pedido.id == pedido_id)
        .first()
    )