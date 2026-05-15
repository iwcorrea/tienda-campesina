import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

// Wrappers con feature flag (migración v2)
import PedidoDetailWrapper from '../screens/pedido/PedidoDetailWrapper';
import TransportHomeWrapper from '../screens/transport/TransportHomeWrapper';

// Pantallas legacy (ajusta las rutas según tu estructura real)
// import Home from '../screens/Home';
// import Catalogo from '../screens/Catalogo';
// import Carrito from '../screens/Carrito';
// import Checkout from '../screens/Checkout';
// import Login from '../screens/Login';
// import Registro from '../screens/Registro';

// Placeholder para pantallas legacy no migradas aún
const Placeholder = ({ nombre }) => (
  <div style={{ padding: 16, fontFamily: 'system-ui' }}>
    <h2>{nombre}</h2>
    <p>Pantalla en versión legacy.</p>
  </div>
);

function NotFound() {
  return (
    <div style={{ padding: 16, textAlign: 'center' }}>
      <h2>Página no encontrada</h2>
      <p>La ruta que buscas no existe.</p>
    </div>
  );
}

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        {/* ── Rutas legacy comunes ─────────────────────────── */}
        <Route path="/" element={<Placeholder nombre="Inicio" />} />
        <Route path="/catalogo" element={<Placeholder nombre="Catálogo" />} />
        <Route path="/carrito" element={<Placeholder nombre="Carrito" />} />
        <Route path="/pagos/checkout/:pedido_id" element={<Placeholder nombre="Checkout" />} />
        <Route path="/pagos/exito/:pago_id" element={<Placeholder nombre="Pago exitoso" />} />
        <Route path="/auth/login" element={<Placeholder nombre="Iniciar sesión" />} />
        <Route path="/auth/register" element={<Placeholder nombre="Registro" />} />

        {/* ── Detalle de pedido (wrapper v1/v2) ─────────────── */}
        <Route path="/pedidos/:id" element={<PedidoDetailWrapper />} />

        {/* ── Transportista (wrapper v1/v2) ─────────────────── */}
        <Route path="/transportista" element={<TransportHomeWrapper />} />

        {/* ── Notificaciones (legacy) ────────────────────────── */}
        <Route path="/notificaciones" element={<Placeholder nombre="Notificaciones" />} />

        {/* ── Perfil (legacy) ────────────────────────────────── */}
        <Route path="/perfil" element={<Placeholder nombre="Perfil" />} />

        {/* ── Admin (legacy) ─────────────────────────────────── */}
        <Route path="/admin/*" element={<Placeholder nombre="Panel de administración" />} />

        {/* ── Fallback ──────────────────────────────────────── */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}