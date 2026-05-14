from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Pedido, ItemPedido, Producto, Notificacion as NotifModel
from app.modules.documents.model import Documento

def calcular_metricas(db: Session, email: str, tipo_usuario: str) -> list:
    """Retorna una lista de métricas simples con título, valor e icono."""
    metricas = []

    if tipo_usuario == "asociacion":
        # Pedidos activos (pendientes, aceptados, pagados)
        activos = db.query(func.count(Pedido.id)).join(ItemPedido).join(Producto).filter(
            Producto.asociacion_email == email,
            Pedido.estado.in_(["pendiente", "aceptado", "pagado"])
        ).scalar() or 0
        metricas.append({"titulo": "Pedidos activos", "valor": activos, "icono": "📦"})

        # Entregas pendientes (estado_envio != entregado)
        pendientes = db.query(func.count(Pedido.id)).join(ItemPedido).join(Producto).filter(
            Producto.asociacion_email == email,
            Pedido.estado_envio != "entregado",
            Pedido.transportista_id.isnot(None)
        ).scalar() or 0
        metricas.append({"titulo": "Entregas pendientes", "valor": pendientes, "icono": "🚚"})

        # Documentos nuevos (generados en los últimos 7 días)
        docs = db.query(func.count(Documento.id)).filter(
            Documento.pedido_id.in_(
                db.query(Pedido.id).join(ItemPedido).join(Producto).filter(
                    Producto.asociacion_email == email
                )
            )
        ).scalar() or 0
        metricas.append({"titulo": "Documentos", "valor": docs, "icono": "📄"})

    elif tipo_usuario == "persona":
        # Pedidos activos del comprador
        activos = db.query(func.count(Pedido.id)).filter(
            Pedido.comprador_email == email,
            Pedido.estado.in_(["pendiente", "aceptado", "pagado"])
        ).scalar() or 0
        metricas.append({"titulo": "Mis pedidos activos", "valor": activos, "icono": "📦"})

        # Documentos disponibles
        docs = db.query(func.count(Documento.id)).filter(
            Documento.pedido_id.in_(
                db.query(Pedido.id).filter(Pedido.comprador_email == email)
            )
        ).scalar() or 0
        metricas.append({"titulo": "Documentos", "valor": docs, "icono": "📄"})

    elif tipo_usuario == "transportista":
        # Rutas asignadas (pedidos con transportista asignado)
        from app.models import Transportista
        transportista = db.query(Transportista).filter(Transportista.email == email).first()
        if transportista:
            asignados = db.query(func.count(Pedido.id)).filter(
                Pedido.transportista_id == transportista.id,
                Pedido.estado_envio != "entregado"
            ).scalar() or 0
            metricas.append({"titulo": "Envíos asignados", "valor": asignados, "icono": "🚚"})
            entregados = db.query(func.count(Pedido.id)).filter(
                Pedido.transportista_id == transportista.id,
                Pedido.estado_envio == "entregado"
            ).scalar() or 0
            metricas.append({"titulo": "Entregados", "valor": entregados, "icono": "✅"})

    # Notificaciones sin leer (común a todos)
    no_leidas = db.query(func.count(NotifModel.id)).filter(
        NotifModel.usuario_email == email,
        NotifModel.estado == "pending"
    ).scalar() or 0
    metricas.append({"titulo": "Notificaciones", "valor": no_leidas, "icono": "🔔"})

    return metricas