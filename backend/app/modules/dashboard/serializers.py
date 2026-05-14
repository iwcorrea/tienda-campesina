from datetime import datetime
from app.utils import utc_to_colombia

def serializar_pedido(pedido) -> dict:
    items_nombres = [item.producto.nombre for item in pedido.items if item.producto]
    return {
        "id": pedido.id,
        "estado": pedido.estado,
        "comprador_email": pedido.comprador_email,
        "total": sum(item.cantidad * item.precio_unitario_inicial for item in pedido.items),
        "fecha": utc_to_colombia(pedido.fecha_creacion).strftime("%d/%m/%Y %H:%M") if pedido.fecha_creacion else "",
        "items": items_nombres,
    }

def serializar_documento(doc) -> dict:
    return {
        "tipo": doc.tipo,
        "url": doc.storage_url,
        "fecha": utc_to_colombia(doc.fecha_generacion).strftime("%d/%m/%Y") if doc.fecha_generacion else "",
    }

def serializar_evento(evento) -> dict:
    iconos = {
        "order_created": "📝",
        "order_confirmed": "🤝",
        "transport_assigned": "🚚",
        "in_transit": "🔄",
        "delivered": "📦",
        "payment_confirmed": "💰",
        "document_generated": "📄",
    }
    return {
        "tipo": evento.tipo,
        "descripcion": evento.descripcion or evento.tipo,
        "fecha": utc_to_colombia(evento.fecha).strftime("%d/%m/%Y %H:%M") if evento.fecha else "",
        "icono": iconos.get(evento.tipo, "🔔"),
    }