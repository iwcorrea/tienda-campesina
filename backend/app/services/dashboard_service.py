from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.models import Asociacion, Producto, Valoracion, Mensaje, Vacante, ItemPedido, RespuestaCotizacion, TransportistaFavorito


def obtener_totales_dashboard(db: Session, email: str) -> dict:
    asociacion = db.query(Asociacion).filter(Asociacion.email == email).first()
    if not asociacion:
        return None

    productos_ids = [p.id for p in asociacion.productos]
    total_productos = len(productos_ids)

    total_valoraciones = db.query(func.count(Valoracion.id)).filter(
        Valoracion.producto_id.in_(productos_ids)
    ).scalar()

    mensajes_pendientes = db.query(func.count(Mensaje.id)).filter(
        Mensaje.destinatario_email == email,
        Mensaje.leido == "0"
    ).scalar()

    cotizaciones_pendientes = db.query(func.count(ItemPedido.id)).join(Producto).filter(
        Producto.asociacion_email == email
    ).filter(
        ~ItemPedido.respuestas.any(RespuestaCotizacion.aceptado.in_(["aceptado", "rechazado"]))
    ).scalar()

    vacantes_activas = db.query(func.count(Vacante.id)).filter(
        Vacante.asociacion_email == email,
        Vacante.fecha_limite >= func.now()
    ).scalar()

    favoritos_count = db.query(func.count(TransportistaFavorito.id)).filter(
        TransportistaFavorito.asociacion_email == email
    ).scalar()

    return {
        "asociacion": asociacion,
        "total_productos": total_productos,
        "total_valoraciones": total_valoraciones or 0,
        "mensajes_pendientes": mensajes_pendientes or 0,
        "cotizaciones_pendientes": cotizaciones_pendientes or 0,
        "vacantes_activas": vacantes_activas or 0,
        "favoritos_count": favoritos_count or 0,
    }


def obtener_actividades_recientes(db: Session, email: str, productos_ids: list, limit: int = 5):
    actividades = []

    mensajes = db.query(Mensaje).filter(Mensaje.destinatario_email == email).order_by(desc(Mensaje.fecha_envio)).limit(3).all()
    for m in mensajes:
        actividades.append({
            "icono": "📨",
            "texto": f"Mensaje de {m.remitente.nombre or m.remitente_email}: {m.texto[:60]}{'...' if len(m.texto)>60 else ''}",
            "fecha": m.fecha_envio,
            "url": f"/mensajes/{m.id}"
        })

    respuestas = db.query(RespuestaCotizacion).join(ItemPedido).join(Producto).filter(
        Producto.asociacion_email == email
    ).order_by(desc(RespuestaCotizacion.fecha_respuesta)).limit(3).all()
    for r in respuestas:
        actividades.append({
            "icono": "📦",
            "texto": f"Respuesta a cotización de {r.item_pedido.producto.nombre} ({r.aceptado})",
            "fecha": r.fecha_respuesta,
            "url": "/panel/cotizaciones"
        })

    if productos_ids:
        vals = db.query(Valoracion).filter(Valoracion.producto_id.in_(productos_ids)).order_by(desc(Valoracion.fecha)).limit(3).all()
        for v in vals:
            actividades.append({
                "icono": "⭐",
                "texto": f"Valoración de {v.producto.nombre} ({v.estrellas} estrellas)",
                "fecha": v.fecha,
                "url": "/dashboard#valoraciones"
            })

    actividades.sort(key=lambda x: x["fecha"] if x["fecha"] else datetime.min, reverse=True)
    return actividades[:limit]