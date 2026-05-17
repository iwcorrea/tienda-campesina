import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { fetchProducts } from '../../api/v2';
import styles from './CatalogV2.module.css';

export default function CatalogV2() {
  const [products, setProducts] = useState([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = async (search = '') => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchProducts(search);
      // Asegurarse de que data sea un array
      const list = Array.isArray(data) ? data : (data?.data || []);
      setProducts(list);
    } catch (err) {
      console.error('Error al cargar productos:', err);
      setError('No se pudieron cargar los productos.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    load(query);
  };

  if (loading) {
    return <div className={styles.container}>Cargando cosechas...</div>;
  }

  if (error) {
    return (
      <div className={styles.container}>
        <p>{error}</p>
        <button onClick={() => load(query)}>Reintentar</button>
      </div>
    );
  }

  if (products.length === 0) {
    return (
      <div className={styles.container}>
        <h2>🌱 Cosechas disponibles</h2>
        <form onSubmit={handleSearch} className={styles.searchForm}>
          <input
            type="text"
            placeholder="Buscar producto..."
            className={styles.searchInput}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button type="submit" className={styles.searchBtn}>Buscar</button>
        </form>
        <p className={styles.empty}>No hay productos todavía. ¡Sé el primero en publicar!</p>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>🌱 Cosechas disponibles</h2>
      <form onSubmit={handleSearch} className={styles.searchForm}>
        <input
          type="text"
          placeholder="Buscar producto..."
          className={styles.searchInput}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit" className={styles.searchBtn}>Buscar</button>
      </form>
      <div className={styles.grid}>
        {products.map((p) => (
          <Link to={`/producto/${p.id}`} key={p.id} className={styles.card}>
            <img
              src={p.imagen_url || '/placeholder.png'}
              alt={p.nombre}
              className={styles.image}
            />
            <div className={styles.info}>
              <span className={styles.name}>{p.nombre}</span>
              <span className={styles.price}>
                ${p.precio?.toLocaleString()} / {p.tipo_precio || 'kg'}
              </span>
              <span className={styles.producer}>
                {p.asociacion?.nombre || 'Productor local'}
              </span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}