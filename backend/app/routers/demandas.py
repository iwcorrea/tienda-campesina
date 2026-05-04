import uuid
from fastapi import APIRouter, Request, Form, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Demanda, Mensaje, Asociacion
import datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# ─── TABLÓN PÚBLICO ──────────────────────────────────
@router.get("/demandas", response_class=HTMLResponse)
def listar_demandas(request: Request, db: Session = Depends(get_db)):
    demandas = db.query(Demanda).filter(Demanda.activo == "1").order_by(Demanda.fecha_publicacion.desc()).all()
    return templates.TemplateResponse("demandas.html", {
        "request": request,
        "demandas": demandas
    })

# ─── FORMULARIO PARA PUBLICAR (solo registrados) ────
@router.get("/demandas/nueva", response_class=HTMLResponse)
def publicar_demanda_get(request: Request):
    if not request.session.get("usuario"):
        return RedirectResponse(url="/auth/login", status_code=303)
    return templates.TemplateResponse("publicar_demanda.html", {"request": request})

@router.post("/demandas/nueva")
def publicar_demanda_post(
    request: Request,
    titulo: str = Form(...),
    descripcion: str = Form(""),
    cantidad: str = Form(""),
    unidad: str = Form(""),
    precio_referencia: int = Form(0),
    db: Session = Depends(get_db)
):
    if not request.session.get("usuario"):
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    tipo = request.session.get("tipo_usuario", "persona")
    nueva = Demanda(
        id=str(uuid.uuid4()),
        titulo=titulo,
        descripcion=descripcion,
        cantidad=cantidad,
        unidad=unidad,
        precio_referencia=precio_referencia,
        email_creador=email,
        tipo_creador=tipo
    )
    db.add(nueva)
    db.commit()
    return RedirectResponse(url="/demandas", status_code=303)

# ─── VER DETALLE DE DEMANDA ─────────────────────────
@router.get("/demandas/{demanda_id}", response_class=HTMLResponse)
def ver_demanda(request: Request, demanda_id: str, db: Session = Depends(get_db)):
    demanda = db.query(Demanda).filter(Demanda.id == demanda_id, Demanda.activo == "1").first()
    if not demanda:
        return RedirectResponse(url="/demandas", status_code=303)

    # Si es una asociación, buscar el nombre, sino mostrar el email
    creador_nombre = ""
    if demanda.tipo_creador == "asociacion":
        asoc = db.query(Asociacion).filter(Asociacion.email == demanda.email_creador).first()
        if asoc:
            creador_nombre = asoc.nombre
    else:
        creador_nombre = demanda.email_creador

    return templates.TemplateResponse("demanda_detalle.html", {
        "request": request,
        "demanda": demanda,
        "creador_nombre": creador_nombre
    })

# ─── RESPONDER A DEMANDA (solo asociaciones) ────────
@router.post("/demandas/{demanda_id}/responder")
def responder_demanda(
    request: Request,
    demanda_id: str,
    mensaje: str = Form(...),
    db: Session = Depends(get_db)
):
    if request.session.get("tipo_usuario") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    demanda = db.query(Demanda).filter(Demanda.id == demanda_id, Demanda.activo == "1").first()
    if not demanda:
        return RedirectResponse(url="/demandas", status_code=303)

    # Enviar mensaje interno al creador de la demanda
    nuevo_msg = Mensaje(
        id=str(uuid.uuid4()),
        remitente_email=email,
        destinatario_email=demanda.email_creador,
        texto=f"Respuesta a tu demanda '{demanda.titulo}':\n{mensaje}",
        leido="0"
    )
    db.add(nuevo_msg)
    db.commit()
    return RedirectResponse(url="/mensajes", status_code=303)