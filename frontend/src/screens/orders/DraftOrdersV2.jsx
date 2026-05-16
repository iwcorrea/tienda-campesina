import React, { useEffect, useState } from 'react';
import { fetchOrders } from '../../api/v2';
import styles from './DraftOrdersV2.module.css';

export default function DraftOrdersV2() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOrders('pendiente').then(data => { setOrders(data); setLoading(false); });
  }, []);

  if (loading) return <div className={styles.loading}>Cargando...</div>;
  if (!orders.length) return <div className={styles.empty}>Aún no tienes pedidos iniciados.</div>;

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>Mis pedidos en borrador</h2>
      {orders.map(order => (
        <a key={order.id} href={`/pedidos/${order.id}`} className={styles.card}>
          <span className={styles.id}>Pedido #{order.id.slice(0, 8)}</span>
          <span className={styles.state}>Estado: {order.estado}</span>
        </a>
      ))}
    </div>
  );
}