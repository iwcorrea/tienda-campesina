import React, { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { registerV2 } from '../../api/v2';
import { AuthContext } from '../../context/AuthContext';
import styles from './Auth.module.css';

export default function RegisterV2() {
  const [nombre, setNombre] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [tipo, setTipo] = useState('persona');
  const [telefono, setTelefono] = useState('');
  const [region, setRegion] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { setUser } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const user = await registerV2(email, password, tipo, nombre, telefono, region);
      setUser(user);
      navigate('/mis-pedidos');
    } catch {
      setError('No se pudo crear la cuenta. Verifica los datos.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>🌱 Registrarme</h2>
      <form onSubmit={handleSubmit} className={styles.form}>
        <label className={styles.label}>
          Tipo de usuario
          <select className={styles.select} value={tipo} onChange={(e) => setTipo(e.target.value)} required>
            <option value="persona">Comprador</option>
            <option value="asociacion">Productor (Asociación)</option>
            <option value="transportista">Transportista</option>
          </select>
        </label>
        <label className={styles.label}>
          Nombre
          <input type="text" className={styles.input} value={nombre} onChange={(e) => setNombre(e.target.value)} required />
        </label>
        <label className={styles.label}>
          Correo electrónico
          <input type="email" className={styles.input} value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <label className={styles.label}>
          Contraseña
          <input type="password" className={styles.input} value={password} onChange={(e) => setPassword(e.target.value)} required />
        </label>
        <label className={styles.label}>
          Teléfono
          <input type="text" className={styles.input} value={telefono} onChange={(e) => setTelefono(e.target.value)} />
        </label>
        <label className={styles.label}>
          Región
          <input type="text" className={styles.input} value={region} onChange={(e) => setRegion(e.target.value)} placeholder="Ej: Cundinamarca" />
        </label>
        {error && <p className={styles.error}>{error}</p>}
        <button type="submit" className={styles.button} disabled={loading}>
          {loading ? 'Creando cuenta...' : 'Crear cuenta'}
        </button>
      </form>
      <p className={styles.link}>¿Ya tienes cuenta? <a href="/login">Iniciar sesión</a></p>
    </div>
  );
}