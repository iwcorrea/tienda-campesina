import math
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, selectinload
from app.models import Pedido, ItemPedido, Producto, Asociacion, RespuestaCotizacion
from sqlalchemy import desc

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


def listar_cotizaciones_enviadas(
    db: Session,
    comprador_email: str,
    pagina: int = 1,
    por_pagina: int = 15,
    estado: Optional[str] = None,
) -> Tuple[List[ItemPedido], int]:
    """
    Devuelve los ítems de pedido realizados por un comprador,
    con el producto, pedido y respuesta aceptada cargados.
    Filtra opcionalmente por estado de la cotización.
    """
    query = db.query(ItemPedido).join(Pedido).options(
        selectinload(ItemPedido.producto).selectinload(Producto.asociacion),
        selectinload(ItemPedido.pedido),
        selectinload(ItemPedido.respuestas)
    ).filter(Pedido.comprador_email == comprador_email)

    if estado == "pendiente":
        # Sin respuesta aceptada
        query = query.filter(~ItemPedido.respuestas.any(RespuestaCotizacion.aceptado == "aceptado"))
    elif estado == "aceptada":
        # Con respuesta aceptada pero pedido no pagado
        query = query.filter(
            ItemPedido.respuestas.any(RespuestaCotizacion.aceptado == "aceptado"),
            Pedido.estado != "pagado"
        )
    elif estado == "pagada":
        query = query.filter(Pedido.estado == "pagado")

    total = query.count()
    offset = (pagina - 1) * por_pagina
    items = query.order_by(desc(Pedido.fecha_creacion)).offset(offset).limit(por_pagina).all()
    return items, total


def actualizar_estado_pedido_si_aplica(db: Session, pedido_id: str):
    pedido = obtener_pedido_por_id(db, pedido_id)
    if not pedido:
        return
    todos_aceptados = True
    for item in pedido.items:
        if not any(r.aceptado == "aceptado" for r in item.respuestas):
            todos_aceptados = False
            break
    if todos_aceptados:
        pedido.estado = "aceptado"
        db.commit()