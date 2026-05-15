"""
Router v2 del módulo orders.
Expone endpoints bajo /api/v2/modular/orders para el nuevo frontend.
Usa la máquina de estados existente y el EventDispatcher central.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.dependencies import get_db, get_current_user
from app.modules.orders.service import change_order_state
from app.modules.orders.models import OrderState, OrderStateLog
from app.modules.orders.events import registrar_evento
from app.models import Pedido
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List

# ─── Contratos Pydantic v2 (respuesta) ────────────────────────────
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

    class Config:
        from_attributes = True

class CreateOrderRequest(BaseModel):
    # futuro: lista de items, pero por ahora solo creamos un borrador vacío
    pass

router = APIRouter()

# ─── Crear pedido (DRAFT) ──────────────────────────────────────────
@router.post("/", response_model=OrderResponse, status_code=201)
async def crear_pedido_v2(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Crea un nuevo pedido en estado DRAFT (borrador) para el comprador autenticado.
    Publica el evento order_created.
    """
    # Validar que el usuario es un comprador
    if current_user["tipo"] not in ("comprador", "asociacion"):  # Ajusta según tu lógica
        raise HTTPException(status_code=403, detail="Solo compradores pueden crear pedidos")

    pedido = Pedido(
        comprador_email=current_user["email"],
        estado=OrderState.DRAFT.value,   # "pendiente"
    )
    db.add(pedido)
    db.flush()

    # Registrar estado inicial y evento
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

# ─── Iniciar negociación (DRAFT → NEGOTIATION) ─────────────────────
@router.post("/{order_id}/negotiate", response_model=OrderResponse)
async def iniciar_negociacion_v2(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Transiciona el pedido de DRAFT a NEGOTIATION.
    Publica el evento order_negotiation_started.
    """
    pedido = db.query(Pedido).filter(Pedido.id == order_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    # Permisos: solo el comprador puede iniciar negociación
    if pedido.comprador_email != current_user["email"] and current_user["tipo"] != "admin":
        raise HTTPException(status_code=403, detail="No autorizado")

    try:
        change_order_state(
            db=db,
            pedido=pedido,
            new_state=OrderState.NEGOTIATION.value,   # "aceptado"
            changed_by=current_user["email"],
            extra_data={"motivo": "Inicio de negociación"}
        )
        registrar_evento(
            db,
            pedido.id,
            "order_negotiation_started",
            usuario_email=current_user["email"],
            estado_anterior=OrderState.DRAFT.value,
            estado_nuevo=OrderState.NEGOTIATION.value,
            descripcion="Negociación iniciada"
        )
        db.commit()
        db.refresh(pedido)
        return pedido
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ─── Confirmar pedido (NEGOTIATION → CONFIRMED) ─────────────────────
@router.post("/{order_id}/confirm", response_model=OrderResponse)
async def confirmar_pedido_v2(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Transiciona el pedido a CONFIRMED (equivalente a 'pagado' en legacy).
    Normalmente esto sería tras el pago, pero en el flujo modular puede ser un paso intermedio.
    """
    pedido = db.query(Pedido).filter(Pedido.id == order_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    try:
        change_order_state(
            db=db,
            pedido=pedido,
            new_state=OrderState.CONFIRMED.value,   # "pagado"
            changed_by=current_user["email"],
            extra_data={"motivo": "Confirmación v2"}
        )
        registrar_evento(
            db,
            pedido.id,
            "order_confirmed",
            usuario_email=current_user["email"],
            estado_anterior=OrderState.NEGOTIATION.value,
            estado_nuevo=OrderState.CONFIRMED.value,
            descripcion="Pedido confirmado (pagado)"
        )
        db.commit()
        db.refresh(pedido)
        return pedido
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ─── Obtener pedido ─────────────────────────────────────────────────
@router.get("/{order_id}", response_model=OrderResponse)
async def obtener_pedido_v2(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    pedido = db.query(Pedido).filter(Pedido.id == order_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    # Verificar que el usuario tenga relación con el pedido
    if pedido.comprador_email != current_user["email"] and current_user["tipo"] != "admin":
        # Podría ser productor, pero no implementamos ese chequeo ahora
        pass
    return pedido

# ─── Historial de estados ──────────────────────────────────────────
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