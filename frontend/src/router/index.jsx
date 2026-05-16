import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import NavBar from '../components/NavBar';
import LoginV2 from '../screens/auth/LoginV2';
import RegisterV2 from '../screens/auth/RegisterV2';
import CatalogWrapper from '../screens/catalog/CatalogWrapper';
import ProductDetailWrapper from '../screens/product/ProductDetailWrapper';
import OrdersListV2 from '../screens/orders/OrdersListV2';
import PedidoDetailWrapper from '../screens/pedido/PedidoDetailWrapper';
import TransportHomeWrapper from '../screens/transport/TransportHomeWrapper';
import ProfileWrapper from '../screens/profile/ProfileWrapper';

function Layout({ children }) {
  return (
    <div style={{ paddingBottom: 70 }}>
      {children}
      <NavBar />
    </div>
  );
}

export default function AppRouter() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Navigate to="/catalogo" />} />
            <Route path="/login" element={<LoginV2 />} />
            <Route path="/register" element={<RegisterV2 />} />
            <Route path="/catalogo" element={<CatalogWrapper />} />
            <Route path="/producto/:id" element={<ProductDetailWrapper />} />
            <Route path="/mis-pedidos" element={<OrdersListV2 />} />
            <Route path="/pedido/:id" element={<PedidoDetailWrapper />} />
            <Route path="/transportista" element={<TransportHomeWrapper />} />
            <Route path="/perfil" element={<ProfileWrapper />} />
            <Route path="*" element={<div style={{ padding: 24, textAlign: 'center' }}>Página no encontrada</div>} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </AuthProvider>
  );
}