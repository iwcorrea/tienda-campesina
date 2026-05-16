import React, { useContext } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { logoutV2 } from '../api/v2';
import styles from './NavBar.module.css';

export default function NavBar() {
  const { user, setUser } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logoutV2();
    setUser(null);
    navigate('/login');
  };

  const isTransportista = user?.tipo === 'transportista';

  return (
    <nav className={styles.nav}>
      {user ? (
        <>
          <NavLink to={isTransportista ? '/transportista' : '/mis-pedidos'} className={styles.link}>
            📋 {isTransportista ? 'Viajes' : 'Pedidos'}
          </NavLink>
          <NavLink to="/catalogo" className={styles.link}>🌱 Catálogo</NavLink>
          <NavLink to="/perfil" className={styles.link}>👤 Perfil</NavLink>
          <button onClick={handleLogout} className={styles.logoutBtn}>Salir</button>
        </>
      ) : (
        <>
          <NavLink to="/catalogo" className={styles.link}>🌱 Catálogo</NavLink>
          <NavLink to="/login" className={styles.link}>🔑 Entrar</NavLink>
        </>
      )}
    </nav>
  );
}