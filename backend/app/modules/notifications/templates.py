"""
Plantillas de mensajes para cada tipo de evento.
Devuelven el título y el contenido en texto plano o HTML simple.
"""
from app.modules.notifications.constants import NOTIFICATION_TYPES

def generar_notificacion(tipo_evento: str, datos: dict) -> dict:
    """Retorna un diccionario con 'titulo' y 'contenido'."""
    if tipo_evento == "order_created":
        return {
            "titulo": "Nuevo pedido recibido",
            "contenido": f"El comprador {datos.get('comprador_email')} ha creado el pedido #{datos.get('pedido_id', '')[:8]}."
        }
    elif tipo_evento == "order_confirmed":
        return {
            "titulo": "Pedido confirmado",
            "contenido": f"Tu pedido #{datos.get('pedido_id', '')[:8]} ha sido aceptado por la asociación. Revisa los documentos generados."
        }
    elif tipo_evento == "transport_assigned":
        return {
            "titulo": "Transporte asignado",
            "contenido": f"Se ha asignado un transportista al pedido #{datos.get('pedido_id', '')[:8]}. Costo de envío: ${datos.get('costo_envio', 0):,}."
        }
    elif tipo_evento == "delivered":
        return {
            "titulo": "Pedido entregado",
            "contenido": f"El pedido #{datos.get('pedido_id', '')[:8]} ha sido marcado como entregado."
        }
    elif tipo_evento == "payment_confirmed":
        return {
            "titulo": "Pago confirmado",
            "contenido": f"Se ha confirmado el pago por ${datos.get('monto', 0):,} para el pedido #{datos.get('pedido_id', '')[:8]}."
        }
    elif tipo_evento == "document_generated":
        return {
            "titulo": "Documento generado",
            "contenido": f"Se ha generado un documento tipo '{datos.get('tipo_documento')}' para el pedido #{datos.get('pedido_id', '')[:8]}."
        }
    elif tipo_evento == "contact_request":
        return {
            "titulo": "Solicitud de contacto",
            "contenido": f"{datos.get('solicitante_email')} te ha enviado una solicitud de contacto."
        }
    elif tipo_evento == "contact_accepted":
        return {
            "titulo": "Contacto aceptado",
            "contenido": f"{datos.get('receptor_email')} ha aceptado tu solicitud de contacto."
        }
    else:
        return {
            "titulo": "Notificación",
            "contenido": datos.get("mensaje", "Tienes una nueva notificación.")
        }