import math
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import desc, asc
from app.models import Pedido, ItemPedido, Producto, Asociacion, RespuestaCotizacion
from app.services.inventario_service import cancelar_reserva_pedido


def listar_pedidos(
    db: Session,
    pagina: int = 1,
    por_pagina: int = 10,
    comprador_email: Optional[str] = None,
    estado: Optional[str] = None,
    orden: str = "fecha",
) -> Tuple[List[Pedido], int]:
    query = db.query(Pedido).options(
        selectinload(Pedido.items).selectinload(ItemPedido.producto),
        selectinload(Pedido.items).selectinload(ItemPedido.respuestas)
    )
    if comprador_email:
        query = query.filter(Pedido.comprador_email == comprador_email)
    if estado:
        query = query.filter(Pedido.estado == estado)

    # Ordenamiento
    if orden == "total":
        query = query.order_by(desc(Pedido.costo_envio))  # se ordena en el viewmodel
    elif orden == "estado":
        query = query.order_by(asc(Pedido.estado))
    else:
        query = query.order_by(desc(Pedido.fecha_creacion))

    total = query.count()
    offset = (pagina - 1) * por_pagina
    pedidos = query.offset(offset).limit(por_pagina).all()
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
    orden: str = "fecha",
) -> Tuple[List[ItemPedido], int]:
    query = db.query(ItemPedido).join(Pedido).options(
        selectinload(ItemPedido.producto).selectinload(Producto.asociacion),
        selectinload(ItemPedido.pedido),
        selectinload(ItemPedido.respuestas)
    ).filter(Pedido.comprador_email == comprador_email)

    if estado == "pendiente":
        query = query.filter(~ItemPedido.respuestas.any(RespuestaCotizacion.aceptado == "aceptado"))
    elif estado == "aceptada":
        query = query.filter(
            ItemPedido.respuestas.any(RespuestaCotizacion.aceptado == "aceptado"),
            Pedido.estado != "pagado"
        )
    elif estado == "pagada":
        query = query.filter(Pedido.estado == "pagado")

    if orden == "producto":
        query = query.join(Producto).order_by(asc(Producto.nombre))
    elif orden == "asociacion":
        query = query.join(Producto).join(Asociacion).order_by(asc(Asociacion.nombre))
    elif orden == "estado":
        query = query.join(Pedido).order_by(asc(Pedido.estado))
    else:
        query = query.order_by(desc(Pedido.fecha_creacion))

    total = query.count()
    offset = (pagina - 1) * por_pagina
    items = query.offset(offset).limit(por_pagina).all()
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


def cancelar_pedido(db: Session, pedido_id: str, comprador_email: str) -> Optional[str]:
    """
    Cancela un pedido si no ha sido pagado.
    Retorna: "ok", "pagado" (no se puede), None (no encontrado).
    """
    pedido = db.query(Pedido).filter(
        Pedido.id == pedido_id,
        Pedido.comprador_email == comprador_email
    ).first()
    if not pedido:
        return None
    if pedido.estado == "pagado":
        return "pagado"

    # Liberar stock si hay reservas
    cancelar_reserva_pedido(db, pedido_id)

    # Eliminar el pedido
    db.delete(pedido)
    db.commit()
    return "ok"