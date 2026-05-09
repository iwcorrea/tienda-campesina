from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.services.mensaje_service import (
    obtener_conversaciones,
    obtener_hilo_con_contacto,
    marcar_conversacion_leida,
    enviar_mensaje,
    eliminar_mensaje,
    eliminar_conversacion,
    bloquear_usuario,
    desbloquear_usuario,
    esta_bloqueado,
    contar_no_leidos,
    obtener_nombre_usuario,
)
from app.services.contacto_service import listar_contactos, obtener_info_contacto
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
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    # Obtener contactos del usuario para el selector
    contactos = []
    contactos_orm = listar_contactos(db, current_user["email"])
    for c in contactos_orm:
        info = obtener_info_contacto(db, c.contacto_email)
        contactos.append({
            "email": c.contacto_email,
            "nombre": info["nombre"] if info else c.contacto_email,
            "tipo": info["tipo"] if info else "desconocido"
        })

    return templates.TemplateResponse("mensaje_nuevo.html", {
        "request": request,
        "destinatario_email": destinatario_email,
        "contactos": contactos,
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
    if esta_bloqueado(db, current_user["email"], destinatario_email):
        return RedirectResponse(url="/mensajes?bloqueado=1", status_code=303)
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
    bloqueado = esta_bloqueado(db, email, contacto_email)
    return templates.TemplateResponse("mensaje_detalle.html", {
        "request": request,
        "hilo": hilo_vm,
        "contacto_email": contacto_email,
        "contacto_nombre": contacto_nombre,
        "bloqueado": bloqueado,
    })

@router.post("/mensajes/eliminar/{mensaje_id}")
def eliminar_mensaje_post(
    request: Request,
    mensaje_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)
    eliminar_mensaje(db, mensaje_id, current_user["email"])
    return RedirectResponse(url=request.headers.get("referer", "/mensajes"), status_code=303)

@router.post("/mensajes/eliminar-conversacion/{contacto_email}")
def eliminar_conversacion_post(
    request: Request,
    contacto_email: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)
    eliminar_conversacion(db, current_user["email"], contacto_email)
    return RedirectResponse(url="/mensajes", status_code=303)

@router.post("/mensajes/bloquear/{contacto_email}")
def bloquear(
    request: Request,
    contacto_email: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)
    bloquear_usuario(db, current_user["email"], contacto_email)
    return RedirectResponse(url=f"/mensajes/chat/{contacto_email}", status_code=303)

@router.post("/mensajes/desbloquear/{contacto_email}")
def desbloquear(
    request: Request,
    contacto_email: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)
    desbloquear_usuario(db, current_user["email"], contacto_email)
    return RedirectResponse(url=f"/mensajes/chat/{contacto_email}", status_code=303)

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