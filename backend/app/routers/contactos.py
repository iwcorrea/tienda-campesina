from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.services.contacto_service import (
    enviar_solicitud_contacto,
    listar_contactos,
    eliminar_contacto,
    obtener_info_contacto,
    listar_solicitudes_pendientes,
    listar_solicitudes_enviadas,
    aceptar_solicitud,
    rechazar_solicitud,
    cancelar_solicitud,
)
from app.modules.notifications.service import crear_notificacion
from app.templates import templates

router = APIRouter(prefix="/contactos", tags=["contactos"])


@router.get("/", response_class=HTMLResponse)
def panel_contactos(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    contactos_orm = listar_contactos(db, current_user["email"])
    contactos = []
    for c in contactos_orm:
        info = obtener_info_contacto(db, c.contacto_email)
        contactos.append({
            "email": c.contacto_email,
            "nombre": info["nombre"] if info else c.contacto_email,
            "tipo": info["tipo"] if info else "desconocido",
            "logo": info.get("logo") if info else None,
            "relacion": c.tipo_relacion
        })

    solicitudes_recibidas = listar_solicitudes_pendientes(db, current_user["email"])
    recibidas_info = []
    for s in solicitudes_recibidas:
        info = obtener_info_contacto(db, s.solicitante_email)
        recibidas_info.append({
            "id": s.id,
            "email": s.solicitante_email,
            "nombre": info["nombre"] if info else s.solicitante_email,
            "tipo": info["tipo"] if info else "desconocido"
        })

    solicitudes_enviadas = listar_solicitudes_enviadas(db, current_user["email"])
    enviadas_info = []
    for s in solicitudes_enviadas:
        info = obtener_info_contacto(db, s.receptor_email)
        enviadas_info.append({
            "id": s.id,
            "email": s.receptor_email,
            "nombre": info["nombre"] if info else s.receptor_email,
            "tipo": info["tipo"] if info else "desconocido"
        })

    return templates.TemplateResponse("contactos.html", {
        "request": request,
        "contactos": contactos,
        "solicitudes_recibidas": recibidas_info,
        "solicitudes_enviadas": enviadas_info,
    })


@router.post("/solicitar")
def solicitar_contacto(
    request: Request,
    contacto_email: str = Form(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    enviar_solicitud_contacto(db, current_user["email"], contacto_email)

    crear_notificacion(
        db,
        destinatario_email=contacto_email,
        remitente_email=current_user["email"],
        texto=f"{current_user['email']} te ha enviado una solicitud de contacto."
    )

    return RedirectResponse(url="/contactos?enviada=1", status_code=303)


@router.post("/aceptar")
def aceptar_solicitud_post(
    request: Request,
    solicitud_id: str = Form(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    aceptar_solicitud(db, solicitud_id, current_user["email"])
    return RedirectResponse(url="/contactos?aceptada=1", status_code=303)


@router.post("/rechazar")
def rechazar_solicitud_post(
    request: Request,
    solicitud_id: str = Form(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    rechazar_solicitud(db, solicitud_id, current_user["email"])
    return RedirectResponse(url="/contactos?rechazada=1", status_code=303)


@router.post("/cancelar")
def cancelar_solicitud_post(
    request: Request,
    solicitud_id: str = Form(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    cancelar_solicitud(db, solicitud_id, current_user["email"])
    return RedirectResponse(url="/contactos?cancelada=1", status_code=303)


@router.post("/eliminar")
def eliminar(
    request: Request,
    contacto_email: str = Form(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    eliminar_contacto(db, current_user["email"], contacto_email)
    return RedirectResponse(url="/contactos?eliminado=1", status_code=303)


@router.get("/historial/{contacto_email}", response_class=HTMLResponse)
def historial_contacto(
    request: Request,
    contacto_email: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    from app.services.historial_service import obtener_historial_con_contacto
    eventos = obtener_historial_con_contacto(db, current_user["email"], contacto_email)
    info = obtener_info_contacto(db, contacto_email)
    contacto_nombre = info["nombre"] if info else contacto_email

    return templates.TemplateResponse("historial_contacto.html", {
        "request": request,
        "eventos": eventos,
        "contacto_email": contacto_email,
        "contacto_nombre": contacto_nombre
    })