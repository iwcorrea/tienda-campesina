const QUEUE_KEY = 'offlineQueue';

function getQueue() {
  try {
    return JSON.parse(localStorage.getItem(QUEUE_KEY)) || [];
  } catch {
    return [];
  }
}

function saveQueue(queue) {
  localStorage.setItem(QUEUE_KEY, JSON.stringify(queue));
}

/**
 * Agrega una acción a la cola offline.
 * accion: { type: 'pickup'|'deliver', transportId, ... }
 */
export function enqueue(accion) {
  const queue = getQueue();
  queue.push({ ...accion, timestamp: Date.now() });
  saveQueue(queue);
}

/**
 * Retorna la cantidad de acciones pendientes.
 */
export function pendingCount() {
  return getQueue().length;
}

/**
 * Intenta procesar todas las acciones pendientes.
 * Llama a la función ejecutora correspondiente.
 * execFn(type, transportId) => Promise
 */
export async function processQueue(execFn) {
  const queue = getQueue();
  if (queue.length === 0) return;

  const remaining = [];
  for (const item of queue) {
    try {
      await execFn(item.type, item.transportId);
    } catch {
      remaining.push(item);
    }
  }
  saveQueue(remaining);
}

/**
 * Escucha eventos de conexión y reintenta automáticamente.
 * execFn: igual que en processQueue.
 * callback: se llama cada vez que la cola cambia de tamaño.
 */
export function listenConnectivity(execFn, callback) {
  async function tryProcess() {
    await processQueue(execFn);
    callback(pendingCount());
  }

  window.addEventListener('online', tryProcess);
  // también se puede llamar al montar el componente
  return () => window.removeEventListener('online', tryProcess);
}