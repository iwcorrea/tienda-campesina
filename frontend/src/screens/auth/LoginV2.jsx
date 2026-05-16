import React, { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { loginV2 } from '../../api/v2';
import { AuthContext } from '../../context/AuthContext';
import styles from './Auth.module.css';

export default function LoginV2() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { setUser } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const user = await loginV2(email, password);
      setUser(user);
      const redirect = new URLSearchParams(window.location.search).get('redirect') || '/mis-pedidos';
      navigate(redirect);
    } catch {
      setError('Correo o contraseña incorrectos');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>🌿 Iniciar sesión</h2>
      <form onSubmit={handleSubmit} className={styles.form}>
        <label className={styles.label}>
          Correo electrónico
          <input type="email" className={styles.input} value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <label className={styles.label}>
          Contraseña
          <input type="password" className={styles.input} value={password} onChange={(e) => setPassword(e.target.value)} required />
        </label>
        {error && <p className={styles.error}>{error}</p>}
        <button type="submit" className={styles.button} disabled={loading}>
          {loading ? 'Entrando...' : 'Entrar'}
        </button>
      </form>
      <p className={styles.link}>¿No tienes cuenta? <a href="/register">Registrarme</a></p>
    </div>
  );
}