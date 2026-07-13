import { useEffect, useState } from 'react';
import { FruitCard } from '../components/FruitCard';
import type { Fruit } from '../types';
import './CataloguePage.css';

export function CataloguePage() {
  const [fruits, setFruits] = useState<Fruit[]>([]);
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setIsLoading(true);
    setError(null);

    const params = new URLSearchParams();
    if (query.trim()) params.set('q', query.trim());

    fetch(`${import.meta.env.VITE_GATEWAY_URL ?? 'http://localhost:8080'}/fruits?${params.toString()}`, {
      signal: controller.signal,
    })
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

  return (
    <div>
      <section className="hero" data-testid="hero-section">
        <div className="container hero__inner">
          <h1 data-testid="hero-title">Fresh fruit, straight from the crate.</h1>
          <p className="hero__subtitle">
            Tutti Frutti - Life is sweet!
          </p>
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

      <section className="container catalogue-grid-section">
        {isLoading && <p data-testid="loading-indicator">Loading the market stall…</p>}
        {error && <p data-testid="error-message" role="alert">{error}</p>}
        {!isLoading && !error && fruits.length === 0 && (
          <p data-testid="empty-state">No fruit matches your search — try another word.</p>
        )}

        <div className="catalogue-grid" data-testid="fruit-grid">
          {fruits.map((fruit) => (
            <FruitCard key={fruit.slug} fruit={fruit} />
          ))}
        </div>
      </section>
    </div>
  );
}
