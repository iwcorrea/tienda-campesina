from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.models import Mensaje
from app.services.actividad_service import obtener_actividades_recientes
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

    # 1. Mensajes no leídos (bandeja de entrada)
    mensajes = (
        db.query(Mensaje)
        .filter(Mensaje.destinatario_email == current_user["email"], Mensaje.leido == "0")
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

    # 2. Actividades recientes del feed (últimas 10, para mostrar en notificaciones)
    actividades = obtener_actividades_recientes(db, limite=10)
    for act in actividades:
        notificaciones.append({
            "tipo": act["tipo"],
            "icono": act["icono"],
            "texto": act["texto"],
            "fecha": act["fecha"].strftime("%d/%m %H:%M") if act["fecha"] else "",
            "url": act["url"]
        })

    # Ordenar por fecha descendente (mezclado)
    from datetime import datetime
    notificaciones.sort(key=lambda x: datetime.strptime(x["fecha"], "%d/%m %H:%M") if x["fecha"] else datetime.min, reverse=True)
    notificaciones = notificaciones[:15]

    return {"notificaciones": notificaciones}