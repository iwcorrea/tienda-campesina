import React, { useEffect, useState } from 'react';

/**
 * Pantalla legacy de detalle de pedido.
 * Consume GET /api/v1/pedidos/{id} y muestra información básica.
 * No se modifica durante la migración.
 */
export default function PedidoDetailLegacy({ orderId }) {
  const [pedido, setPedido] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/v1/pedidos/${orderId}`)
      .then((res) => res.json())
      .then((data) => setPedido(data))
      .catch(() => setPedido(null))
      .finally(() => setLoading(false));
  }, [orderId]);

  if (loading) return <div>Cargando pedido...</div>;
  if (!pedido) return <div>Pedido no encontrado</div>;

  return (
    <div style={{ padding: 16, fontFamily: 'system-ui' }}>
      <h2>Pedido #{pedido.id.slice(0, 8)}</h2>
      <p><strong>Estado:</strong> {pedido.estado}</p>
      <p><strong>Comprador:</strong> {pedido.comprador_email}</p>
      {/* Más campos según el modelo real */}
    </div>
  );
}