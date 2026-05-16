import React, { useEffect, useState } from 'react';
import { fetchDashboard } from '../../api/v2';
import styles from './HomeV2.module.css';

export default function HomeV2() {
  const [dashboard, setDashboard] = useState(null);

  useEffect(() => {
    fetchDashboard().then(setDashboard).catch(() => {});
  }, []);

  return (
    <div className={styles.container}>
      <h1 className={styles.greeting}>Bienvenido</h1>
      <div className={styles.shortcuts}>
        <a href="/catalogo" className={styles.shortcut}>🌱 Buscar cosechas</a>
        <a href="/pedidos/borrador" className={styles.shortcut}>📋 Pedidos en curso</a>
        {dashboard?.transportista && (
          <a href="/transportista" className={styles.shortcut}>🚚 Viajes pendientes</a>
        )}
      </div>
      {dashboard && (
        <div className={styles.stats}>
          <p>Pedidos activos: {dashboard.activeOrders}</p>
          <p>Entregas hoy: {dashboard.todayDeliveries}</p>
        </div>
      )}
    </div>
  );
}