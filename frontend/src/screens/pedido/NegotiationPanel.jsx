import React, { useState } from 'react';
import { negotiateOrder } from '../../api/v2';
import { enqueue } from '../../utils/offlineQueue';
import { track } from '../../telemetry/pilot';
import styles from './NegotiationPanel.module.css';

export default function NegotiationPanel({ orderId, currentQuantity, currentPrice, onProposalSuccess }) {
  const [quantity, setQuantity] = useState(currentQuantity || 0);
  const [price, setPrice] = useState(currentPrice || 0);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [offlineQueued, setOfflineQueued] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (quantity <= 0 || price <= 0) {
      setError('Ingresa valores mayores a cero');
      return;
    }
    setError('');
    setSending(true);
    try {
      await negotiateOrder(orderId, quantity, price);
      setOfflineQueued(false);
      track('action_executed', { action: 'propose' });
      onProposalSuccess();
    } catch (err) {
      if (!navigator.onLine) {
        enqueue({ type: 'negotiate', orderId, quantity, price });
        setOfflineQueued(true);
        track('offline_queue_used', { action: 'propose' });
      } else {
        setError('Ocurrió un error. Intenta nuevamente.');
      }
    } finally {
      setSending(false);
    }
  };

  return (
    <div className={styles.panel}>
      <h3 className={styles.title}>Propuesta de negociación</h3>
      <form onSubmit={handleSubmit} className={styles.form}>
        <label className={styles.label}>
          Cantidad (kg)
          <input
            type="number"
            className={styles.input}
            value={quantity}
            onChange={(e) => setQuantity(Number(e.target.value))}
            min="0.1"
            step="0.1"
            required
          />
        </label>
        <label className={styles.label}>
          Precio por kg
          <input
            type="number"
            className={styles.input}
            value={price}
            onChange={(e) => setPrice(Number(e.target.value))}
            min="1"
            step="1"
            required
          />
        </label>
        {error && <p className={styles.error}>{error}</p>}
        {offlineQueued && (
          <p className={styles.offlineMsg}>
            Sin conexión. Propuesta guardada. Se enviará automáticamente.
          </p>
        )}
        <button type="submit" className={styles.button} disabled={sending}>
          {sending ? 'Enviando propuesta...' : 'Proponer'}
        </button>
      </form>
    </div>
  );
}