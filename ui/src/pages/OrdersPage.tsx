import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../api/client';
import type { Order } from '../types';
import './OrdersPage.css';

export function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchParams] = useSearchParams();
  const justPlacedId = searchParams.get('justPlaced');

  useEffect(() => {
    api
      .get<Order[]>('/orders')
      .then(setOrders)
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <div className="container orders-page" data-testid="orders-page">
      <h1>My orders</h1>

      {justPlacedId && (
        <p className="orders-page__confirmation" data-testid="order-confirmation-banner">
          Order placed successfully! 🎉
        </p>
      )}

      {isLoading && <p data-testid="loading-indicator">Loading your orders…</p>}
      {!isLoading && orders.length === 0 && <p data-testid="empty-orders-message">No orders yet.</p>}

      <ul className="orders-list">
        {orders.map((order) => (
          <li key={order.id} className="order-card" data-testid="order-card">
            <div className="order-card__header">
              <span data-testid="order-status">{order.status}</span>
              <span data-testid="order-total">€{order.total_eur.toFixed(2)}</span>
            </div>
            <ul className="order-card__items">
              {order.items.map((item) => (
                <li key={item.fruit_sku} data-testid="order-item">
                  {item.quantity}× {item.fruit_sku} — €{item.unit_price_eur.toFixed(2)} each
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ul>
    </div>
  );
}
