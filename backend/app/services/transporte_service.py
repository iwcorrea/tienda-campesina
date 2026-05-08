from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Pedido, Transportista

def listar_envios_transportista(db: Session, transportista_email: str) -> List[dict]:
    transportista = db.query(Transportista).filter(Transportista.email == transportista_email).first()
    if not transportista:
        return []

    pedidos = (
        db.query(Pedido)
        .filter(Pedido.transportista_id == transportista.id)
        .order_by(Pedido.fecha_creacion.desc())
        .all()
    )
    resultado = []
    for p in pedidos:
        items = p.items
        productos = []
        total = 0
        for item in items:
            nombre_producto = item.producto.nombre if item.producto else "Producto eliminado"
            subtotal = item.cantidad * item.precio_unitario_inicial
            total += subtotal
            productos.append({"nombre": nombre_producto, "cantidad": item.cantidad})

        resultado.append({
            "pedido_id": p.id,
            "comprador_email": p.comprador_email,
            "estado_pedido": p.estado,
            "estado_envio": p.estado_envio or "pendiente",
            "productos": productos,
            "total": total,
            "fecha": p.fecha_creacion
        })
    return resultado

def actualizar_estado_envio(db: Session, pedido_id: str, transportista_id: str, nuevo_estado: str) -> bool:
    pedido = db.query(Pedido).filter(
        Pedido.id == pedido_id,
        Pedido.transportista_id == transportista_id
    ).first()
    if not pedido:
        return False
    pedido.estado_envio = nuevo_estado
    if nuevo_estado == "entregado":
        pedido.estado = "entregado"
    db.commit()
    return True

def asignar_transportista_a_pedido(db: Session, pedido_id: str, transportista_id: str, email_asociacion: str) -> Optional[Pedido]:
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        return None
    pertenece = False
    for item in pedido.items:
        if item.producto and item.producto.asociacion_email == email_asociacion:
            pertenece = True
            break
    if not pertenece:
        return None

    pedido.transportista_id = transportista_id
    pedido.estado_envio = "pendiente"
    db.commit()
    return pedido