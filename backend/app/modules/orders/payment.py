import uuid
import hashlib
import hmac
import os
from datetime import datetime, timezone
from typing import Optional, Tuple
import httpx
from sqlalchemy.orm import Session
from app.models import Pago, Comision, Pedido, Transportista
from app.modules.orders.service import change_order_state
from app.modules.orders.models import OrderState
from app.modules.orders.events import registrar_evento
from app.modules.products.inventory import salida_stock_por_pedido

COMISION_PLATAFORMA = 8
WOMPI_API_URL = "https://api.wompi.sv"
WOMPI_API_KEY = os.getenv("WOMPI_API_KEY", "")
WOMPI_SECRET_KEY = os.getenv("WOMPI_SECRET_KEY", "")

def generar_referencia_unica() -> str:
    return uuid.uuid4().hex[:12].upper()

def calcular_comision(monto_total: int, porcentaje: int = COMISION_PLATAFORMA) -> Tuple[int, int]:
    monto_comision = int(monto_total * porcentaje / 100)
    monto_vendedor = monto_total - monto_comision
    return monto_comision, monto_vendedor

def calcular_total_pedido(db: Session, pedido_id: str) -> Tuple[int, str, str, int]:
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        return 0, "", "", 0
    total_productos = 0
    asociacion_email = ""
    comprador_email = pedido.comprador_email
    for item in pedido.items:
        precio_unit = item.precio_unitario_inicial
        for r in item.respuestas:
            if r.aceptado == "aceptado" and r.precio_contraoferta > 0:
                precio_unit = r.precio_contraoferta
                break
        total_productos += item.cantidad * precio_unit
        if item.producto:
            asociacion_email = item.producto.asociacion_email
    costo_envio = pedido.costo_envio or 0
    total = total_productos + costo_envio
    return total, asociacion_email, comprador_email, costo_envio

def crear_pago(db: Session, pedido_id: str, comprador_email: str) -> Optional[Pago]:
    total, asociacion_email, _, costo_envio = calcular_total_pedido(db, pedido_id)
    if total <= 0:
        return None
    monto_comision, monto_vendedor = calcular_comision(total)
    referencia = generar_referencia_unica()
    pago = Pago(
        id=str(uuid.uuid4()),
        pedido_id=pedido_id,
        comprador_email=comprador_email,
        monto_total=total,
        comision_plataforma=monto_comision,
        monto_vendedor=monto_vendedor,
        estado="pendiente",
        wompi_referencia=referencia,
    )
    db.add(pago)
    db.commit()
    db.refresh(pago)
    return pago

def verificar_firma_webhook(payload: bytes, firma: str) -> bool:
    if not WOMPI_SECRET_KEY:
        return False
    hash_calculado = hmac.new(WOMPI_SECRET_KEY.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(hash_calculado, firma)

def confirmar_pago(db: Session, wompi_transaccion_id: str, wompi_referencia: str) -> Optional[Pago]:
    pago = db.query(Pago).filter(Pago.wompi_referencia == wompi_referencia, Pago.estado == "pendiente").first()
    if not pago:
        return None
    pago.wompi_transaccion_id = wompi_transaccion_id
    pago.estado = "completado"
    pago.fecha_confirmacion = datetime.now(timezone.utc)
    pedido = db.query(Pedido).filter(Pedido.id == pago.pedido_id).first()
    asociacion_email = ""
    if pedido:
        for item in pedido.items:
            if item.producto:
                asociacion_email = item.producto.asociacion_email
                break
    comision = Comision(
        id=str(uuid.uuid4()),
        pago_id=pago.id,
        pedido_id=pago.pedido_id,
        asociacion_email=asociacion_email,
        comprador_email=pago.comprador_email,
        monto_venta=pago.monto_total,
        porcentaje_comision=COMISION_PLATAFORMA,
        monto_comision=pago.comision_plataforma,
    )
    db.add(comision)
    if pedido:
        change_order_state(db=db, pedido=pedido, new_state=OrderState.CONFIRMED.value,
                           changed_by=pago.comprador_email,
                           extra_data={"motivo": "Pago confirmado", "monto": pago.monto_total})
        transportista_email = None
        if pedido.transportista:
            transportista_email = pedido.transportista.email
        registrar_evento(db, pago.pedido_id, "payment_confirmed",
                         usuario_email=pago.comprador_email,
                         estado_anterior="aceptado",
                         estado_nuevo=OrderState.CONFIRMED.value,
                         descripcion=f"Pago confirmado por ${pago.monto_total:,}",
                         extra={
                             "monto_total": pago.monto_total,
                             "comision_plataforma": pago.comision_plataforma,
                             "monto_vendedor": pago.monto_vendedor,
                             "vendedor_email": asociacion_email,
                             "transportista_email": transportista_email,
                             "costo_envio": pedido.costo_envio or 0,
                             "wompi_referencia": pago.wompi_referencia,
                         })
        salida_stock_por_pedido(db, pago.pedido_id)
    db.commit()
    return pago

async def dispersar_fondos_vendedor(db: Session, pago_id: str) -> bool:
    pago = db.query(Pago).filter(Pago.id == pago_id, Pago.estado == "completado").first()
    if not pago:
        return False
    pedido = db.query(Pedido).filter(Pedido.id == pago.pedido_id).first()
    if not pedido:
        return False
    asociacion = None
    for item in pedido.items:
        if item.producto and item.producto.asociacion:
            asociacion = item.producto.asociacion
            break
    if not asociacion:
        return False
    payload = {
        "payment": {
            "reference": f"PAGO-{pago.wompi_referencia}",
            "description": f"Venta Tienda Campesina - Pedido #{pago.pedido_id[:8]}",
            "currency": "COP",
            "amount": {"total": pago.monto_vendedor},
            "collector": {
                "name": asociacion.nombre,
                "email": asociacion.email,
                "document_type": "CC",
                "document_number": "",
            }
        }
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{WOMPI_API_URL}/payouts", json=payload,
                                     headers={"Authorization": f"Bearer {WOMPI_API_KEY}", "Content-Type": "application/json"},
                                     timeout=30.0)
            if resp.status_code in (200, 201):
                return True
    except Exception:
        pass
    return False