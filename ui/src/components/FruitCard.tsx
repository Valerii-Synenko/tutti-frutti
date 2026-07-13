import { Link } from 'react-router-dom';
import type { Fruit } from '../types';
import { useCart } from '../hooks/useCart';
import './FruitCard.css';

export function FruitCard({ fruit }: { fruit: Fruit }) {
  const { addToCart } = useCart();
  const price = fruit.live_price_eur ?? fruit.base_price_hint_eur;

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
