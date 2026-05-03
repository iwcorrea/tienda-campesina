from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Mensaje
import uuid

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/mensajes", response_class=HTMLResponse)
def bandeja_entrada(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("usuario"):
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    mensajes = db.query(Mensaje).filter(
        Mensaje.destinatario_email == email
    ).order_by(Mensaje.fecha_envio.desc()).all()
    return templates.TemplateResponse("mensajes.html", {
        "request": request,
        "mensajes": mensajes,
        "tipo_bandeja": "entrada"
    })

@router.get("/mensajes/enviados", response_class=HTMLResponse)
def bandeja_salida(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("usuario"):
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    mensajes = db.query(Mensaje).filter(
        Mensaje.remitente_email == email
    ).order_by(Mensaje.fecha_envio.desc()).all()
    return templates.TemplateResponse("mensajes.html", {
        "request": request,
        "mensajes": mensajes,
        "tipo_bandeja": "salida"
    })

@router.get("/mensajes/{mensaje_id}", response_class=HTMLResponse)
def ver_mensaje(request: Request, mensaje_id: str, db: Session = Depends(get_db)):
    if not request.session.get("usuario"):
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    mensaje = db.query(Mensaje).filter(
        Mensaje.id == mensaje_id,
        (Mensaje.destinatario_email == email) | (Mensaje.remitente_email == email)
    ).first()
    if not mensaje:
        return RedirectResponse(url="/mensajes", status_code=303)

    if mensaje.destinatario_email == email and mensaje.leido == "0":
        mensaje.leido = "1"
        db.commit()

    hilo = [mensaje]
    respuestas = db.query(Mensaje).filter(
        Mensaje.mensaje_padre_id == mensaje.id
    ).order_by(Mensaje.fecha_envio.asc()).all()
    hilo.extend(respuestas)

    return templates.TemplateResponse("mensaje_detalle.html", {
        "request": request,
        "mensaje": mensaje,
        "hilo": hilo
    })

@router.post("/mensajes/responder/{mensaje_id}")
def responder_mensaje(
    request: Request,
    mensaje_id: str,
    texto: str = Form(...),
    db: Session = Depends(get_db)
):
    if not request.session.get("usuario"):
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    original = db.query(Mensaje).filter(Mensaje.id == mensaje_id).first()
    if not original:
        return RedirectResponse(url="/mensajes", status_code=303)

    destinatario = original.remitente_email if original.remitente_email != email else original.destinatario_email
    nueva = Mensaje(
        id=str(uuid.uuid4()),
        remitente_email=email,
        destinatario_email=destinatario,
        producto_id=original.producto_id,
        texto=texto,
        leido="0",
        mensaje_padre_id=original.id
    )
    db.add(nueva)
    db.commit()
    return RedirectResponse(url=f"/mensajes/{mensaje_id}", status_code=303)

@router.post("/mensajes/enviar")
def enviar_mensaje(
    request: Request,
    texto: str = Form(...),
    destinatario_email: str = Form(...),
    producto_id: str = Form(None),
    db: Session = Depends(get_db)
):
    if not request.session.get("usuario"):
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    nuevo = Mensaje(
        id=str(uuid.uuid4()),
        remitente_email=email,
        destinatario_email=destinatario_email,
        producto_id=producto_id or None,
        texto=texto,
        leido="0"
    )
    db.add(nuevo)
    db.commit()
    return RedirectResponse(url="/catalogo", status_code=303)