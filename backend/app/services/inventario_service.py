import uuid
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models import Producto, MovimientoInventario


def inicializar_stock(db: Session, producto: Producto, cantidad: int, referencia: str = "creacion") -> MovimientoInventario:
    existe = db.query(MovimientoInventario).filter(
        MovimientoInventario.producto_id == producto.id
    ).first()
    if existe:
        return None

    stock_anterior = producto.stock or 0
    nuevo_stock = stock_anterior + cantidad

    movimiento = MovimientoInventario(
        id=str(uuid.uuid4()),
        producto_id=producto.id,
        asociacion_email=producto.asociacion_email,
        tipo="entrada",
        cantidad=cantidad,
        stock_anterior=stock_anterior,
        stock_nuevo=nuevo_stock,
        referencia=referencia,
    )
    db.add(movimiento)
    producto.stock = nuevo_stock
    db.commit()
    return movimiento


def entrada_stock(db: Session, producto_id: str, cantidad: int, referencia: str = "ajuste", email_asociacion: str = "") -> Optional[MovimientoInventario]:
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        return None
    if email_asociacion and producto.asociacion_email != email_asociacion:
        return None

    stock_anterior = producto.stock or 0
    nuevo_stock = stock_anterior + cantidad

    movimiento = MovimientoInventario(
        id=str(uuid.uuid4()),
        producto_id=producto.id,
        asociacion_email=producto.asociacion_email,
        tipo="entrada",
        cantidad=cantidad,
        stock_anterior=stock_anterior,
        stock_nuevo=nuevo_stock,
        referencia=referencia,
    )
    db.add(movimiento)
    producto.stock = nuevo_stock
    db.commit()
    return movimiento


def salida_stock_manual(db: Session, producto_id: str, cantidad: int, referencia: str = "ajuste", email_asociacion: str = "") -> Optional[MovimientoInventario]:
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        return None
    if email_asociacion and producto.asociacion_email != email_asociacion:
        return None

    stock_anterior = producto.stock or 0
    nuevo_stock = max(0, stock_anterior - cantidad)

    movimiento = MovimientoInventario(
        id=str(uuid.uuid4()),
        producto_id=producto.id,
        asociacion_email=producto.asociacion_email,
        tipo="salida",
        cantidad=cantidad,
        stock_anterior=stock_anterior,
        stock_nuevo=nuevo_stock,
        referencia=referencia,
    )
    db.add(movimiento)
    producto.stock = nuevo_stock
    db.commit()
    return movimiento


def reservar_stock_por_cotizacion(db: Session, item_pedido_id: str) -> Optional[MovimientoInventario]:
    from app.models import ItemPedido
    item = db.query(ItemPedido).filter(ItemPedido.id == item_pedido_id).first()
    if not item or not item.producto:
        return None

    producto = item.producto
    stock_anterior = producto.stock or 0
    if stock_anterior < item.cantidad:
        return None

    nuevo_stock = stock_anterior - item.cantidad

    movimiento = MovimientoInventario(
        id=str(uuid.uuid4()),
        producto_id=producto.id,
        asociacion_email=producto.asociacion_email,
        tipo="reserva",
        cantidad=item.cantidad,
        stock_anterior=stock_anterior,
        stock_nuevo=nuevo_stock,
        referencia=item.pedido_id if item.pedido else "",
    )
    db.add(movimiento)
    producto.stock = nuevo_stock
    db.commit()
    return movimiento


def salida_stock_por_pedido(db: Session, pedido_id: str) -> List[MovimientoInventario]:
    from app.models import Pedido
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido or pedido.estado != "pagado":
        return []

    movimientos = []
    for item in pedido.items:
        producto = item.producto
        if not producto:
            continue

        # Si existe una reserva previa, la convertimos en salida real
        reserva = db.query(MovimientoInventario).filter(
            MovimientoInventario.producto_id == producto.id,
            MovimientoInventario.referencia == pedido_id,
            MovimientoInventario.tipo == "reserva"
        ).first()

        if reserva:
            reserva.tipo = "salida"
            db.commit()
            movimientos.append(reserva)
        else:
            stock_anterior = producto.stock
            nuevo_stock = max(0, stock_anterior - item.cantidad)

            movimiento = MovimientoInventario(
                id=str(uuid.uuid4()),
                producto_id=producto.id,
                asociacion_email=producto.asociacion_email,
                tipo="salida",
                cantidad=item.cantidad,
                stock_anterior=stock_anterior,
                stock_nuevo=nuevo_stock,
                referencia=pedido_id,
            )
            db.add(movimiento)
            producto.stock = nuevo_stock
            movimientos.append(movimiento)
            db.commit()

    return movimientos


def cancelar_reserva_pedido(db: Session, pedido_id: str) -> bool:
    reservas = db.query(MovimientoInventario).filter(
        MovimientoInventario.referencia == pedido_id,
        MovimientoInventario.tipo == "reserva"
    ).all()

    for r in reservas:
        producto = db.query(Producto).filter(Producto.id == r.producto_id).first()
        if producto:
            nuevo_stock = (producto.stock or 0) + r.cantidad
            producto.stock = nuevo_stock

            cancelacion = MovimientoInventario(
                id=str(uuid.uuid4()),
                producto_id=producto.id,
                asociacion_email=producto.asociacion_email,
                tipo="cancelacion",
                cantidad=r.cantidad,
                stock_anterior=producto.stock - r.cantidad,
                stock_nuevo=nuevo_stock,
                referencia=pedido_id,
            )
            db.add(cancelacion)
        db.delete(r)

    db.commit()
    return True


def listar_inventario_asociacion(db: Session, email: str) -> List[dict]:
    productos = db.query(Producto).filter(Producto.asociacion_email == email).all()
    resultado = []
    for p in productos:
        resultado.append({
            "id": p.id,
            "nombre": p.nombre,
            "stock_actual": p.stock or 0,
            "tipo": p.tipo,
            "precio": p.precio,
            "alerta_bajo": (p.stock or 0) <= 10 and p.tipo == "producto"
        })
    return resultado


def obtener_movimientos_producto(db: Session, producto_id: str, email_asociacion: str, pagina: int = 1, por_pagina: int = 15) -> Tuple[List[MovimientoInventario], int]:
    query = db.query(MovimientoInventario).filter(
        MovimientoInventario.producto_id == producto_id,
        MovimientoInventario.asociacion_email == email_asociacion,
    ).order_by(MovimientoInventario.fecha.desc())

    total = query.count()
    offset = (pagina - 1) * por_pagina
    movimientos = query.offset(offset).limit(por_pagina).all()
    return movimientos, total