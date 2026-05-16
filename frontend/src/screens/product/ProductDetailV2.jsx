import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { fetchProduct } from '../../api/v2';
import styles from './ProductDetailV2.module.css';

export default function ProductDetailV2() {
  const { id } = useParams();
  const [product, setProduct] = useState(null);

  useEffect(() => {
    fetchProduct(id).then(setProduct).catch(() => {});
  }, [id]);

  if (!product) return <div className={styles.loading}>Cargando producto...</div>;

  return (
    <div className={styles.container}>
      <img src={product.imagen_url || '/placeholder.png'} alt={product.nombre} className={styles.image} />
      <h2 className={styles.name}>{product.nombre}</h2>
      <p className={styles.price}>${product.precio?.toLocaleString()} / kg</p>
      <p className={styles.description}>{product.descripcion}</p>
      <p className={styles.producer}>Producido por: {product.asociacion?.nombre}</p>
      <button className={styles.orderBtn}>Iniciar pedido</button>
    </div>
  );
}