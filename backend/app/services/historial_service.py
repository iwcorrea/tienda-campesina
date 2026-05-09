from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.models import Mensaje, Pedido, ItemPedido, RespuestaCotizacion, Valoracion, ValoracionComprador
from app.utils import utc_to_colombia

def obtener_historial_con_contacto(db: Session, email_usuario: str, email_contacto: str) -> List[dict]:
    """
    Devuelve una lista unificada de eventos entre el usuario y el contacto,
    ordenados del más reciente al más antiguo.
    Cada evento tiene: tipo, icono, texto, descripcion, fecha, url.
    """
    eventos = []

    # ─── 1. Mensajes entre ambos ──────────────────────────
    mensajes = (
        db.query(Mensaje)
        .filter(
            or_(
                and_(Mensaje.remitente_email == email_usuario, Mensaje.destinatario_email == email_contacto),
                and_(Mensaje.remitente_email == email_contacto, Mensaje.destinatario_email == email_usuario)
            )
        )
        .order_by(Mensaje.fecha_envio.desc())
        .limit(50)
        .all()
    )
    for m in mensajes:
        eventos.append({
            "tipo": "mensaje",
            "icono": "💬",
            "texto": f"Mensaje de {m.remitente_email}",
            "descripcion": m.texto[:250] + ("..." if len(m.texto) > 250 else ""),
            "fecha": utc_to_colombia(m.fecha_envio) if m.fecha_envio else None,
            "url": f"/mensajes/chat/{email_contacto}#msg-{m.id}"
        })

    # ─── 2. Pedidos donde el contacto es comprador ──────────
    pedidos_comprador = (
        db.query(Pedido)
        .filter(Pedido.comprador_email == email_contacto)
        .order_by(Pedido.fecha_creacion.desc())
        .limit(20)
        .all()
    )
    for p in pedidos_comprador:
        # Verificar que al menos un producto pertenezca al usuario (si es asociación)
        pertenece = False
        productos_nombres = []
        for item in p.items:
            if item.producto:
                productos_nombres.append(item.producto.nombre)
                if item.producto.asociacion_email == email_usuario:
                    pertenece = True
        if pertenece:
            eventos.append({
                "tipo": "pedido",
                "icono": "📦",
                "texto": f"Pedido #{p.id[:8]} de {p.comprador_email}",
                "descripcion": f"Productos: {', '.join(productos_nombres[:3])}. Estado: {p.estado}.",
                "fecha": utc_to_colombia(p.fecha_creacion) if p.fecha_creacion else None,
                "url": f"/pedidos/{p.id}"
            })

    # ─── 3. Respuestas a cotizaciones (aceptadas/rechazadas) ─
    respuestas = (
        db.query(RespuestaCotizacion)
        .join(ItemPedido)
        .join(Pedido)
        .filter(
            or_(
                RespuestaCotizacion.asociacion_email == email_usuario,
                RespuestaCotizacion.asociacion_email == email_contacto
            ),
            or_(
                Pedido.comprador_email == email_usuario,
                Pedido.comprador_email == email_contacto
            )
        )
        .order_by(RespuestaCotizacion.fecha_respuesta.desc())
        .limit(20)
        .all()
    )
    for r in respuestas:
        if r.item_pedido and r.item_pedido.producto:
            producto = r.item_pedido.producto
            pedido = r.item_pedido.pedido
            if pedido and (pedido.comprador_email in (email_usuario, email_contacto)):
                eventos.append({
                    "tipo": "cotizacion",
                    "icono": "🤝" if r.aceptado == "aceptado" else "❌",
                    "texto": f"Cotización {r.aceptado} para '{producto.nombre}'",
                    "descripcion": f"Pedido #{pedido.id[:8]}. {r.mensaje or 'Sin mensaje adicional.'}",
                    "fecha": utc_to_colombia(r.fecha_respuesta) if r.fecha_respuesta else None,
                    "url": f"/pedidos/{pedido.id}"
                })
                # Si hay contrato o factura, lo añado como evento extra
                if r.contrato_url:
                    eventos.append({
                        "tipo": "documento",
                        "icono": "📄",
                        "texto": "Contrato generado",
                        "descripcion": f"Contrato para el pedido #{pedido.id[:8]}",
                        "fecha": utc_to_colombia(r.fecha_respuesta) if r.fecha_respuesta else None,
                        "url": r.contrato_url
                    })
                if r.factura_url:
                    eventos.append({
                        "tipo": "documento",
                        "icono": "🧾",
                        "texto": "Factura generada",
                        "descripcion": f"Factura para el pedido #{pedido.id[:8]}",
                        "fecha": utc_to_colombia(r.fecha_respuesta) if r.fecha_respuesta else None,
                        "url": r.factura_url
                    })

    # ─── 4. Valoraciones mutuas ────────────────────────────
    valoraciones = (
        db.query(Valoracion)
        .filter(Valoracion.email_usuario.in_([email_usuario, email_contacto]))
        .filter(Valoracion.producto_id.isnot(None))
        .order_by(Valoracion.fecha.desc())
        .limit(10)
        .all()
    )
    for v in valoraciones:
        if v.producto and v.producto.asociacion_email in (email_usuario, email_contacto):
            eventos.append({
                "tipo": "valoracion",
                "icono": "⭐",
                "texto": f"Valoración de {v.email_usuario} ({v.estrellas} estrellas)",
                "descripcion": f"Producto: {v.producto.nombre}. {v.comentario or ''}",
                "fecha": utc_to_colombia(v.fecha) if v.fecha else None,
                "url": f"/catalogo?q={v.producto.nombre}"
            })

    valoraciones_comp = (
        db.query(ValoracionComprador)
        .filter(
            ValoracionComprador.comprador_email.in_([email_usuario, email_contacto]),
            ValoracionComprador.asociacion_email.in_([email_usuario, email_contacto])
        )
        .order_by(ValoracionComprador.fecha.desc())
        .limit(10)
        .all()
    )
    for vc in valoraciones_comp:
        eventos.append({
            "tipo": "valoracion",
            "icono": "⭐",
            "texto": f"Valoración como comprador ({vc.estrellas} estrellas)",
            "descripcion": f"De {vc.asociacion_email}. {vc.comentario or ''}",
            "fecha": utc_to_colombia(vc.fecha) if vc.fecha else None,
            "url": f"/pedidos/{vc.pedido_id}"
        })

    # Ordenar todos los eventos por fecha descendente
    eventos.sort(key=lambda x: x["fecha"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return eventos[:50]