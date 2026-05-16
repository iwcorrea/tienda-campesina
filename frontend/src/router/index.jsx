import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import HomeWrapper from '../screens/home/HomeWrapper';
import CatalogWrapper from '../screens/catalog/CatalogWrapper';
import ProductDetailWrapper from '../screens/product/ProductDetailWrapper';
import DraftOrdersWrapper from '../screens/orders/DraftOrdersWrapper';
import PedidoDetailWrapper from '../screens/pedido/PedidoDetailWrapper';
import TransportHomeWrapper from '../screens/transport/TransportHomeWrapper';
import ProfileWrapper from '../screens/profile/ProfileWrapper';

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomeWrapper />} />
        <Route path="/catalogo" element={<CatalogWrapper />} />
        <Route path="/producto/:id" element={<ProductDetailWrapper />} />
        <Route path="/pedidos/borrador" element={<DraftOrdersWrapper />} />
        <Route path="/pedidos/:id" element={<PedidoDetailWrapper />} />
        <Route path="/transportista" element={<TransportHomeWrapper />} />
        <Route path="/perfil" element={<ProfileWrapper />} />
        <Route path="*" element={<div style={{padding:24, textAlign:'center'}}>Página no encontrada</div>} />
      </Routes>
    </BrowserRouter>
  );
}