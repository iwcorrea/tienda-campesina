import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { fetchOrders } from '../../api/v2';
import styles from './OrdersListV2.module.css';

const ESTADO_MAP = {
  pendiente: { color: '#757575', bg: '#f5f5f5', label: 'Pendiente' },
  negociacion: { color: '#F9A825', bg: '#fff8e1', label: 'Negociando' },
  pagado: { color: '#2E7D32', bg: '#e8f5e9', label: 'Confirmado' },
  transporte_asignado: { color: '#F9A825', bg: '#fff8e1', label: 'Transporte asignado' },
  en_transito: { color: '#F9A825', bg: '#fff8e1', label: 'En camino' },
  entregado: { color: '#2E7D32', bg: '#e8f5e9', label: 'Entregado' },
  cerrado: { color: '#757575', bg: '#f5f5f5', label: 'Cerrado' },
};

export default function OrdersListV2() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOrders().then(data => setOrders(data)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className={styles.loading}>Cargando pedidos...</div>;
  if (!orders.length) return <div className={styles.empty}>Aún no tienes pedidos.</div>;

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>Mis pedidos</h2>
      {orders.map(order => {
        const info = ESTADO_MAP[order.estado] || ESTADO_MAP['pendiente'];
        return (
          <Link to={`/pedido/${order.id}`} key={order.id} className={styles.card}
            style={{ borderLeftColor: info.color, backgroundColor: info.bg }}>
            <span className={styles.id}>Pedido #{order.id.slice(0, 8)}</span>
            <span className={styles.state} style={{ color: info.color }}>{info.label}</span>
          </Link>
        );
      })}
    </div>
  );
}