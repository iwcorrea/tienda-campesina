from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.modules.chat.service import (
    obtener_rooms_usuario,
    obtener_mensajes_room,
    enviar_mensaje,
)
from app.templates import templates

router = APIRouter(prefix="/chat", tags=["chat"])

@router.get("/", response_class=HTMLResponse)
def listar_rooms(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)
    rooms = obtener_rooms_usuario(db, current_user["email"])
    return templates.TemplateResponse("chat/rooms.html", {
        "request": request,
        "rooms": rooms,
    })

@router.get("/room/{room_id}", response_class=HTMLResponse)
def ver_room(
    request: Request,
    room_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)
    mensajes = obtener_mensajes_room(db, room_id)
    return templates.TemplateResponse("chat/room.html", {
        "request": request,
        "room_id": room_id,
        "mensajes": mensajes,
    })

@router.post("/room/{room_id}/enviar")
def enviar(
    request: Request,
    room_id: str,
    contenido: str = Form(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)
    enviar_mensaje(db, room_id, current_user["email"], contenido)
    return RedirectResponse(url=f"/chat/room/{room_id}", status_code=303)