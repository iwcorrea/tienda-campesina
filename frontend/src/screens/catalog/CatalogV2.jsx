import React, { useEffect, useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { fetchProducts } from '../../api/v2';
import styles from './CatalogV2.module.css';

export default function CatalogV2() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchProducts();
      // Acepta array directo o un objeto con propiedad data
      const list = Array.isArray(data) ? data : (data?.data || []);
      setProducts(list);
    } catch (err) {
      console.error('Error al cargar productos:', err);
      setError('No pudimos cargar las cosechas. Revisa tu conexión.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const filtered = useMemo(() => {
    if (!searchTerm.trim()) return products;
    const term = searchTerm.toLowerCase();
    return products.filter(
      p =>
        p.nombre.toLowerCase().includes(term) ||
        (p.descripcion && p.descripcion.toLowerCase().includes(term))
    );
  }, [products, searchTerm]);

  // ── Estados de UI ──────────────────────────
  if (loading) {
    return (
      <div className={styles.container}>
        <h2 className={styles.title}>🌱 Cosechas disponibles</h2>
        <div className={styles.skeleton} />
        <div className={styles.skeleton} />
        <div className={styles.skeleton} />
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.container}>
        <p className={styles.error}>{error}</p>
        <button className={styles.retryBtn} onClick={load}>
          Reintentar
        </button>
      </div>
    );
  }

  if (products.length === 0) {
    return (
      <div className={styles.container}>
        <h2 className={styles.title}>🌱 Cosechas disponibles</h2>
        <p className={styles.empty}>Aún no hay cosechas disponibles. Vuelve pronto.</p>
      </div>
    );
  }

  // ── Catálogo con búsqueda local ────────────
  return (
    <div className={styles.container}>
      <h2 className={styles.title}>🌱 Cosechas disponibles</h2>

      {/* Barra de búsqueda decorativa (filtro local) */}
      <div className={styles.searchBar}>
        <input
          type="text"
          placeholder="Buscar cosecha..."
          className={styles.searchInput}
          value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
        />
        {searchTerm && (
          <button className={styles.clearBtn} onClick={() => setSearchTerm('')}>
            ✕
          </button>
        )}
      </div>

      {filtered.length === 0 ? (
        <p className={styles.empty}>Ninguna cosecha coincide con "{searchTerm}"</p>
      ) : (
        <div className={styles.grid}>
          {filtered.map(p => (
            <Link to={`/producto/${p.id}`} key={p.id} className={styles.card}>
              <img
                src={p.imagen_url || '/placeholder.png'}
                alt={p.nombre}
                className={styles.image}
                loading="lazy"
              />
              <div className={styles.info}>
                <span className={styles.name}>{p.nombre}</span>
                <span className={styles.price}>
                  $ {p.precio?.toLocaleString()} / {p.tipo_precio || 'kg'}
                </span>
                <span className={styles.producer}>
                  {p.asociacion?.nombre || 'Productor local'}
                </span>
                {p.valoracion_promedio != null && (
                  <span className={styles.rating}>
                    {'★'.repeat(Math.round(p.valoracion_promedio))}{' '}
                    {p.valoracion_promedio}
                  </span>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}