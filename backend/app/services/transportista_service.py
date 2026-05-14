from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Pedido, Transportista
from app.modules.orders.events import registrar_evento

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
        total_productos = 0
        for item in items:
            nombre_producto = item.producto.nombre if item.producto else "Producto eliminado"
            subtotal = item.cantidad * item.precio_unitario_inicial
            total_productos += subtotal
            productos.append({"nombre": nombre_producto, "cantidad": item.cantidad})

        comision_envio = int(p.costo_envio * 0.08) if p.costo_envio else 0
        monto_transportista = p.costo_envio - comision_envio if p.costo_envio else 0

        asociacion_email = ""
        for item in p.items:
            if item.producto:
                asociacion_email = item.producto.asociacion_email
                break

        resultado.append({
            "pedido_id": p.id,
            "comprador_email": p.comprador_email,
            "estado_pedido": p.estado,
            "estado_envio": p.estado_envio or "pendiente",
            "productos": productos,
            "total_productos": total_productos,
            "costo_envio": p.costo_envio or 0,
            "comision_plataforma_envio": comision_envio,
            "monto_transportista": monto_transportista,
            "fecha": p.fecha_creacion,
            "asociacion_email": asociacion_email,
        })
    return resultado


def actualizar_estado_envio(db: Session, pedido_id: str, transportista_id: str, nuevo_estado: str) -> bool:
    pedido = db.query(Pedido).filter(
        Pedido.id == pedido_id,
        Pedido.transportista_id == transportista_id
    ).first()
    if not pedido:
        return False
    estado_anterior = pedido.estado_envio
    pedido.estado_envio = nuevo_estado
    if nuevo_estado == "entregado":
        pedido.estado = "entregado"
    db.commit()

    tipo_evento = "in_transit" if nuevo_estado == "en_transito" else "delivered" if nuevo_estado == "entregado" else "note_added"
    registrar_evento(
        db,
        pedido_id,
        tipo_evento,
        usuario_email="sistema",
        estado_anterior=estado_anterior,
        estado_nuevo=nuevo_estado,
        descripcion=f"Estado de envío cambiado de '{estado_anterior}' a '{nuevo_estado}'"
    )
    return True


def asignar_transportista_a_pedido(
    db: Session,
    pedido_id: str,
    transportista_id: str,
    email_asociacion: str,
    costo_envio: int = 0
) -> Optional[Pedido]:
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
    pedido.costo_envio = costo_envio
    db.commit()

    registrar_evento(
        db,
        pedido.id,
        "transport_assigned",
        usuario_email=email_asociacion,
        estado_anterior="aceptado",
        estado_nuevo="pendiente_envio",
        descripcion=f"Transportista {transportista_id} asignado, costo envío ${costo_envio}"
    )
    return pedido