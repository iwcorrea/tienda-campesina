from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.services.mensaje_service import (
    obtener_conversaciones,
    obtener_hilo_con_contacto,
    marcar_conversacion_leida,
    enviar_mensaje,
    contar_no_leidos,
    obtener_nombre_usuario,
)
from app.viewmodels.mensaje import MensajeChatViewModel
from app.templates import templates

router = APIRouter()

@router.get("/mensajes", response_class=HTMLResponse)
def bandeja_principal(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    conversaciones = obtener_conversaciones(db, current_user["email"])
    return templates.TemplateResponse("mensajes.html", {
        "request": request,
        "conversaciones": conversaciones,
    })

@router.get("/mensajes/nuevo", response_class=HTMLResponse)
def nuevo_mensaje(
    request: Request,
    destinatario_email: str = "",
    current_user: dict = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    return templates.TemplateResponse("mensaje_nuevo.html", {
        "request": request,
        "destinatario_email": destinatario_email,
    })

@router.post("/mensajes/enviar")
def enviar(
    request: Request,
    texto: str = Form(...),
    destinatario_email: str = Form(...),
    producto_id: str = Form(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    enviar_mensaje(db, current_user["email"], destinatario_email, texto, producto_id)
    return RedirectResponse(url=f"/mensajes/chat/{destinatario_email}", status_code=303)

@router.get("/mensajes/chat/{contacto_email}", response_class=HTMLResponse)
def ver_chat(
    request: Request,
    contacto_email: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    email = current_user["email"]
    marcar_conversacion_leida(db, email, contacto_email)

    hilo = obtener_hilo_con_contacto(db, email, contacto_email)
    hilo_vm = []
    for m in hilo:
        vm = MensajeChatViewModel.from_orm(m)
        vm.remitente_nombre = obtener_nombre_usuario(db, m.remitente_email)
        vm.destinatario_nombre = obtener_nombre_usuario(db, m.destinatario_email)
        hilo_vm.append(vm)

    contacto_nombre = obtener_nombre_usuario(db, contacto_email)

    return templates.TemplateResponse("mensaje_detalle.html", {
        "request": request,
        "hilo": hilo_vm,
        "contacto_email": contacto_email,
        "contacto_nombre": contacto_nombre,
    })

@router.get("/api/mensajes/no-leidos")
def no_leidos(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user:
        return {"count": 0}
    count = contar_no_leidos(db, current_user["email"])
    return {"count": count}