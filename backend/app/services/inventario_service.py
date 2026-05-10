"""
Servicio de Inventario – Tienda Campesina
==========================================
Gestiona el stock real de productos y registra cada movimiento.
Se integra automáticamente con los procesos de creación de producto
y confirmación de pago.
"""

import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Producto, MovimientoInventario, Asociacion


def inicializar_stock(db: Session, producto: Producto, cantidad: int, referencia: str = "creacion") -> MovimientoInventario:
    """
    Registra una entrada de inventario al crear un producto por primera vez.
    Solo se ejecuta si el producto no tiene movimientos previos.
    """
    # Verificar si ya existe algún movimiento para este producto
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

    # Actualizar stock del producto
    producto.stock = nuevo_stock
    db.commit()
    return movimiento


def entrada_stock(db: Session, producto_id: str, cantidad: int, referencia: str = "ajuste") -> Optional[MovimientoInventario]:
    """Añade stock a un producto manualmente (para ajustes de inventario)."""
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
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


def salida_stock_por_pedido(db: Session, pedido_id: str) -> List[MovimientoInventario]:
    """
    Registra las salidas de inventario para todos los productos de un pedido
    que haya sido pagado. Se llama desde el servicio de pagos al confirmar.
    Retorna la lista de movimientos creados.
    """
    from app.models import Pedido
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido or pedido.estado != "pagado":
        return []

    movimientos = []
    for item in pedido.items:
        producto = item.producto
        if not producto:
            continue

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


def listar_inventario_asociacion(db: Session, email: str) -> List[dict]:
    """
    Devuelve el inventario actual de una asociación con sus movimientos recientes.
    """
    productos = db.query(Producto).filter(Producto.asociacion_email == email).all()
    resultado = []
    for p in productos:
        resultado.append({
            "id": p.id,
            "nombre": p.nombre,
            "stock_actual": p.stock,
            "tipo": p.tipo,
            "precio": p.precio,
        })
    return resultado


def obtener_movimientos_producto(db: Session, producto_id: str, email_asociacion: str) -> List[MovimientoInventario]:
    """Historial de movimientos de un producto específico."""
    return (
        db.query(MovimientoInventario)
        .filter(
            MovimientoInventario.producto_id == producto_id,
            MovimientoInventario.asociacion_email == email_asociacion,
        )
        .order_by(MovimientoInventario.fecha.desc())
        .all()
    )