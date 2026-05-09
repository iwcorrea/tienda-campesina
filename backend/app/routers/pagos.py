from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.services.pago_service import (
    crear_pago,
    confirmar_pago,
    verificar_firma_webhook,
    calcular_total_pedido,
    COMISION_PLATAFORMA,
)
from app.viewmodels.pago import PagoViewModel
from app.templates import templates
from app.models import Pedido, Pago

router = APIRouter(prefix="/pagos", tags=["pagos"])


@router.get("/checkout/{pedido_id}", response_class=HTMLResponse)
def checkout(
    request: Request,
    pedido_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Muestra la página de checkout con el resumen del pedido y el detalle de comisión.
    """
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido or pedido.comprador_email != current_user["email"]:
        return RedirectResponse(url="/pedidos", status_code=303)

    total, asociacion_email, _ = calcular_total_pedido(db, pedido_id)
    monto_comision, monto_vendedor = calcular_comision(total)

    from app.services.pago_service import calcular_comision

    return templates.TemplateResponse("pago_checkout.html", {
        "request": request,
        "pedido": pedido,
        "total": total,
        "comision_plataforma": monto_comision,
        "monto_vendedor": monto_vendedor,
        "porcentaje_comision": COMISION_PLATAFORMA,
        "wompi_api_key": "",  # Se completa con la variable de entorno real
    })


@router.post("/iniciar/{pedido_id}")
def iniciar_pago(
    request: Request,
    pedido_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Crea el registro de pago y redirige a la confirmación.
    En producción, aquí se redirigiría al checkout de Wompi.
    """
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    pago = crear_pago(db, pedido_id, current_user["email"])
    if not pago:
        return RedirectResponse(url="/pedidos?error=pago", status_code=303)

    return RedirectResponse(
        url=f"/pagos/procesar/{pago.id}",
        status_code=303
    )


@router.get("/procesar/{pago_id}", response_class=HTMLResponse)
def procesar_pago(
    request: Request,
    pago_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Muestra la página de procesamiento de pago (simulación de Wompi).
    """
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    pago = db.query(Pago).filter(Pago.id == pago_id).first()
    if not pago:
        return RedirectResponse(url="/pedidos", status_code=303)

    pago_vm = PagoViewModel.from_orm(pago)
    return templates.TemplateResponse("pago_procesar.html", {
        "request": request,
        "pago": pago_vm,
    })


@router.post("/confirmar/{pago_id}")
def confirmar_pago_post(
    request: Request,
    pago_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Simula la confirmación del pago (como si Wompi enviara el webhook).
    En producción, esta lógica estaría en el endpoint del webhook.
    """
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    pago = db.query(Pago).filter(Pago.id == pago_id, Pago.estado == "pendiente").first()
    if not pago:
        return RedirectResponse(url="/pedidos?error=pago_estado", status_code=303)

    # Simular webhook de Wompi
    confirmar_pago(db, "SIMULADO-" + pago_id, pago.wompi_referencia)

    return RedirectResponse(url=f"/pagos/exito/{pago.id}", status_code=303)


@router.get("/exito/{pago_id}", response_class=HTMLResponse)
def pago_exitoso(
    request: Request,
    pago_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Página de confirmación después del pago exitoso."""
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    pago = db.query(Pago).filter(Pago.id == pago_id).first()
    if not pago:
        return RedirectResponse(url="/pedidos", status_code=303)

    pago_vm = PagoViewModel.from_orm(pago)
    return templates.TemplateResponse("pago_exito.html", {
        "request": request,
        "pago": pago_vm,
    })


@router.post("/webhook")
async def webhook_wompi(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint que recibe las notificaciones de Wompi cuando una transacción
    cambia de estado. Verifica la firma HMAC-SHA256 para seguridad.
    """
    body = await request.body()
    firma = request.headers.get("X-Wompi-Signature", "")

    # Verificar firma (opcional en sandbox, obligatorio en producción)
    if firma and not verificar_firma_webhook(body, firma):
        return JSONResponse({"error": "Firma inválida"}, status_code=403)

    try:
        import json
        data = json.loads(body)
        transaccion_id = data.get("data", {}).get("transaction", {}).get("id", "")
        referencia = data.get("data", {}).get("transaction", {}).get("reference", "")

        if transaccion_id and referencia:
            confirmar_pago(db, transaccion_id, referencia)
            return JSONResponse({"status": "ok"}, status_code=200)
    except Exception:
        pass

    return JSONResponse({"status": "ignored"}, status_code=200)