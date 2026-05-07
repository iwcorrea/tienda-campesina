from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.services.mensaje_service import (
    obtener_bandeja_entrada,
    obtener_bandeja_salida,
    obtener_mensaje_por_id,
    marcar_como_leido,
    obtener_hilo,
    responder_mensaje,
    enviar_mensaje_nuevo,
    contar_no_leidos,
)
from app.viewmodels.mensaje import MensajeViewModel
from app.templates import templates

router = APIRouter()


@router.get("/mensajes", response_class=HTMLResponse)
def bandeja_entrada(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    email = current_user["email"]
    mensajes_orm = obtener_bandeja_entrada(db, email)
    mensajes_vm = [MensajeViewModel.from_orm(m) for m in mensajes_orm]
    return templates.TemplateResponse("mensajes.html", {
        "request": request,
        "mensajes": mensajes_vm,
        "tipo_bandeja": "entrada",
    })


@router.get("/mensajes/enviados", response_class=HTMLResponse)
def bandeja_salida(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    email = current_user["email"]
    mensajes_orm = obtener_bandeja_salida(db, email)
    mensajes_vm = [MensajeViewModel.from_orm(m) for m in mensajes_orm]
    return templates.TemplateResponse("mensajes.html", {
        "request": request,
        "mensajes": mensajes_vm,
        "tipo_bandeja": "salida",
    })


@router.get("/mensajes/{mensaje_id}", response_class=HTMLResponse)
def ver_mensaje(
    request: Request,
    mensaje_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    email = current_user["email"]
    mensaje = obtener_mensaje_por_id(db, mensaje_id, email)
    if not mensaje:
        return RedirectResponse(url="/mensajes", status_code=303)

    marcar_como_leido(db, mensaje, email)
    hilo = obtener_hilo(db, mensaje)
    hilo_vm = [MensajeViewModel.from_orm(m) for m in hilo]
    return templates.TemplateResponse("mensaje_detalle.html", {
        "request": request,
        "mensaje": MensajeViewModel.from_orm(mensaje),
        "hilo": hilo_vm,
    })


@router.post("/mensajes/responder/{mensaje_id}")
def responder(
    request: Request,
    mensaje_id: str,
    texto: str = Form(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    email = current_user["email"]
    original = obtener_mensaje_por_id(db, mensaje_id, email)
    if not original:
        return RedirectResponse(url="/mensajes", status_code=303)

    responder_mensaje(db, original, email, texto)
    return RedirectResponse(url=f"/mensajes/{mensaje_id}", status_code=303)


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

    enviar_mensaje_nuevo(db, current_user["email"], destinatario_email, texto, producto_id)
    return RedirectResponse(url="/catalogo", status_code=303)


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