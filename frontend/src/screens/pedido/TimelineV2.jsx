import React, { useEffect, useState, useCallback } from 'react';
import { fetchOrderTimeline, fetchOrder } from '../../api/v2';
import NegotiationPanel from './NegotiationPanel';
import FeedbackEmoji from '../../components/FeedbackEmoji';
import { track } from '../../telemetry/pilot';
import styles from './TimelineV2.module.css';

const ESTADO_MAP = {
  pendiente: {
    icon: '🌱',
    label: 'Cosecha publicada',
    color: '#757575',
    bg: '#f5f5f5',
  },
  aceptado: {
    icon: '🤝',
    label: 'Hay un interesado',
    color: '#F9A825',
    bg: '#fff8e1',
  },
  pagado: {
    icon: '✅',
    label: 'Pedido confirmado',
    color: '#F9A825',
    bg: '#fff8e1',
  },
  transporte_asignado: {
    icon: '🚚',
    label: 'Transportista asignado',
    color: '#F9A825',
    bg: '#fff8e1',
  },
  en_transito: {
    icon: '🚚',
    label: 'El transportista va en camino',
    color: '#F9A825',
    bg: '#fff8e1',
  },
  entregado: {
    icon: '📦',
    label: 'Entregado',
    color: '#2E7D32',
    bg: '#e8f5e9',
  },
  cerrado: {
    icon: '🔒',
    label: 'Cerrado',
    color: '#757575',
    bg: '#f5f5f5',
  },
};

const DEFAULT_ESTADO = {
  icon: '❓',
  label: 'Desconocido',
  color: '#9e9e9e',
  bg: '#f5f5f5',
};

function getRelativeTime(dateString) {
  const now = new Date();
  const then = new Date(dateString);
  const diffMs = now - then;
  const seconds = Math.floor(diffMs / 1000);
  if (seconds < 60) return 'Ahora mismo';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `Hace ${minutes} min`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `Hace ${hours} horas`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `Hace ${days} días`;
  return then.toLocaleDateString('es-CO', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
}

export default function TimelineV2({ orderId }) {
  const [eventos, setEventos] = useState([]);
  const [order, setOrder] = useState(null);
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

  // Telemetría – vista de pantalla
  useEffect(() => {
    track('screen_view', { screen: 'timeline' });
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleProposalSuccess = () => {
    loadData();
  };

  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.skeleton} />
        <div className={styles.skeleton} />
        <div className={styles.skeleton} />
      </div>
    );
  }

  if (eventos.length === 0 && !order) {
    return <div className={styles.empty}>Aún no hay información del pedido.</div>;
  }

  const currentState = order?.estado || (eventos.length > 0 ? eventos[eventos.length - 1].new_state : null);
  const isNegotiating = currentState === 'negociacion';

  return (
    <div className={styles.container}>
      {offline && (
        <div className={styles.offlineBar}>Sin conexión – información guardada</div>
      )}
      <h2 className={styles.title}>¿Cómo va tu pedido?</h2>
      <div className={styles.timeline}>
        {eventos.map((evento, idx) => {
          const estadoInfo = ESTADO_MAP[evento.new_state] || DEFAULT_ESTADO;
          return (
            <div
              key={evento.id || idx}
              className={styles.event}
              style={{ borderLeftColor: estadoInfo.color, backgroundColor: estadoInfo.bg }}
            >
              <span className={styles.icon}>{estadoInfo.icon}</span>
              <div className={styles.content}>
                <span className={styles.stateText}>{estadoInfo.label}</span>
                <span className={styles.time}>{getRelativeTime(evento.changed_at)}</span>
                {evento.extra_data?.transportista_id && (
                  <span className={styles.detail}>
                    Transportista: {evento.extra_data.transportista_id}
                  </span>
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

      <FeedbackEmoji screenName="timeline" />
    </div>
  );
}