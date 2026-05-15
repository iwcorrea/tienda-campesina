from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

from app.dependencies import get_db, get_current_user
from app.modules.transport.service import change_transport_state
from app.modules.transport.models import Transport, TransportState, TransportStateLog
from app.modules.transport.events import publicar_evento_transporte
from app.models import Pedido

router = APIRouter()

# ─── Schemas de respuesta ──────────────────────────
class TransportResponse(BaseModel):
    id: str
    pedido_id: str
    transportista_id: str
    estado: str
    fecha_creacion: datetime
    costo: int
    detalles: dict = Field(default_factory=dict)

    class Config:
        from_attributes = True

class TimelineEntry(BaseModel):
    id: str
    previous_state: Optional[str]
    new_state: str
    changed_by: str
    changed_at: datetime
    extra_data: dict

    class Config:
        from_attributes = True

# ─── Endpoints ─────────────────────────────────────

@router.post("/", response_model=TransportResponse, status_code=201)
async def crear_oferta_transporte(
    pedido_id: str,
    costo: int = 0,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Crea una oferta de transporte para un pedido (transportista)."""
    if current_user["tipo"] != "transportista":
        raise HTTPException(status_code=403, detail="Solo transportistas pueden crear ofertas")

    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    # Crear oferta de transporte
    transporte = Transport(
        pedido_id=pedido_id,
        transportista_id=current_user["email"],  # email del transportista
        costo=costo,
        estado=TransportState.PENDING_ACCEPTANCE.value,
    )
    db.add(transporte)
    db.flush()

    # Registrar estado inicial y publicar evento
    change_transport_state(
        db, transporte, TransportState.PENDING_ACCEPTANCE.value,
        changed_by=current_user["email"],
        extra_data={"evento": "creación_oferta"}
    )
    publicar_evento_transporte(
        db,
        "transport_offer_created",
        transport_id=transporte.id,
        pedido_id=pedido_id,
        usuario_email=current_user["email"],
        estado_nuevo=TransportState.PENDING_ACCEPTANCE.value,
        descripcion="Oferta de transporte creada"
    )

    db.commit()
    db.refresh(transporte)
    return transporte

@router.post("/{transport_id}/accept", response_model=TransportResponse)
async def aceptar_oferta(
    transport_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """El comprador/productor acepta la oferta de transporte."""
    transporte = db.query(Transport).filter(Transport.id == transport_id).first()
    if not transporte:
        raise HTTPException(status_code=404, detail="Transporte no encontrado")

    # Verificar que el usuario esté involucrado en el pedido
    pedido = transporte.pedido
    if current_user["email"] not in [pedido.comprador_email] + [i.producto.asociacion_email for i in pedido.items]:
        raise HTTPException(status_code=403, detail="No autorizado")

    try:
        change_transport_state(
            db, transporte, TransportState.ACCEPTED.value,
            changed_by=current_user["email"],
            extra_data={"motivo": "Oferta aceptada"}
        )
        publicar_evento_transporte(
            db,
            "transport_accepted",
            transport_id=transporte.id,
            pedido_id=transporte.pedido_id,
            usuario_email=current_user["email"],
            estado_anterior=TransportState.PENDING_ACCEPTANCE.value,
            estado_nuevo=TransportState.ACCEPTED.value,
            descripcion="Oferta de transporte aceptada"
        )
        db.commit()
        db.refresh(transporte)
        return transporte
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{transport_id}/pickup", response_model=TransportResponse)
async def recoger(
    transport_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Confirma recogida (transportista)."""
    transporte = db.query(Transport).filter(Transport.id == transport_id, Transport.transportista_id == current_user["email"]).first()
    if not transporte:
        raise HTTPException(status_code=404, detail="No encontrado o no autorizado")

    try:
        change_transport_state(db, transporte, TransportState.PICKED_UP.value, changed_by=current_user["email"])
        publicar_evento_transporte(db, "transport_picked_up", transport_id=transport_id, pedido_id=transporte.pedido_id,
                                   usuario_email=current_user["email"], estado_anterior=TransportState.ACCEPTED.value,
                                   estado_nuevo=TransportState.PICKED_UP.value, descripcion="Recogida confirmada")
        db.commit()
        db.refresh(transporte)
        return transporte
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{transport_id}/deliver", response_model=TransportResponse)
async def entregar(
    transport_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Confirma entrega (transportista). Al entregar, se publica transport.delivered."""
    transporte = db.query(Transport).filter(Transport.id == transport_id, Transport.transportista_id == current_user["email"]).first()
    if not transporte:
        raise HTTPException(status_code=404, detail="No encontrado o no autorizado")

    try:
        change_transport_state(db, transporte, TransportState.DELIVERED.value, changed_by=current_user["email"])
        publicar_evento_transporte(db, "transport_delivered", transport_id=transport_id, pedido_id=transporte.pedido_id,
                                   usuario_email=current_user["email"], estado_anterior=TransportState.IN_TRANSIT.value,
                                   estado_nuevo=TransportState.DELIVERED.value, descripcion="Entrega completada")
        db.commit()
        db.refresh(transporte)
        return transporte
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{transport_id}", response_model=TransportResponse)
async def obtener_transporte(transport_id: str, db: Session = Depends(get_db)):
    transporte = db.query(Transport).filter(Transport.id == transport_id).first()
    if not transporte:
        raise HTTPException(status_code=404, detail="No encontrado")
    return transporte

@router.get("/{transport_id}/timeline", response_model=List[TimelineEntry])
async def timeline(transport_id: str, db: Session = Depends(get_db)):
    logs = db.query(TransportStateLog).filter(TransportStateLog.transport_id == transport_id).order_by(TransportStateLog.changed_at.asc()).all()
    return logs