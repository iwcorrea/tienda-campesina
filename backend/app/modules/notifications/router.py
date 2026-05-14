from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from app.dependencies import get_current_user
from app.modules.notifications.service import listar_notificaciones_usuario, marcar_leida
from app.modules.notifications.dependencies import get_db

router = APIRouter(prefix="/notificaciones", tags=["notificaciones"])

@router.get("/", response_class=JSONResponse)
def obtener_notificaciones(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user:
        return JSONResponse([])
    notifs = listar_notificaciones_usuario(db, current_user["email"])
    return JSONResponse([
        {
            "id": n.id,
            "tipo_evento": n.tipo_evento,
            "titulo": n.titulo,
            "contenido": n.contenido,
            "estado": n.estado,
            "fecha": n.fecha_creacion.strftime("%d/%m/%Y %H:%M") if n.fecha_creacion else "",
            "url": f"/pedidos/{n.referencia_pedido_id}" if n.referencia_pedido_id else "#"
        } for n in notifs
    ])

@router.post("/{notificacion_id}/leer")
def marcar_leida_endpoint(
    request: Request,
    notificacion_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)
    marcar_leida(db, notificacion_id, current_user["email"])
    return RedirectResponse(url="/notificaciones", status_code=303)