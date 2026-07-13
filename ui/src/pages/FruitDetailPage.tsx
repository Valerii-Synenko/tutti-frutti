import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../api/client';
import { useCart } from '../hooks/useCart';
import type { Fruit } from '../types';
import './FruitDetailPage.css';

export function FruitDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const [fruit, setFruit] = useState<Fruit | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const { addToCart } = useCart();

  useEffect(() => {
    if (!slug) return;
    api
      .get<Fruit>(`/fruits/${slug}`)
      .then(setFruit)
      .catch(() => setError('Fruit not found.'));
  }, [slug]);

  if (error) return <p className="container" data-testid="error-message" role="alert">{error}</p>;
  if (!fruit) return <p className="container" data-testid="loading-indicator">Loading…</p>;

  const price = fruit.live_price_eur ?? fruit.base_price_hint_eur;

  return (
    <div className="container fruit-detail" data-testid="fruit-detail-page">
      <div className="fruit-detail__media">
        {fruit.image_url ? (
          <img src={fruit.image_url} alt={fruit.name} />
        ) : (
          <div className="fruit-detail__media-placeholder" aria-hidden="true">🍇</div>
        )}
      </div>

      <div className="fruit-detail__info">
        <h1 data-testid="fruit-detail-name">{fruit.name}</h1>
        <p className="fruit-detail__origin">{fruit.origin}</p>
        <p className="fruit-detail__price" data-testid="fruit-detail-price">€{price.toFixed(2)}</p>
        <p className="fruit-detail__description">{fruit.description}</p>

        <ul className="fruit-detail__tags">
          {fruit.tags.map((tag) => (
            <li key={tag}>{tag}</li>
          ))}
        </ul>

        {fruit.in_stock === false ? (
          <p className="fruit-detail__out-of-stock" data-testid="out-of-stock-label">
            Currently out of stock
          </p>
        ) : (
          <div className="fruit-detail__actions">
            <label htmlFor="quantity-input" className="visually-hidden">Quantity</label>
            <input
              id="quantity-input"
              type="number"
              min={1}
              max={fruit.quantity_available ?? 99}
              value={quantity}
              onChange={(e) => setQuantity(Number(e.target.value))}
              data-testid="quantity-input"
            />
            <button
              className="btn-primary"
              onClick={() => addToCart(fruit, quantity)}
              data-testid="add-to-cart-button"
            >
              Add {quantity} to basket
            </button>
          </div>
        )}

        {fruit.quantity_available !== null && (
          <p className="fruit-detail__stock" data-testid="stock-count">
            {fruit.quantity_available} in stock
          </p>
        )}
      </div>
    </div>
  );
}
