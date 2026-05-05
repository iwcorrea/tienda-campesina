import logging
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.database import get_db
from app.models import Asociacion, Producto, Valoracion, Mensaje, Vacante, ItemPedido, RespuestaCotizacion, TransportistaFavorito

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger("dashboard")

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    if "usuario" not in request.session or request.session.get("tipo_usuario") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)

    email = request.session["usuario"]
    asociacion = db.query(Asociacion).filter(Asociacion.email == email).first()
    if not asociacion:
        return RedirectResponse(url="/auth/login", status_code=303)

    mis_productos = asociacion.productos
    total_productos = len(mis_productos)
    # Valoraciones
    total_valoraciones = db.query(func.count(Valoracion.id)).filter(Valoracion.producto_id.in_([p.id for p in mis_productos])).scalar()
    # Mensajes sin leer
    mensajes_pendientes = db.query(func.count(Mensaje.id)).filter(
        Mensaje.destinatario_email == email,
        Mensaje.leido == "0"
    ).scalar()
    # Cotizaciones pendientes (items de mis productos sin respuesta aceptada/rechazada)
    cotizaciones_pendientes = db.query(func.count(ItemPedido.id)).join(Producto).filter(
        Producto.asociacion_email == email
    ).filter(~ItemPedido.respuestas.any(RespuestaCotizacion.aceptado.in_(["aceptado", "rechazado"]))).scalar()
    # Vacantes activas
    vacantes_activas = db.query(func.count(Vacante.id)).filter(
        Vacante.asociacion_email == email,
        Vacante.fecha_limite >= func.now()
    ).scalar()
    # Transportistas favoritos
    favoritos_count = db.query(func.count(TransportistaFavorito.id)).filter(
        TransportistaFavorito.asociacion_email == email
    ).scalar()

    # Actividades recientes (últimos 5 eventos combinados)
    actividades = []

    # Mensajes recibidos recientes
    mensajes_recibidos = db.query(Mensaje).filter(Mensaje.destinatario_email == email).order_by(desc(Mensaje.fecha_envio)).limit(3).all()
    for m in mensajes_recibidos:
        actividades.append({
            "icono": "📨",
            "texto": f"Mensaje de {m.remitente.nombre or m.remitente_email}: {m.texto[:60]}{'...' if len(m.texto)>60 else ''}",
            "fecha": m.fecha_envio,
            "url": f"/mensajes/{m.id}"
        })

    # Respuestas a mis cotizaciones (actuando como comprador? no, las cotizaciones son pedidos de otros. Pero podemos mostrar respuestas que he recibido en mis productos)
    # Mejor mostrar cuando alguien responde a una cotización de mis productos.
    respuestas = db.query(RespuestaCotizacion).join(ItemPedido).join(Producto).filter(
        Producto.asociacion_email == email
    ).order_by(desc(RespuestaCotizacion.fecha_respuesta)).limit(3).all()
    for r in respuestas:
        estado = r.aceptado.capitalize()
        actividades.append({
            "icono": "📦",
            "texto": f"Respuesta a cotización de {r.item_pedido.producto.nombre} ({estado})",
            "fecha": r.fecha_respuesta,
            "url": "/panel/cotizaciones"
        })

    # Últimas valoraciones recibidas
    vals = db.query(Valoracion).filter(Valoracion.producto_id.in_([p.id for p in mis_productos])).order_by(desc(Valoracion.fecha)).limit(3).all()
    for v in vals:
        actividades.append({
            "icono": "⭐",
            "texto": f"Valoración de {v.producto.nombre} ({v.estrellas} estrellas)",
            "fecha": v.fecha,
            "url": "/dashboard#valoraciones"
        })

    # Ordenar todas las actividades por fecha descendente y tomar las 5 primeras
    actividades.sort(key=lambda x: x["fecha"], reverse=True)
    actividades = actividades[:5]

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "usuario": asociacion.nombre,
        "total_productos": total_productos,
        "total_valoraciones": total_valoraciones,
        "mensajes_pendientes": mensajes_pendientes,
        "cotizaciones_pendientes": cotizaciones_pendientes,
        "vacantes_activas": vacantes_activas,
        "favoritos_count": favoritos_count,
        "actividades": actividades
    })