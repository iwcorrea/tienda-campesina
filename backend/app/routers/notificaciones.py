from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.models import Mensaje, NotificacionSistema
from sqlalchemy import desc

router = APIRouter()

@router.get("/api/notificaciones")
def listar_notificaciones(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user:
        return {"notificaciones": []}

    notificaciones = []
    email = current_user["email"]

    # 1. Mensajes no leídos (comunicación personal)
    mensajes = (
        db.query(Mensaje)
        .filter(Mensaje.destinatario_email == email, Mensaje.leido == "0")
        .order_by(desc(Mensaje.fecha_envio))
        .limit(5)
        .all()
    )
    for m in mensajes:
        notificaciones.append({
            "tipo": "mensaje",
            "icono": "💬",
            "texto": f"Mensaje de {m.remitente_email}: {m.texto[:60]}{'...' if len(m.texto)>60 else ''}",
            "fecha": m.fecha_envio.strftime("%d/%m %H:%M") if m.fecha_envio else "",
            "url": f"/mensajes/{m.id}"
        })

    # 2. Notificaciones del sistema (pedidos, cotizaciones, contratos)
    sistema = (
        db.query(NotificacionSistema)
        .filter(NotificacionSistema.destinatario_email == email, NotificacionSistema.leido == "0")
        .order_by(desc(NotificacionSistema.fecha_creacion))
        .limit(10)
        .all()
    )
    for n in sistema:
        notificaciones.append({
            "tipo": "sistema",
            "icono": "📢",
            "texto": n.texto[:80] + ("..." if len(n.texto) > 80 else ""),
            "fecha": n.fecha_creacion.strftime("%d/%m %H:%M") if n.fecha_creacion else "",
            "url": n.url or "#"
        })

    notificaciones.sort(key=lambda x: x["fecha"], reverse=True)
    notificaciones = notificaciones[:15]

    return {"notificaciones": notificaciones}