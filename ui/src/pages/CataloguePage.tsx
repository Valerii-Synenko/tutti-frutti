import { useEffect, useMemo, useState } from 'react';
import { FruitCard } from '../components/FruitCard';
import type { Fruit } from '../types';
import './CataloguePage.css';

const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL ?? 'http://localhost:8080';
const MAX_PRICE = 10;

interface Filters {
  organicOnly: boolean;
  inStockOnly: boolean;
  maxPrice: number;
  tags: Set<string>;
  origins: Set<string>;
}

const DEFAULT_FILTERS: Filters = {
  organicOnly: false,
  inStockOnly: false,
  maxPrice: MAX_PRICE,
  tags: new Set(),
  origins: new Set(),
};

function applyFilters(fruits: Fruit[], f: Filters): Fruit[] {
  return fruits.filter((fruit) => {
    const price = fruit.live_price_eur ?? fruit.base_price_hint_eur;
    if (f.organicOnly && !fruit.is_organic) return false;
    if (f.inStockOnly && !fruit.in_stock) return false;
    if (price > f.maxPrice) return false;
    if (f.tags.size > 0 && !fruit.tags.some((t) => f.tags.has(t))) return false;
    if (f.origins.size > 0 && !f.origins.has(fruit.origin)) return false;
    return true;
  });
}

export function CataloguePage() {
  const [fruits, setFruits] = useState<Fruit[]>([]);
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS);

  useEffect(() => {
    const controller = new AbortController();
    setIsLoading(true);
    setError(null);

    const params = new URLSearchParams();
    if (query.trim()) params.set('q', query.trim());

    fetch(`${GATEWAY_URL}/fruits?${params.toString()}`, { signal: controller.signal })
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load fruits');
        return res.json();
      })
      .then((data: Fruit[]) => setFruits(data))
      .catch((err) => {
        if (err.name !== 'AbortError') setError('Could not load the market right now.');
      })
      .finally(() => setIsLoading(false));

    return () => controller.abort();
  }, [query]);

  const allTags = useMemo(() => {
    const s = new Set<string>();
    fruits.forEach((f) => f.tags.forEach((t) => s.add(t)));
    return [...s].sort();
  }, [fruits]);

  const allOrigins = useMemo(() => {
    const s = new Set<string>();
    fruits.forEach((f) => { if (f.origin) s.add(f.origin); });
    return [...s].sort();
  }, [fruits]);

  const displayed = useMemo(() => applyFilters(fruits, filters), [fruits, filters]);

  const activeCount =
    (filters.organicOnly ? 1 : 0) +
    (filters.inStockOnly ? 1 : 0) +
    (filters.maxPrice < MAX_PRICE ? 1 : 0) +
    filters.tags.size +
    filters.origins.size;

  function toggleTag(tag: string) {
    setFilters((prev) => {
      const next = new Set(prev.tags);
      next.has(tag) ? next.delete(tag) : next.add(tag);
      return { ...prev, tags: next };
    });
  }

  function toggleOrigin(origin: string) {
    setFilters((prev) => {
      const next = new Set(prev.origins);
      next.has(origin) ? next.delete(origin) : next.add(origin);
      return { ...prev, origins: next };
    });
  }

  return (
    <div>
      <section className="hero" data-testid="hero-section">
        <div className="container hero__inner">
          <h1 data-testid="hero-title">Fresh fruit, straight from the crate.</h1>
          <p className="hero__subtitle">Tutti Frutti - Life is sweet!</p>
          <div className="hero__search">
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search for mango, figs, berries…"
              aria-label="Search fruit"
              data-testid="search-input"
            />
          </div>
        </div>
      </section>

      <section className="container catalogue-layout">
        <aside className="catalogue-sidebar">
          <div className="sidebar-header">
            <span className="sidebar-title">Filters</span>
            {activeCount > 0 && (
              <button className="sidebar-reset" onClick={() => setFilters(DEFAULT_FILTERS)}>
                Clear ({activeCount})
              </button>
            )}
          </div>

          <div className="sidebar-section">
            <label className="sidebar-check">
              <input
                type="checkbox"
                checked={filters.organicOnly}
                onChange={(e) => setFilters((p) => ({ ...p, organicOnly: e.target.checked }))}
              />
              Organic only
            </label>
            <label className="sidebar-check">
              <input
                type="checkbox"
                checked={filters.inStockOnly}
                onChange={(e) => setFilters((p) => ({ ...p, inStockOnly: e.target.checked }))}
              />
              In stock only
            </label>
          </div>

          <div className="sidebar-section">
            <p className="sidebar-section-title">Max price</p>
            <div className="sidebar-price-row">
              <span>€0</span>
              <span className="sidebar-price-val">
                {filters.maxPrice >= MAX_PRICE ? `€${MAX_PRICE}+` : `€${filters.maxPrice.toFixed(2)}`}
              </span>
            </div>
            <input
              type="range"
              min={0}
              max={MAX_PRICE}
              step={0.5}
              value={filters.maxPrice}
              onChange={(e) => setFilters((p) => ({ ...p, maxPrice: parseFloat(e.target.value) }))}
              className="sidebar-range"
            />
          </div>

          {allOrigins.length > 0 && (
            <div className="sidebar-section">
              <p className="sidebar-section-title">Origin</p>
              {allOrigins.map((origin) => (
                <label key={origin} className="sidebar-check">
                  <input
                    type="checkbox"
                    checked={filters.origins.has(origin)}
                    onChange={() => toggleOrigin(origin)}
                  />
                  {origin}
                </label>
              ))}
            </div>
          )}

          {allTags.length > 0 && (
            <div className="sidebar-section">
              <p className="sidebar-section-title">Tags</p>
              <div className="sidebar-tags">
                {allTags.map((tag) => (
                  <button
                    key={tag}
                    className={`sidebar-tag${filters.tags.has(tag) ? ' sidebar-tag--active' : ''}`}
                    onClick={() => toggleTag(tag)}
                  >
                    {tag}
                  </button>
                ))}
              </div>
            </div>
          )}
        </aside>

        <div className="catalogue-main">
          {isLoading && <p data-testid="loading-indicator">Loading the market stall…</p>}
          {error && <p data-testid="error-message" role="alert">{error}</p>}
          {!isLoading && !error && displayed.length === 0 && (
            <p data-testid="empty-state">No fruit matches your search — try another word.</p>
          )}
          <div className="catalogue-grid" data-testid="fruit-grid">
            {displayed.map((fruit) => (
              <FruitCard key={fruit.slug} fruit={fruit} />
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
