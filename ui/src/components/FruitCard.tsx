import type { MouseEvent } from 'react';
import { Link } from 'react-router-dom';
import type { Fruit } from '../types';
import { useAuth } from '../hooks/useAuth';
import { useCart } from '../hooks/useCart';
import { api } from '../api/client';
import { TrashIcon } from './icons';
import './FruitCard.css';

export function FruitCard({ fruit, onDeleted }: { fruit: Fruit; onDeleted?: (slug: string) => void }) {
  const { addToCart } = useCart();
  const { user } = useAuth();
  const price = fruit.live_price_eur ?? fruit.base_price_hint_eur;
  const canDelete = user?.is_admin || (!!user && fruit.seller_id === user.id);

  async function handleDelete(e: MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (!window.confirm(`Delete "${fruit.name}"? This cannot be undone.`)) return;
    await api.delete(`/fruits/${fruit._id}`);
    onDeleted?.(fruit.slug);
  }

  return (
    <article className="fruit-card" data-testid="fruit-card" data-fruit-slug={fruit.slug}>
      <Link to={`/fruits/${fruit.slug}`} className="fruit-card__media-link" data-testid="fruit-card-link">
        <div className="fruit-card__media">
          {fruit.image_url ? (
            <img src={fruit.image_url} alt={fruit.name} loading="lazy" />
          ) : (
            <div className="fruit-card__media-placeholder" aria-hidden="true">🍇</div>
          )}
          <span className="fruit-card__price-tag" data-testid="fruit-price-tag">
            €{price.toFixed(2)}
          </span>
          {fruit.is_organic && (
            <span className="fruit-card__organic-badge" data-testid="organic-badge">organic</span>
          )}
          {canDelete && (
            <button
              className="icon-button icon-button--danger fruit-card__delete-btn"
              onClick={handleDelete}
              aria-label={`Delete ${fruit.name}`}
              data-testid="fruit-card-delete-button"
            >
              <TrashIcon />
            </button>
          )}
        </div>
      </Link>

      <div className="fruit-card__body">
        <h3 data-testid="fruit-name">{fruit.name}</h3>
        <p className="fruit-card__origin">{fruit.origin}</p>

        <div className="fruit-card__footer">
          {fruit.in_stock === false ? (
            <span className="fruit-card__out-of-stock" data-testid="out-of-stock-label">Out of stock</span>
          ) : (
            <button
              className="btn-primary fruit-card__add-btn"
              onClick={() => addToCart(fruit)}
              data-testid="add-to-cart-button"
            >
              Add to basket
            </button>
          )}
        </div>
      </div>
    </article>
  );
}
