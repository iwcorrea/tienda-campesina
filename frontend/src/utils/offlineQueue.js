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
 * item: objeto arbitrario que guardaremos (type, orderId, quantity, etc.)
 */
export function enqueue(item) {
  const queue = getQueue();
  queue.push({ ...item, timestamp: Date.now() });
  saveQueue(queue);
}

export function pendingCount() {
  return getQueue().length;
}

/**
 * Procesa todas las acciones pendientes usando la función ejecutora dada.
 * execFn recibe el objeto completo guardado en la cola.
 */
export async function processQueue(execFn) {
  const queue = getQueue();
  if (queue.length === 0) return;

  const remaining = [];
  for (const item of queue) {
    try {
      await execFn(item);
    } catch {
      remaining.push(item);
    }
  }
  saveQueue(remaining);
}

/**
 * Escucha eventos de conexión y reintenta automáticamente.
 * execFn: igual que en processQueue.
 * callback: se llama con el número de pendientes después de cada intento.
 * Retorna función para limpiar el listener.
 */
export function listenConnectivity(execFn, callback) {
  async function tryProcess() {
    await processQueue(execFn);
    callback(pendingCount());
  }

  window.addEventListener('online', tryProcess);
  return () => window.removeEventListener('online', tryProcess);
}