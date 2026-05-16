const BASE_URL = '/api/v2/modular';

const cache = {
  get(key) {
    try { const item = localStorage.getItem(`v2cache_${key}`); return item ? JSON.parse(item) : null; } catch { return null; }
  },
  set(key, data) {
    try { localStorage.setItem(`v2cache_${key}`, JSON.stringify(data)); } catch {}
  }
};

async function request(url, options = {}) {
  const fullUrl = `${BASE_URL}${url}`;
  try {
    const response = await fetch(fullUrl, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    if (!options.method || options.method === 'GET') cache.set(url, data);
    return data;
  } catch (error) {
    console.warn('[api/v2] Error, intentando cache:', error);
    const cached = cache.get(url);
    if (cached) return { ...cached, _fromCache: true };
    throw error;
  }
}

// ─── Auth ────────────────────────────────────────
export async function loginV2(email, password) {
  const formData = new URLSearchParams();
  formData.append('email', email);
  formData.append('password', password);
  return request('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: formData.toString(),
  });
}

export async function registerV2(email, password, tipo, nombre, telefono = '', region = '') {
  const formData = new URLSearchParams();
  formData.append('email', email);
  formData.append('password', password);
  formData.append('tipo', tipo);
  formData.append('nombre', nombre);
  formData.append('telefono', telefono);
  formData.append('region', region);
  return request('/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: formData.toString(),
  });
}

export async function logoutV2() {
  return request('/auth/logout', { method: 'POST' });
}

// ─── Users ───────────────────────────────────────
export async function fetchProfile() {
  return request('/users/me');
}

export async function updateProfile(data) {
  return request('/users/me', { method: 'PATCH', body: JSON.stringify(data) });
}

// ─── Products ────────────────────────────────────
export async function fetchProducts(query = '', region = '') {
  const params = new URLSearchParams();
  if (query) params.append('q', query);
  if (region) params.append('region', region);
  return request(`/products?${params.toString()}`);
}

export async function fetchProduct(productId) {
  return request(`/products/${productId}`);
}

// ─── Orders ──────────────────────────────────────
export async function fetchOrders(estado = '', region = '') {
  const params = new URLSearchParams();
  if (estado) params.append('estado', estado);
  if (region) params.append('region', region);
  return request(`/orders?${params.toString()}`);
}

export async function fetchOrder(orderId) {
  return request(`/orders/${orderId}`);
}

export async function fetchOrderTimeline(orderId) {
  return request(`/orders/${orderId}/timeline`);
}

export async function createOrder() {
  return request('/orders', { method: 'POST' });
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

export async function confirmOrder(orderId) {
  return request(`/orders/${orderId}/confirm`, { method: 'POST' });
}

// ─── Transport ───────────────────────────────────
export async function fetchTransportAssignments() {
  return request('/transport');
}

export async function pickupTransport(transportId) {
  return request(`/transport/${transportId}/pickup`, { method: 'POST' });
}

export async function deliverTransport(transportId) {
  return request(`/transport/${transportId}/deliver`, { method: 'POST' });
}

// ─── Dashboard ───────────────────────────────────
export async function fetchDashboard() {
  return request('/dashboard');
}