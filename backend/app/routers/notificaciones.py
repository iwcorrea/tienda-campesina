from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.models import Mensaje
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

    mensajes = (
        db.query(Mensaje)
        .filter(Mensaje.destinatario_email == current_user["email"])
        .order_by(desc(Mensaje.fecha_envio))
        .limit(10)
        .all()
    )

    notificaciones = []
    for m in mensajes:
        notificaciones.append({
            "id": m.id,
            "texto": m.texto[:80] + ("..." if len(m.texto) > 80 else ""),
            "fecha": m.fecha_envio.strftime("%d/%m %H:%M") if m.fecha_envio else "",
            "url": f"/mensajes/{m.id}"
        })

    return {"notificaciones": notificaciones}