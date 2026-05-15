import React, { useEffect, useState, useCallback } from 'react';
import { fetchOrderTimeline, fetchOrder } from '../../api/v2';
import NegotiationPanel from './NegotiationPanel';
import styles from './TimelineV2.module.css';

const ESTADO_MAP = { /* ... igual que antes ... */ };

const DEFAULT_ESTADO = { /* ... igual que antes ... */ };

function getRelativeTime(dateString) { /* ... igual que antes ... */ }

export default function TimelineV2({ orderId }) {
  const [eventos, setEventos] = useState([]);
  const [order, setOrder] = useState(null);   // datos completos del pedido
  const [loading, setLoading] = useState(true);
  const [offline, setOffline] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [timeline, orderData] = await Promise.all([
        fetchOrderTimeline(orderId),
        fetchOrder(orderId),
      ]);
      setEventos(timeline);
      setOrder(orderData);
      setOffline(false);
    } catch (err) {
      // Si falla, intentar cache individual
      try {
        const cachedTimeline = await fetchOrderTimeline(orderId);
        if (cachedTimeline._fromCache) {
          setEventos(cachedTimeline);
          setOffline(true);
        }
      } catch {}
      try {
        const cachedOrder = await fetchOrder(orderId);
        if (cachedOrder._fromCache) {
          setOrder(cachedOrder);
          setOffline(true);
        }
      } catch {}
    } finally {
      setLoading(false);
    }
  }, [orderId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Refrescar después de una propuesta exitosa
  const handleProposalSuccess = () => {
    loadData();
  };

  if (loading) { /* esqueleto... */ }

  if (eventos.length === 0 && !order) { /* vacío... */ }

  const currentState = order?.estado || (eventos.length > 0 ? eventos[eventos.length - 1].new_state : null);
  const isNegotiating = currentState === 'negociacion';

  return (
    <div className={styles.container}>
      {offline && <div className={styles.offlineBar}>Sin conexión – información guardada</div>}
      <h2 className={styles.title}>¿Cómo va tu pedido?</h2>
      <div className={styles.timeline}>
        {eventos.map((evento, idx) => {
          const estadoInfo = ESTADO_MAP[evento.new_state] || DEFAULT_ESTADO;
          return (
            <div key={evento.id || idx} className={styles.event} style={{ borderLeftColor: estadoInfo.color, backgroundColor: estadoInfo.bg }}>
              <span className={styles.icon}>{estadoInfo.icon}</span>
              <div className={styles.content}>
                <span className={styles.stateText}>{estadoInfo.label}</span>
                <span className={styles.time}>{getRelativeTime(evento.changed_at)}</span>
                {evento.extra_data?.transportista_id && (
                  <span className={styles.detail}>Transportista: {evento.extra_data.transportista_id}</span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {isNegotiating && order && (
        <NegotiationPanel
          orderId={orderId}
          currentQuantity={order.current_quantity || order.items?.[0]?.cantidad || 0}
          currentPrice={order.current_price_per_kg || order.items?.[0]?.precio_unitario_inicial || 0}
          onProposalSuccess={handleProposalSuccess}
        />
      )}
    </div>
  );
}