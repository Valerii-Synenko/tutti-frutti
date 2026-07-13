import { Routes, Route } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { ChatWidget } from './components/ChatWidget';
import { CataloguePage } from './pages/CataloguePage';
import { FruitDetailPage } from './pages/FruitDetailPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { CartPage } from './pages/CartPage';
import { OrdersPage } from './pages/OrdersPage';
import { AuthProvider } from './hooks/useAuth';
import { CartProvider } from './hooks/useCart';

export default function App() {
  return (
    <AuthProvider>
      <CartProvider>
        <Navbar />
        <main>
          <Routes>
            <Route path="/" element={<CataloguePage />} />
            <Route path="/fruits/:slug" element={<FruitDetailPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/cart" element={<CartPage />} />
            <Route path="/orders" element={<OrdersPage />} />
          </Routes>
        </main>
        <ChatWidget />
      </CartProvider>
    </AuthProvider>
  );
}
