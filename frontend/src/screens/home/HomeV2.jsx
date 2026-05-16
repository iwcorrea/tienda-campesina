import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
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
        <Link to="/catalogo" className={styles.shortcut}>🌱 Buscar cosechas</Link>
        <Link to="/mis-pedidos" className={styles.shortcut}>📋 Mis pedidos</Link>
        {dashboard?.transportista && (
          <Link to="/transportista" className={styles.shortcut}>🚚 Viajes pendientes</Link>
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