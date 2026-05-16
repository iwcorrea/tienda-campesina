import React, { useEffect, useState } from 'react';
import { fetchProducts } from '../../api/v2';
import FeedbackEmoji from '../../components/FeedbackEmoji';
import styles from './CatalogV2.module.css';

export default function CatalogV2() {
  const [products, setProducts] = useState([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);

  const load = async (search = '') => {
    setLoading(true);
    try {
      const data = await fetchProducts(search);
      setProducts(data);
    } catch {} finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    load(query);
  };

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>Cosechas disponibles</h2>
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
      {loading ? (
        <div className={styles.skeleton}>Cargando...</div>
      ) : (
        <div className={styles.grid}>
          {products.map((p) => (
            <a key={p.id} href={`/producto/${p.id}`} className={styles.card}>
              <img src={p.imagen_url || '/placeholder.png'} alt={p.nombre} className={styles.image} />
              <div className={styles.info}>
                <span className={styles.name}>{p.nombre}</span>
                <span className={styles.price}>${p.precio?.toLocaleString()}</span>
                <span className={styles.producer}>{p.asociacion?.nombre || 'Productor'}</span>
              </div>
            </a>
          ))}
        </div>
      )}
      <FeedbackEmoji screenName="catalog" />
    </div>
  );
}