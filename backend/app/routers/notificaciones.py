from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.models import Mensaje, Pedido
from sqlalchemy import desc
from app.utils import utc_to_colombia

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

    mensajes = (
        db.query(Mensaje)
        .filter(Mensaje.destinatario_email == email, Mensaje.leido == "0")
        .order_by(desc(Mensaje.fecha_envio))
        .limit(5)
        .all()
    )
    for m in mensajes:
        fecha = utc_to_colombia(m.fecha_envio)
        notificaciones.append({
            "tipo": "mensaje",
            "icono": "💬",
            "texto": f"Mensaje de {m.remitente_email}: {m.texto[:60]}{'...' if len(m.texto)>60 else ''}",
            "fecha": fecha.strftime("%d/%m %H:%M") if fecha else "",
            "url": f"/mensajes/{m.id}"
        })

    pedidos_aceptados = (
        db.query(Pedido)
        .filter(Pedido.comprador_email == email, Pedido.estado == "aceptado")
        .order_by(desc(Pedido.fecha_creacion))
        .limit(5)
        .all()
    )
    for p in pedidos_aceptados:
        fecha = utc_to_colombia(p.fecha_creacion)
        notificaciones.append({
            "tipo": "pedido_aceptado",
            "icono": "🤝",
            "texto": f"Tu pedido #{p.id[:8]} fue aceptado",
            "fecha": fecha.strftime("%d/%m %H:%M") if fecha else "",
            "url": f"/pedidos/{p.id}"
        })

    notificaciones.sort(key=lambda x: x["fecha"], reverse=True)
    notificaciones = notificaciones[:15]

    return {"notificaciones": notificaciones}