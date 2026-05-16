from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

from app.dependencies import get_db, get_current_user
from app.modules.orders.service import change_order_state
from app.modules.orders.models import OrderState, OrderStateLog
from app.modules.orders.events import registrar_evento
from app.models import Pedido

# Schemas Pydantic v2
class OrderTimelineEntry(BaseModel):
    id: str
    previous_state: Optional[str]
    new_state: str
    changed_by: str
    changed_at: datetime
    extra_data: dict = Field(default_factory=dict)

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: str
    comprador_email: str
    estado: str
    fecha_creacion: datetime
    transportista_id: Optional[str] = None
    estado_envio: Optional[str] = "pendiente"
    costo_envio: Optional[int] = 0
    region: Optional[str] = None

    class Config:
        from_attributes = True

router = APIRouter()

# ---------- Crear pedido (DRAFT) ----------
@router.post("/", response_model=OrderResponse, status_code=201)
async def crear_pedido_v2(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["tipo"] not in ("comprador", "asociacion"):
        raise HTTPException(status_code=403, detail="Solo compradores pueden crear pedidos")

    pedido = Pedido(
        comprador_email=current_user["email"],
        estado=OrderState.DRAFT.value,
        region=current_user.get("region")
    )
    db.add(pedido)
    db.flush()

    change_order_state(
        db=db,
        pedido=pedido,
        new_state=OrderState.DRAFT.value,
        changed_by=current_user["email"],
        extra_data={"evento": "creación_v2"}
    )
    registrar_evento(
        db,
        pedido.id,
        "order_created",
        usuario_email=current_user["email"],
        estado_nuevo=OrderState.DRAFT.value,
        descripcion="Pedido creado vía API v2"
    )

    db.commit()
    db.refresh(pedido)
    return pedido

# ---------- Iniciar negociación ----------
@router.post("/{order_id}/negotiate", response_model=OrderResponse)
async def iniciar_negociacion_v2(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    pedido = db.query(Pedido).filter(Pedido.id == order_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    if pedido.comprador_email != current_user["email"] and current_user["tipo"] != "admin":
        raise HTTPException(status_code=403, detail="No autorizado")

    try:
        change_order_state(
            db=db,
            pedido=pedido,
            new_state=OrderState.NEGOTIATION.value,
            changed_by=current_user["email"],
            extra_data={"motivo": "Inicio de negociación"}
        )
        registrar_evento(db, pedido.id, "order_negotiation_started",
                         usuario_email=current_user["email"],
                         estado_anterior=OrderState.DRAFT.value,
                         estado_nuevo=OrderState.NEGOTIATION.value,
                         descripcion="Negociación iniciada")
        db.commit()
        db.refresh(pedido)
        return pedido
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ---------- Confirmar pedido ----------
@router.post("/{order_id}/confirm", response_model=OrderResponse)
async def confirmar_pedido_v2(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    pedido = db.query(Pedido).filter(Pedido.id == order_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    try:
        change_order_state(
            db=db,
            pedido=pedido,
            new_state=OrderState.CONFIRMED.value,
            changed_by=current_user["email"],
            extra_data={"motivo": "Confirmación v2"}
        )
        registrar_evento(db, pedido.id, "order_confirmed",
                         usuario_email=current_user["email"],
                         estado_anterior=OrderState.NEGOTIATION.value,
                         estado_nuevo=OrderState.CONFIRMED.value,
                         descripcion="Pedido confirmado (pagado)")
        db.commit()
        db.refresh(pedido)
        return pedido
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ---------- Obtener pedido ----------
@router.get("/{order_id}", response_model=OrderResponse)
async def obtener_pedido_v2(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    pedido = db.query(Pedido).filter(Pedido.id == order_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return pedido

# ---------- Historial de estados ----------
@router.get("/{order_id}/timeline", response_model=List[OrderTimelineEntry])
async def obtener_timeline_v2(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    pedido = db.query(Pedido).filter(Pedido.id == order_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    logs = db.query(OrderStateLog).filter(
        OrderStateLog.order_id == order_id
    ).order_by(OrderStateLog.changed_at.asc()).all()
    return logs

# ---------- Listar pedidos (con filtro por región) ----------
@router.get("/", response_model=List[OrderResponse])
async def listar_pedidos_v2(
    estado: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    query = db.query(Pedido)
    effective_region = region or (current_user.get("region") if current_user else None)
    if effective_region:
        query = query.filter(Pedido.region == effective_region)
    if estado:
        query = query.filter(Pedido.estado == estado)
    return query.order_by(Pedido.fecha_creacion.desc()).all()