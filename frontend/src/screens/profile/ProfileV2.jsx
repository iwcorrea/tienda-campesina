import React from 'react';
import { useAuth } from '../../context/AuthContext'; // Ajustar ruta
import styles from './ProfileV2.module.css';

export default function ProfileV2() {
  const { user } = useAuth();
  if (!user) return <div className={styles.loading}>Cargando perfil...</div>;

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>Mi Perfil</h2>
      <div className={styles.info}>
        <p><strong>Nombre:</strong> {user.nombre}</p>
        <p><strong>Email:</strong> {user.email}</p>
        <p><strong>Rol:</strong> {user.tipo}</p>
      </div>
    </div>
  );
}