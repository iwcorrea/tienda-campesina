import math
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, selectinload
from app.models import Pedido, ItemPedido

def listar_pedidos(
    db: Session,
    pagina: int = 1,
    por_pagina: int = 10,
    comprador_email: Optional[str] = None,
    estado: Optional[str] = None,
) -> Tuple[List[Pedido], int]:
    query = db.query(Pedido).options(
        selectinload(Pedido.items).selectinload(ItemPedido.producto),
        selectinload(Pedido.items).selectinload(ItemPedido.respuestas)
    )
    if comprador_email:
        query = query.filter(Pedido.comprador_email == comprador_email)
    if estado:
        query = query.filter(Pedido.estado == estado)
    total = query.count()
    offset = (pagina - 1) * por_pagina
    pedidos = query.order_by(Pedido.fecha_creacion.desc()).offset(offset).limit(por_pagina).all()
    return pedidos, total

def obtener_pedido_por_id(db: Session, pedido_id: str) -> Optional[Pedido]:
    return (
        db.query(Pedido)
        .options(
            selectinload(Pedido.items).selectinload(ItemPedido.producto),
            selectinload(Pedido.items).selectinload(ItemPedido.respuestas)
        )
        .filter(Pedido.id == pedido_id)
        .first()
    )