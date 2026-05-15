from datetime import datetime
from sqlalchemy.orm import Session
from app.events.dispatcher import EventDispatcher
from app.events.payloads import PaymentConfirmedPayload, OrderBasePayload
from app.modules.documents.generators import generar_html as generar_doc_html
from app.modules.documents.service import crear_documento

def _on_payment_confirmed(payload: PaymentConfirmedPayload, db: Session):
    """
    Cuando el pago es confirmado, genera la factura correspondiente.
    """
    # Construir los datos para la factura igual que se hacía antes
    datos_factura = {
        "numero": f"FAC-{payload.wompi_referencia}",
        "fecha": datetime.now().strftime("%d/%m/%Y"),
        "vendedor": payload.vendedor_email,
        "comprador": payload.usuario_email,
        "items": [
            {
                "nombre": "Pedido " + payload.pedido_id[:8],
                "cantidad": 1,
                "precio_unit": payload.monto_total,
                "subtotal": payload.monto_total
            }
        ],
        "total": payload.monto_total,
    }

    html_factura = generar_doc_html("factura", datos_factura)
    crear_documento(
        db=db,
        tipo="factura",
        pedido_id=payload.pedido_id,
        usuario_generador=payload.usuario_email,
        contenido_html=html_factura,
    )

def _on_document_generated(payload: OrderBasePayload, db: Session):
    """
    Notifica al usuario que un documento fue generado.
    (Este listener se encarga de publicar el evento para que
     el módulo de notificaciones actúe.)
    """
    # La publicación se hace desde el módulo de notificaciones,
    # aquí solo podemos asegurar el evento si es necesario.
    pass  # la notificación la maneja el listener de notificaciones

def register(dispatcher: EventDispatcher):
    dispatcher.register("payment_confirmed", _on_payment_confirmed)
    # No es necesario registrar document_generated aquí, ya lo hace notificaciones