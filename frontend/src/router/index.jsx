import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import PedidoDetailWrapper from '../screens/pedido/PedidoDetailWrapper';
// Importa otras pantallas legacy que ya tengas...
// import Home from '../screens/Home';
// import Catalogo from '../screens/Catalogo';
// ...

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Rutas legacy existentes */}
        {/* <Route path="/" element={<Home />} /> */}
        {/* <Route path="/catalogo" element={<Catalogo />} /> */}

        {/* Detalle de pedido con wrapper para feature flag */}
        <Route path="/pedidos/:id" element={<PedidoDetailWrapper />} />

        {/* Otras rutas legacy... */}
        {/* <Route path="*" element={<NotFound />} /> */}
      </Routes>
    </BrowserRouter>
  );
}