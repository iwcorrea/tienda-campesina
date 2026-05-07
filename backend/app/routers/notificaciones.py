from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.models import Mensaje, Pedido
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

    # 1. Mensajes no leídos
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

    # 2. Pedidos aceptados del usuario
    pedidos_aceptados = (
        db.query(Pedido)
        .filter(Pedido.comprador_email == email, Pedido.estado == "aceptado")
        .order_by(desc(Pedido.fecha_creacion))
        .limit(5)
        .all()
    )
    for p in pedidos_aceptados:
        notificaciones.append({
            "tipo": "pedido_aceptado",
            "icono": "🤝",
            "texto": f"Tu pedido #{p.id[:8]} fue aceptado",
            "fecha": p.fecha_creacion.strftime("%d/%m %H:%M") if p.fecha_creacion else "",
            "url": f"/pedidos/{p.id}"
        })

    notificaciones.sort(key=lambda x: x["fecha"], reverse=True)
    notificaciones = notificaciones[:15]

    return {"notificaciones": notificaciones}