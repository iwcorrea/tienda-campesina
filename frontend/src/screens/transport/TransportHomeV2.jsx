import React, { useEffect, useState, useCallback } from 'react';
import {
  fetchTransportAssignments,
  pickupTransport,
  deliverTransport,
} from '../../api/v2';
import {
  enqueue,
  pendingCount,
  processQueue,
  listenConnectivity,
} from '../../utils/offlineQueue';
import styles from './TransportHomeV2.module.css';

const ESTADO_MAP = {
  pendiente_aceptacion: { label: 'Asignado', color: '#757575', bg: '#f5f5f5', icon: '⏳' },
  aceptado: { label: 'Por recoger', color: '#F9A825', bg: '#fff8e1', icon: '🚶' },
  recogido: { label: 'En camino', color: '#F9A825', bg: '#fff8e1', icon: '🚚' },
  en_transito: { label: 'En camino', color: '#F9A825', bg: '#fff8e1', icon: '🚚' },
  entregado: { label: 'Entregado', color: '#2E7D32', bg: '#e8f5e9', icon: '✅' },
  cancelado: { label: 'Cancelado', color: '#757575', bg: '#f5f5f5', icon: '❌' },
};

export default function TransportHomeV2() {
  const [viajes, setViajes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [offline, setOffline] = useState(!navigator.onLine);
  const [pending, setPending] = useState(pendingCount());
  const [processing, setProcessing] = useState({}); // transportId -> true

  const loadAssignments = useCallback(async () => {
    try {
      const data = await fetchTransportAssignments();
      setViajes(data);
    } catch {
      // Si falla, se queda con los datos actuales (o vacío)
    } finally {
      setLoading(false);
    }
  }, []);

  // Función que ejecuta una acción offline genérica
  const execOfflineAction = useCallback(async (item) => {
    if (item.type === 'pickup') {
      await pickupTransport(item.transportId);
    } else if (item.type === 'deliver') {
      await deliverTransport(item.transportId);
    }
  }, []);

  // Procesar cola offline
  const processOffline = useCallback(async () => {
    await processQueue(execOfflineAction);
    setPending(pendingCount());
  }, [execOfflineAction]);

  // Listener de conectividad
  useEffect(() => {
    const cleanup = listenConnectivity(execOfflineAction, (newPending) => setPending(newPending));
    return cleanup;
  }, [execOfflineAction]);

  // Carga inicial y polling cada 30s
  useEffect(() => {
    loadAssignments();
    const interval = setInterval(loadAssignments, 30000);
    return () => clearInterval(interval);
  }, [loadAssignments]);

  // Monitorear estado online/offline
  useEffect(() => {
    const handleOnline = () => { setOffline(false); processOffline(); };
    const handleOffline = () => setOffline(true);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [processOffline]);

  const handleAction = async (transportId, actionType) => {
    setProcessing((prev) => ({ ...prev, [transportId]: true }));
    try {
      if (actionType === 'pickup') {
        await pickupTransport(transportId);
      } else if (actionType === 'deliver') {
        await deliverTransport(transportId);
      }
      await loadAssignments(); // refrescar lista
    } catch (err) {
      if (!navigator.onLine) {
        // Encolar para envío posterior
        enqueue({ type: actionType, transportId });
        setPending(pendingCount());
      } else {
        alert('Ocurrió un error. Intenta de nuevo.');
      }
    } finally {
      setProcessing((prev) => ({ ...prev, [transportId]: false }));
    }
  };

  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.skeleton} />
        <div className={styles.skeleton} />
      </div>
    );
  }

  return (
    <div className={styles.container}>
      {offline && (
        <div className={styles.offlineBanner}>
          Sin conexión {pending > 0 && `– ${pending} acciones pendientes`}
        </div>
      )}
      <h2 className={styles.title}>Mis viajes</h2>
      {viajes.length === 0 ? (
        <div className={styles.empty}>
          <span className={styles.emptyIcon}>🚛</span>
          <p>No tienes viajes pendientes</p>
        </div>
      ) : (
        <div className={styles.list}>
          {viajes.map((viaje) => {
            const estadoInfo = ESTADO_MAP[viaje.estado] || ESTADO_MAP['pendiente_aceptacion'];
            const isProcessing = processing[viaje.id];
            const showPickup = viaje.estado === 'aceptado';
            const showDeliver = viaje.estado === 'recogido' || viaje.estado === 'en_transito';
            const isCompleted = viaje.estado === 'entregado';
            return (
              <div
                key={viaje.id}
                className={styles.card}
                style={{ borderLeftColor: estadoInfo.color, backgroundColor: estadoInfo.bg }}
              >
                <div className={styles.cardHeader}>
                  <span className={styles.icon}>{estadoInfo.icon}</span>
                  <span className={styles.statusText}>{estadoInfo.label}</span>
                </div>
                <div className={styles.cardBody}>
                  <p><strong>Pedido:</strong> {viaje.pedido_id?.slice(0, 8)}</p>
                  <p><strong>Origen:</strong> {viaje.detalles?.origen || 'No especificado'}</p>
                  <p><strong>Destino:</strong> {viaje.detalles?.destino || 'No especificado'}</p>
                </div>
                {!isCompleted && (
                  <div className={styles.actions}>
                    {showPickup && (
                      <button
                        className={styles.actionBtn}
                        disabled={isProcessing}
                        onClick={() => handleAction(viaje.id, 'pickup')}
                      >
                        {isProcessing ? 'Enviando...' : 'Llegué al punto de recogida'}
                      </button>
                    )}
                    {showDeliver && (
                      <button
                        className={styles.actionBtn}
                        disabled={isProcessing}
                        onClick={() => handleAction(viaje.id, 'deliver')}
                      >
                        {isProcessing ? 'Enviando...' : 'Ya entregué el pedido'}
                      </button>
                    )}
                  </div>
                )}
                {isCompleted && (
                  <div className={styles.completed}>Entregado ✅</div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}