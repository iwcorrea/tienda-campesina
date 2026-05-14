"""
Estados avanzados del pedido agrícola y transiciones permitidas.
Los pedidos NO dependen del pago para avanzar.
"""

# Estados del pedido
ORDER_STATES = {
    "draft": "Borrador",
    "negotiating": "En negociación",
    "confirmed": "Confirmado",
    "transport_pending": "Pendiente de transporte",
    "transport_assigned": "Transporte asignado",
    "pickup_scheduled": "Recogida programada",
    "in_transit": "En tránsito",
    "delivered": "Entregado",
    "verified": "Verificado por comprador",
    "completed": "Completado",
    "cancelled": "Cancelado",
    "disputed": "En disputa",
}

# Transiciones válidas entre estados
VALID_TRANSITIONS = {
    "draft": ["negotiating", "cancelled"],
    "negotiating": ["confirmed", "cancelled"],
    "confirmed": ["transport_pending", "cancelled"],
    "transport_pending": ["transport_assigned", "cancelled"],
    "transport_assigned": ["pickup_scheduled", "cancelled"],
    "pickup_scheduled": ["in_transit", "cancelled"],
    "in_transit": ["delivered", "cancelled"],
    "delivered": ["verified"],
    "verified": ["completed", "disputed"],
    "completed": [],
    "cancelled": [],
    "disputed": ["cancelled", "completed"],
}

# Tipos de eventos que se registran
EVENT_TYPES = {
    "order_created": "Pedido creado",
    "order_confirmed": "Pedido confirmado",
    "transport_assigned": "Transporte asignado",
    "pickup_scheduled": "Recogida programada",
    "delivery_started": "Envío iniciado",
    "delivery_completed": "Entrega completada",
    "order_verified": "Verificado por comprador",
    "order_completed": "Pedido completado",
    "order_cancelled": "Pedido cancelado",
    "order_disputed": "Disputa iniciada",
    "payment_released": "Pago liberado",
    "note_added": "Nota agregada",
    "contact_added": "Contacto vinculado",
}