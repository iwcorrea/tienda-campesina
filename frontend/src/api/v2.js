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

export async function fetchOrderTimeline(orderId) {
  return request(`/orders/${orderId}/timeline`);
}