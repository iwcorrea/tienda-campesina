from fastapi import APIRouter, Request, Form, File, UploadFile, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.database import get_db
from app.models import Persona, Aplicacion, Mensaje, Pedido, Valoracion
import cloudinary.uploader

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/perfil", response_class=HTMLResponse)
def perfil_persona(request: Request, db: Session = Depends(get_db)):
    if request.session.get("tipo_usuario") != "persona":
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    persona = db.query(Persona).filter(Persona.email == email).first()
    if not persona:
        return RedirectResponse(url="/auth/login", status_code=303)

    # Aplicaciones
    aplicaciones = db.query(Aplicacion).filter(Aplicacion.persona_email == email).all()
    apps_info = []
    for a in aplicaciones:
        vacante = a.vacante
        apps_info.append({
            "cargo": vacante.cargo if vacante else "Cargo desconocido",
            "asociacion": vacante.asociacion.nombre if vacante and vacante.asociacion else "",
            "fecha": a.fecha_aplicacion.strftime("%d/%m/%Y") if a.fecha_aplicacion else ""
        })

    # Mensajes sin leer
    mensajes_pendientes = db.query(func.count(Mensaje.id)).filter(
        Mensaje.destinatario_email == email,
        Mensaje.leido == "0"
    ).scalar()

    # Pedidos realizados
    pedidos_count = db.query(func.count(Pedido.id)).filter(Pedido.comprador_email == email).scalar()

    # Valoraciones emitidas
    valoraciones_count = db.query(func.count(Valoracion.id)).filter(Valoracion.email_usuario == email).scalar()

    # Actividad reciente
    actividades = []

    # Respuestas a mis pedidos
    # Buscar respuestas a items de pedidos del usuario
    respuestas = db.query(RespuestaCotizacion).join(ItemPedido).join(Pedido).filter(
        Pedido.comprador_email == email
    ).order_by(desc(RespuestaCotizacion.fecha_respuesta)).limit(3).all()
    for r in respuestas:
        actividades.append({
            "icono": "📦",
            "texto": f"Respuesta a tu solicitud de {r.item_pedido.producto.nombre} ({r.aceptado})",
            "fecha": r.fecha_respuesta,
            "url": f"/mis-pedidos/{r.item_pedido.pedido_id}"
        })

    # Mensajes recibidos
    mensajes_recibidos = db.query(Mensaje).filter(Mensaje.destinatario_email == email).order_by(desc(Mensaje.fecha_envio)).limit(3).all()
    for m in mensajes_recibidos:
        actividades.append({
            "icono": "📨",
            "texto": f"Mensaje de {m.remitente.nombre or m.remitente_email}: {m.texto[:60]}",
            "fecha": m.fecha_envio,
            "url": f"/mensajes/{m.id}"
        })

    actividades.sort(key=lambda x: x["fecha"] or None, reverse=True)
    actividades = actividades[:5]

    return templates.TemplateResponse("perfil_persona.html", {
        "request": request,
        "persona": persona,
        "aplicaciones": apps_info,
        "mensajes_pendientes": mensajes_pendientes,
        "pedidos_count": pedidos_count,
        "valoraciones_count": valoraciones_count,
        "actividades": actividades
    })

@router.post("/perfil/actualizar")
def actualizar_perfil_persona(
    request: Request,
    nombre: str = Form(...),
    telefono: str = Form(None),
    hoja_vida: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    if request.session.get("tipo_usuario") != "persona":
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    persona = db.query(Persona).filter(Persona.email == email).first()
    if not persona:
        return RedirectResponse(url="/auth/login", status_code=303)

    if hoja_vida and hoja_vida.filename:
        if persona.hoja_vida_url:
            from app.main import delete_cloudinary_asset
            delete_cloudinary_asset(persona.hoja_vida_url, resource_type="raw")
        try:
            result = cloudinary.uploader.upload(
                hoja_vida.file,
                folder="hojas_vida",
                resource_type="raw",
                filename=hoja_vida.filename,
                use_filename=True,
                unique_filename=True,
                access_mode="public"
            )
            persona.hoja_vida_url = result.get("secure_url", "")
        except Exception:
            pass

    persona.nombre = nombre
    persona.telefono = telefono or ""
    db.commit()
    request.session["nombre_usuario"] = persona.nombre
    return RedirectResponse(url="/perfil", status_code=303)