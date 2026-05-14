from sqlalchemy.orm import Session
from app.models import Pedido, Producto, ItemPedido, Asociacion
from app.modules.documents.model import Documento
from app.modules.orders.model import OrderEvent
from app.modules.dashboard.serializers import serializar_pedido, serializar_documento, serializar_evento

def widget_pedidos_recientes(db: Session, email: str, tipo_usuario: str, limite: int = 5) -> list:
    """Pedidos recientes del usuario según su rol."""
    if tipo_usuario == "asociacion":
        # Pedidos que contienen productos de esta asociación
        pedidos = db.query(Pedido).join(ItemPedido).join(Producto).filter(
            Producto.asociacion_email == email
        ).order_by(Pedido.fecha_creacion.desc()).limit(limite).all()
    else:
        pedidos = db.query(Pedido).filter(Pedido.comprador_email == email).order_by(Pedido.fecha_creacion.desc()).limit(limite).all()
    return [serializar_pedido(p) for p in pedidos]

def widget_documentos_recientes(db: Session, pedido_id: str, limite: int = 3) -> list:
    docs = db.query(Documento).filter(Documento.pedido_id == pedido_id).order_by(Documento.fecha_generacion.desc()).limit(limite).all()
    return [serializar_documento(d) for d in docs]

def widget_timeline(db: Session, pedido_id: str) -> list:
    eventos = db.query(OrderEvent).filter(OrderEvent.pedido_id == pedido_id).order_by(OrderEvent.fecha.asc()).all()
    return [serializar_evento(e) for e in eventos]

def widget_productos_activos(db: Session, email: str) -> list:
    productos = db.query(Producto).filter(Producto.asociacion_email == email).all()
    return [{"id": p.id, "nombre": p.nombre, "precio": p.precio, "stock": p.stock} for p in productos]