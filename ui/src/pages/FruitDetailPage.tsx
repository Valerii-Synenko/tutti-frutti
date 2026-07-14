import { useEffect, useState, type FormEvent } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../hooks/useAuth';
import { useCart } from '../hooks/useCart';
import type { Comment, Fruit } from '../types';
import './FruitDetailPage.css';

const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL ?? 'http://localhost:8080';

export function FruitDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const [fruit, setFruit] = useState<Fruit | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [commentBody, setCommentBody] = useState('');
  const [isPosting, setIsPosting] = useState(false);
  const { addToCart } = useCart();
  const { user } = useAuth();
  const isAdmin = user?.email === 'admin@admin.com';

  useEffect(() => {
    if (!slug) return;
    api.get<Fruit>(`/fruits/${slug}`)
      .then(setFruit)
      .catch(() => setError('Fruit not found.'));
    fetch(`${GATEWAY_URL}/fruits/${slug}/comments`)
      .then((r) => r.json())
      .then(setComments)
      .catch(() => {});
  }, [slug]);

  async function handleCommentSubmit(e: FormEvent) {
    e.preventDefault();
    if (!user) {
      navigate('/login');
      return;
    }
    if (!slug || !commentBody.trim()) return;
    setIsPosting(true);
    try {
      const token = localStorage.getItem('tf_access_token');
      const res = await fetch(`${GATEWAY_URL}/fruits/${slug}/comments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ author: user.full_name, body: commentBody.trim() }),
      });
      if (!res.ok) throw new Error();
      const newComment: Comment = await res.json();
      setComments((prev) => [...prev, newComment]);

      setCommentBody('');
    } finally {
      setIsPosting(false);
    }
  }

  async function handleDeleteComment(commentId: string) {
    const token = localStorage.getItem('tf_access_token');
    const res = await fetch(`${GATEWAY_URL}/fruits/${slug}/comments/${commentId}`, {
      method: 'DELETE',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (res.ok) {
      setComments((prev) => prev.filter((c) => c._id !== commentId));
    }
  }

  if (error) return <p className="container" data-testid="error-message" role="alert">{error}</p>;
  if (!fruit) return <p className="container" data-testid="loading-indicator">Loading…</p>;

  const price = fruit.live_price_eur ?? fruit.base_price_hint_eur;

  return (
    <div className="container fruit-detail-page">
      <div className="fruit-detail" data-testid="fruit-detail-page">
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

          {Object.keys(fruit.attributes).length > 0 && (
            <dl className="fruit-detail__attributes">
              {Object.entries(fruit.attributes)
                .filter(([, val]) => val !== null && val !== undefined)
                .map(([key, val]) => (
                  <div key={key} className="fruit-detail__attr-row">
                    <dt>{key.replaceAll('_', ' ')}</dt>
                    <dd>{String(val)}</dd>
                  </div>
                ))}
            </dl>
          )}
        </div>
      </div>

      {/* ---- Comments ---- */}
      <section className="fruit-comments">
        <h2 className="fruit-comments__title">
          Reviews &amp; comments
          {comments.length > 0 && <span className="fruit-comments__count">{comments.length}</span>}
        </h2>

        {comments.length === 0 && (
          <p className="fruit-comments__empty">No comments yet — be the first!</p>
        )}

        <ul className="fruit-comments__list">
          {comments.map((c) => (
            <li key={c._id} className="comment-card">
              <div className="comment-card__header">
                <span className="comment-card__author">{c.author}</span>
                <div className="comment-card__meta">
                  <time className="comment-card__date" dateTime={c.created_at}>
                    {new Date(c.created_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}
                  </time>
                  {(isAdmin || (user && c.user_id === user.id)) && (
                    <button
                      className="comment-card__delete"
                      onClick={() => handleDeleteComment(c._id)}
                      aria-label="Delete comment"
                    >
                      ×
                    </button>
                  )}
                </div>
              </div>
              <p className="comment-card__body">{c.body}</p>
            </li>
          ))}
        </ul>

        <form className="comment-form" onSubmit={handleCommentSubmit}>
          <h3 className="comment-form__title">Leave a comment</h3>
          {user ? (
            <p className="comment-form__author-name">Posting as <strong>{user.full_name}</strong></p>
          ) : (
            <p className="comment-form__login-hint">
              <Link to="/login">Log in</Link> to leave a comment.
            </p>
          )}
          <textarea
            placeholder="What do you think about this fruit?"
            value={commentBody}
            onChange={(e) => setCommentBody(e.target.value)}
            maxLength={1000}
            rows={3}
            className="comment-form__body"
            disabled={!user}
          />
          <button type="submit" className="btn-primary" disabled={isPosting}>
            {isPosting ? 'Posting…' : 'Post comment'}
          </button>
        </form>
      </section>
    </div>
  );
}
