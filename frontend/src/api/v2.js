const BASE_URL = '/api/v2/modular';

const cache = {
  get(key) {
    try {
      const item = localStorage.getItem(`v2cache_${key}`);
      return item ? JSON.parse(item) : null;
    } catch {
      return null;
    }
  },
  set(key, data) {
    try {
      localStorage.setItem(`v2cache_${key}`, JSON.stringify(data));
    } catch { /* ignorar */ }
  }
};

async function request(url, options = {}) {
  const fullUrl = `${BASE_URL}${url}`;
  try {
    const response = await fetch(fullUrl, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    if (!options.method || options.method === 'GET') {
      cache.set(url, data);
    }
    return data;
  } catch (error) {
    console.warn('[api/v2] Error, intentando cache:', error);
    const cached = cache.get(url);
    if (cached) {
      return { ...cached, _fromCache: true };
    }
    throw error;
  }
}

// ─── Pedidos ───────────────────────────────────────
export async function fetchOrderTimeline(orderId) {
  return request(`/orders/${orderId}/timeline`);
}

export async function fetchOrder(orderId) {
  return request(`/orders/${orderId}`);
}

export async function negotiateOrder(orderId, proposedQuantity, proposedPricePerKg) {
  return request(`/orders/${orderId}/negotiate`, {
    method: 'POST',
    body: JSON.stringify({
      proposed_quantity: proposedQuantity,
      proposed_price_per_kg: proposedPricePerKg,
    }),
  });
}

// ─── Transporte ─────────────────────────────────────
export async function fetchTransportAssignments() {
  return request('/transport');
}

export async function pickupTransport(transportId) {
  return request(`/transport/${transportId}/pickup`, { method: 'POST' });
}

export async function deliverTransport(transportId) {
  return request(`/transport/${transportId}/deliver`, { method: 'POST' });
}