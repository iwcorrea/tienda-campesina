"""
Servicio de Pagos – Tienda Campesina
=====================================
Integración con Wompi API de Pagos a Terceros para procesar pagos
con comisión automática de la plataforma (8% por defecto).

Flujo:
  1. Comprador inicia el pago → se crea registro Pago (estado: pendiente)
  2. Comprador completa checkout en ventana de Wompi
  3. Wompi envía webhook → se confirma el Pago, se crea Comision
  4. Pedido pasa a estado "pagado"
  5. Wompi dispersa los fondos a la cuenta de la asociación (vía API Pagos a Terceros)
"""

import uuid
import hashlib
import hmac
import os
from datetime import datetime, timezone
from typing import Optional, Tuple
import httpx
from sqlalchemy.orm import Session
from app.models import Pago, Comision, Pedido, ItemPedido, Asociacion
from app.services.notificacion_service import crear_notificacion

# ─── CONSTANTES ────────────────────────────────────────────────
COMISION_PLATAFORMA = 8          # Porcentaje de comisión (8%)
WOMPI_API_URL = "https://api.wompi.sv"                         # Sandbox
# WOMPI_API_URL = "https://api.wompi.co"                        # Producción
WOMPI_API_KEY = os.getenv("WOMPI_API_KEY", "")
WOMPI_SECRET_KEY = os.getenv("WOMPI_SECRET_KEY", "")


# ─── CHECKOUT ──────────────────────────────────────────────────
def generar_referencia_unica() -> str:
    """Genera una referencia única de 12 caracteres para identificar la transacción."""
    return uuid.uuid4().hex[:12].upper()


def calcular_comision(monto_total: int, porcentaje: int = COMISION_PLATAFORMA) -> Tuple[int, int]:
    """
    Calcula la comisión de la plataforma y el monto neto para el vendedor.

    Args:
        monto_total: Monto total del pedido en COP
        porcentaje: Porcentaje de comisión (default: 8)

    Returns:
        Tuple[int, int]: (monto_comision, monto_vendedor)
    """
    monto_comision = int(monto_total * porcentaje / 100)
    monto_vendedor = monto_total - monto_comision
    return monto_comision, monto_vendedor


def calcular_total_pedido(db: Session, pedido_id: str) -> Tuple[int, str, str]:
    """
    Calcula el total real del pedido sumando todos los ítems.
    Retorna (total, asociacion_email, comprador_email).
    """
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        return 0, "", ""

    total = 0
    asociacion_email = ""
    comprador_email = pedido.comprador_email

    for item in pedido.items:
        precio_unit = item.precio_unitario_inicial
        # Si hay respuesta aceptada con contraoferta, usar ese precio
        for r in item.respuestas:
            if r.aceptado == "aceptado":
                if r.precio_contraoferta > 0:
                    precio_unit = r.precio_contraoferta
                break
        total += item.cantidad * precio_unit
        if item.producto:
            asociacion_email = item.producto.asociacion_email

    return total, asociacion_email, comprador_email


def crear_pago(db: Session, pedido_id: str, comprador_email: str) -> Optional[Pago]:
    """
    Crea un registro de pago y lo retorna.
    El estado inicial es 'pendiente'.
    """
    total, asociacion_email, _ = calcular_total_pedido(db, pedido_id)
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


# ─── VERIFICACIÓN DE WEBHOOK ──────────────────────────────────
def verificar_firma_webhook(payload: bytes, firma: str) -> bool:
    """
    Verifica que el webhook recibido sea legítimo según la firma HMAC-SHA256 de Wompi.
    """
    if not WOMPI_SECRET_KEY:
        return False
    hash_calculado = hmac.new(
        WOMPI_SECRET_KEY.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(hash_calculado, firma)


# ─── CONFIRMACIÓN DE PAGO ────────────────────────────────────
def confirmar_pago(db: Session, wompi_transaccion_id: str, wompi_referencia: str) -> Optional[Pago]:
    """
    Confirma un pago cuando Wompi notifica que la transacción fue exitosa.
    - Actualiza el estado del Pago a 'completado'
    - Crea el registro de Comision
    - Actualiza el estado del Pedido a 'pagado'
    - Notifica a la asociación y al comprador
    """
    pago = db.query(Pago).filter(
        Pago.wompi_referencia == wompi_referencia,
        Pago.estado == "pendiente"
    ).first()

    if not pago:
        return None

    pago.wompi_transaccion_id = wompi_transaccion_id
    pago.estado = "completado"
    pago.fecha_confirmacion = datetime.now(timezone.utc)

    # Obtener la asociación del pedido
    pedido = db.query(Pedido).filter(Pedido.id == pago.pedido_id).first()
    asociacion_email = ""
    if pedido:
        for item in pedido.items:
            if item.producto:
                asociacion_email = item.producto.asociacion_email
                break

    # Crear registro de comisión
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

    # Actualizar estado del pedido
    if pedido:
        pedido.estado = "pagado"
        # Notificar a la asociación
        crear_notificacion(
            db,
            destinatario_email=asociacion_email,
            remitente_email=pago.comprador_email,
            texto=f"Pago recibido por ${pago.monto_total:,} para el pedido #{pago.pedido_id[:8]}. Comisión: ${pago.comision_plataforma:,}.",
        )
        # Notificar al comprador
        crear_notificacion(
            db,
            destinatario_email=pago.comprador_email,
            remitente_email="sistema",
            texto=f"✅ Pago confirmado por ${pago.monto_total:,} para el pedido #{pago.pedido_id[:8]}.",
        )

    db.commit()
    return pago


# ─── DISPERSIÓN DE FONDOS (WOMPI API PAGOS A TERCEROS) ────────
async def dispersar_fondos_vendedor(db: Session, pago_id: str) -> bool:
    """
    Una vez confirmado el pago, dispersa los fondos (monto_vendedor) a la cuenta
    bancaria de la asociación utilizando la API de Pagos a Terceros de Wompi.

    Nota: Requiere que la asociación tenga registrada su información bancaria.
    """
    pago = db.query(Pago).filter(Pago.id == pago_id, Pago.estado == "completado").first()
    if not pago:
        return False

    # Obtener datos bancarios de la asociación
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

    # TODO: En producción, obtener datos bancarios reales de la asociación
    # (requiere agregar campos bancarios al modelo Asociacion)
    payload = {
        "payment": {
            "reference": f"PAGO-{pago.wompi_referencia}",
            "description": f"Venta Tienda Campesina - Pedido #{pago.pedido_id[:8]}",
            "currency": "COP",
            "amount": {
                "total": pago.monto_vendedor,
            },
            "collector": {
                "name": asociacion.nombre,
                "email": asociacion.email,
                "document_type": "CC",
                "document_number": "",     # Requeriría nuevo campo en modelo
            }
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{WOMPI_API_URL}/payouts",
                json=payload,
                headers={
                    "Authorization": f"Bearer {WOMPI_API_KEY}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
            if resp.status_code in (200, 201):
                return True
    except Exception:
        pass
    return False