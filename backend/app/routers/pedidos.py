from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.dependencies import get_db, get_current_user
from app.models import Pedido
from app.modules.orders.service import change_order_state
from app.modules.orders.models import OrderState

router = APIRouter(
    prefix="/pedidos",
    tags=["pedidos"],
    responses={404: {"description": "Pedido no encontrado"}},
    deprecated=True
)

# ---------- Consultas ----------
@router.get("/")
async def listar_pedidos(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    estado: Optional[str] = Query(None),
):
    query = db.query(Pedido)
    email = current_user["email"]
    tipo = current_user["tipo"]
    if tipo == "asociacion":
        query = query.filter(Pedido.asociacion_email == email)
    else:
        query = query.filter(Pedido.comprador_email == email)
    if estado:
        query = query.filter(Pedido.estado == estado)
    return query.order_by(Pedido.fecha_creacion.desc()).all()

@router.get("/{pedido_id}")
async def obtener_pedido(
    pedido_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return pedido

# ---------- Creación ----------
@router.post("/", status_code=201)
async def crear_pedido(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    nuevo = Pedido(
        comprador_email=current_user["email"],
        estado=OrderState.DRAFT.value,
    )
    db.add(nuevo)
    db.flush()

    change_order_state(
        db, nuevo, OrderState.DRAFT.value,
        changed_by=current_user["email"],
        extra_data={"evento": "creación"}
    )
    db.commit()
    db.refresh(nuevo)
    return nuevo

# ---------- Mutaciones de estado ----------
@router.post("/{pedido_id}/confirmar")
async def confirmar_pedido(
    pedido_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    try:
        change_order_state(
            db, pedido, OrderState.CONFIRMED.value,
            changed_by=current_user["email"],
            extra_data={"motivo": "Confirmación del comprador"}
        )
        db.commit()
        db.refresh(pedido)
        return {"mensaje": "Pedido confirmado", "estado": pedido.estado}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{pedido_id}/asignar-transporte")
async def asignar_transporte(
    pedido_id: str,
    transportista_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    try:
        change_order_state(
            db, pedido, OrderState.TRANSPORT_ASSIGNED.value,
            changed_by=current_user["email"],
            extra_data={"transportista_id": transportista_id}
        )
        db.commit()
        db.refresh(pedido)
        return {"mensaje": "Transporte asignado", "estado": pedido.estado}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{pedido_id}/marcar-en-transito")
async def marcar_en_transito(
    pedido_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    try:
        change_order_state(
            db, pedido, OrderState.IN_TRANSIT.value,
            changed_by=current_user["email"],
            extra_data={"iniciado_por": current_user["email"]}
        )
        db.commit()
        db.refresh(pedido)
        return {"mensaje": "Pedido en tránsito", "estado": pedido.estado}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{pedido_id}/marcar-entregado")
async def marcar_entregado(
    pedido_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    try:
        change_order_state(
            db, pedido, OrderState.DELIVERED.value,
            changed_by=current_user["email"],
            extra_data={"recibido_por": current_user["email"]}
        )
        db.commit()
        db.refresh(pedido)
        return {"mensaje": "Pedido entregado", "estado": pedido.estado}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{pedido_id}/cerrar")
async def cerrar_pedido(
    pedido_id: str,
    motivo: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    try:
        change_order_state(
            db, pedido, OrderState.CLOSED.value,
            changed_by=current_user["email"],
            extra_data={"motivo": motivo or "Cierre del pedido"}
        )
        db.commit()
        db.refresh(pedido)
        return {"mensaje": "Pedido cerrado", "estado": pedido.estado}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))