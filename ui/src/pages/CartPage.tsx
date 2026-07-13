import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCart } from '../hooks/useCart';
import { useAuth } from '../hooks/useAuth';
import { api, ApiError } from '../api/client';
import type { Order } from '../types';
import './CartPage.css';

export function CartPage() {
  const { lines, updateQuantity, removeFromCart, clearCart, totalEur } = useCart();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [isPlacing, setIsPlacing] = useState(false);

  async function handleCheckout() {
    if (!user) {
      navigate('/login');
      return;
    }
    setError(null);
    setIsPlacing(true);
    try {
      const order = await api.post<Order>('/orders', {
        items: lines.map((line) => ({ fruit_sku: line.fruit.slug, quantity: line.quantity })),
      });
      clearCart();
      navigate(`/orders?justPlaced=${order.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not place the order. Please try again.');
    } finally {
      setIsPlacing(false);
    }
  }

  if (lines.length === 0) {
    return (
      <div className="container cart-page" data-testid="cart-page">
        <p data-testid="empty-cart-message">Your basket is empty — go pick some fruit!</p>
      </div>
    );
  }

  return (
    <div className="container cart-page" data-testid="cart-page">
      <h1>Your basket</h1>

      <ul className="cart-list">
        {lines.map((line) => (
          <li key={line.fruit.slug} className="cart-line" data-testid="cart-line">
            <span className="cart-line__name" data-testid="cart-line-name">{line.fruit.name}</span>
            <input
              type="number"
              min={1}
              value={line.quantity}
              onChange={(e) => updateQuantity(line.fruit.slug, Number(e.target.value))}
              data-testid="cart-line-quantity"
            />
            <span data-testid="cart-line-subtotal">
              €{((line.fruit.live_price_eur ?? line.fruit.base_price_hint_eur) * line.quantity).toFixed(2)}
            </span>
            <button
              className="btn-secondary cart-line__remove"
              onClick={() => removeFromCart(line.fruit.slug)}
              data-testid="cart-line-remove-button"
            >
              Remove
            </button>
          </li>
        ))}
      </ul>

      <div className="cart-summary">
        <span>Total</span>
        <strong data-testid="cart-total">€{totalEur.toFixed(2)}</strong>
      </div>

      {error && <p className="cart-page__error" role="alert" data-testid="checkout-error">{error}</p>}

      <button
        className="btn-primary cart-page__checkout"
        onClick={handleCheckout}
        disabled={isPlacing}
        data-testid="checkout-button"
      >
        {isPlacing ? 'Placing order…' : user ? 'Place order' : 'Log in to check out'}
      </button>
    </div>
  );
}
