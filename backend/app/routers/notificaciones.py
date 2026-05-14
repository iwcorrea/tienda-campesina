from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.modules.notifications.service import listar_notificaciones_usuario
from app.services.mensaje_service import contar_no_leidos, obtener_conversaciones

router = APIRouter()

@router.get("/api/notificaciones")
def listar_notificaciones(request: Request, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if not current_user:
        return {"notificaciones": []}

    notificaciones = []
    email = current_user["email"]

    # Mensajes no leídos (comunicación personal)
    mensajes_count = contar_no_leidos(db, email)
    if mensajes_count > 0:
        notificaciones.append({
            "tipo": "mensaje",
            "icono": "💬",
            "texto": f"Tienes {mensajes_count} mensaje(s) nuevo(s)",
            "fecha": "",
            "url": "/mensajes"
        })

    # Notificaciones del sistema (nuevo módulo)
    sistema = listar_notificaciones_usuario(db, email, limite=15)
    for n in sistema:
        notificaciones.append({
            "tipo": "sistema",
            "icono": "📢",
            "texto": n.titulo,
            "fecha": n.fecha_creacion.strftime("%d/%m %H:%M") if n.fecha_creacion else "",
            "url": f"/pedidos/{n.referencia_pedido_id}" if n.referencia_pedido_id else "#"
        })

    return {"notificaciones": notificaciones}