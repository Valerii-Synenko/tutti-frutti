import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api, ApiError } from '../api/client';
import { useAuth } from '../hooks/useAuth';
import type { Fruit, FruitCreateInput } from '../types';
import { CheckIcon, PlusIcon, ShieldIcon, StoreIcon, TrashIcon, UserIcon, XIcon } from '../components/icons';
import './CabinetPage.css';

function slugify(value: string): string {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '');
}

const EMPTY_FRUIT_FORM = {
  name: '',
  slug: '',
  description: '',
  origin: '',
  is_organic: false,
  tags: '',
  seasonal_months: '',
  image_url: '',
  base_price_hint_eur: '0',
};

function statusLabel(status: Fruit['status']): string {
  if (status === 'approved') return 'On the shelf';
  if (status === 'rejected') return 'Rejected';
  return 'Awaiting moderation';
}

function FruitStatusBadge({ status }: { status: Fruit['status'] }) {
  return (
    <span className={`fruit-status-badge fruit-status-badge--${status}`} data-testid="fruit-status-badge">
      {statusLabel(status)}
    </span>
  );
}

export function CabinetPage() {
  const { user, isLoading, updateProfile, becomeSeller } = useAuth();
  const navigate = useNavigate();

  // ---- Profile form ----
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [profileMessage, setProfileMessage] = useState<string | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);

  // ---- Seller state ----
  const [isBecomingSeller, setIsBecomingSeller] = useState(false);
  const [myFruits, setMyFruits] = useState<Fruit[]>([]);
  const [isLoadingMyFruits, setIsLoadingMyFruits] = useState(false);
  const [fruitForm, setFruitForm] = useState(EMPTY_FRUIT_FORM);
  const [isCreatingFruit, setIsCreatingFruit] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [slugTouched, setSlugTouched] = useState(false);

  // ---- Admin moderation state ----
  const [pendingFruits, setPendingFruits] = useState<Fruit[]>([]);
  const [isLoadingPending, setIsLoadingPending] = useState(false);
  const [moderationError, setModerationError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && !user) {
      navigate('/login');
    }
  }, [isLoading, user, navigate]);

  useEffect(() => {
    if (user) {
      setFullName(user.full_name);
      setEmail(user.email);
    }
  }, [user]);

  const loadMyFruits = useCallback(() => {
    if (!user?.is_seller) return;
    setIsLoadingMyFruits(true);
    api.get<Fruit[]>('/fruits/mine')
      .then(setMyFruits)
      .catch(() => {})
      .finally(() => setIsLoadingMyFruits(false));
  }, [user?.is_seller]);

  const loadPendingFruits = useCallback(() => {
    if (!user?.is_admin) return;
    setIsLoadingPending(true);
    api.get<Fruit[]>('/fruits/pending')
      .then(setPendingFruits)
      .catch(() => setModerationError('Could not load the moderation queue.'))
      .finally(() => setIsLoadingPending(false));
  }, [user?.is_admin]);

  useEffect(() => { loadMyFruits(); }, [loadMyFruits]);
  useEffect(() => { loadPendingFruits(); }, [loadPendingFruits]);

  async function handleProfileSubmit(e: FormEvent) {
    e.preventDefault();
    setProfileMessage(null);
    setProfileError(null);
    setIsSavingProfile(true);
    try {
      await updateProfile({
        full_name: fullName.trim() || undefined,
        email: email.trim() || undefined,
        password: password.trim() || undefined,
      });
      setPassword('');
      setProfileMessage('Profile updated.');
    } catch (err) {
      setProfileError(err instanceof ApiError ? err.message : 'Could not update your profile.');
    } finally {
      setIsSavingProfile(false);
    }
  }

  async function handleBecomeSeller() {
    setIsBecomingSeller(true);
    try {
      await becomeSeller();
    } finally {
      setIsBecomingSeller(false);
    }
  }

  async function handleCreateFruit(e: FormEvent) {
    e.preventDefault();
    setCreateError(null);
    setIsCreatingFruit(true);
    try {
      const payload: FruitCreateInput = {
        name: fruitForm.name.trim(),
        slug: fruitForm.slug.trim() || slugify(fruitForm.name),
        description: fruitForm.description.trim(),
        origin: fruitForm.origin.trim(),
        is_organic: fruitForm.is_organic,
        tags: fruitForm.tags.split(',').map((t) => t.trim()).filter(Boolean),
        seasonal_months: fruitForm.seasonal_months
          .split(',')
          .map((m) => parseInt(m.trim(), 10))
          .filter((m) => Number.isInteger(m) && m >= 1 && m <= 12),
        image_url: fruitForm.image_url.trim() || null,
        base_price_hint_eur: Number(fruitForm.base_price_hint_eur) || 0,
        attributes: {},
      };
      await api.post<Fruit>('/fruits', payload);
      setFruitForm(EMPTY_FRUIT_FORM);
      setSlugTouched(false);
      loadMyFruits();
    } catch (err) {
      setCreateError(err instanceof ApiError ? err.message : 'Could not create the listing.');
    } finally {
      setIsCreatingFruit(false);
    }
  }

  async function handleDeleteFruit(fruit: Fruit, refresh: () => void) {
    if (!window.confirm(`Delete "${fruit.name}"? This cannot be undone.`)) return;
    try {
      await api.delete(`/fruits/${fruit._id}`);
      refresh();
    } catch {
      /* leave the list as-is; the user can retry */
    }
  }

  async function handleApprove(fruit: Fruit) {
    try {
      await api.post(`/fruits/${fruit._id}/approve`);
      loadPendingFruits();
    } catch {
      setModerationError('Could not approve this listing.');
    }
  }

  async function handleReject(fruit: Fruit) {
    try {
      await api.post(`/fruits/${fruit._id}/reject`);
      loadPendingFruits();
    } catch {
      setModerationError('Could not reject this listing.');
    }
  }

  if (isLoading || !user) {
    return <p className="container" data-testid="loading-indicator">Loading…</p>;
  }

  return (
    <div className="container cabinet-page" data-testid="cabinet-page">
      <h1>
        <UserIcon className="cabinet-page__title-icon" /> My cabinet
      </h1>

      <section className="cabinet-card" data-testid="profile-section">
        <h2>Personal data</h2>
        <form onSubmit={handleProfileSubmit} className="cabinet-form">
          <label htmlFor="cabinet-full-name">Full name</label>
          <input
            id="cabinet-full-name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            data-testid="cabinet-full-name-input"
          />

          <label htmlFor="cabinet-email">Email</label>
          <input
            id="cabinet-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            data-testid="cabinet-email-input"
          />

          <label htmlFor="cabinet-password">New password</label>
          <input
            id="cabinet-password"
            type="password"
            placeholder="Leave blank to keep your current password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            data-testid="cabinet-password-input"
          />

          {profileError && <p className="cabinet-form__error" role="alert" data-testid="profile-error">{profileError}</p>}
          {profileMessage && <p className="cabinet-form__success" data-testid="profile-success">{profileMessage}</p>}

          <button type="submit" className="btn-primary" disabled={isSavingProfile} data-testid="save-profile-button">
            {isSavingProfile ? 'Saving…' : 'Save changes'}
          </button>
        </form>
      </section>

      {!user.is_admin && (
      <section className="cabinet-card" data-testid="seller-status-section">
        <h2><StoreIcon /> Selling on Tutti Frutti</h2>
        {user.is_seller ? (
          <p className="cabinet-card__hint">
            You're a seller — your listings below are visible only to you until an admin approves them.
          </p>
        ) : (
          <>
            <p className="cabinet-card__hint">
              Want to sell your own fruit on Tutti Frutti? Become a seller to list produce —
              every listing goes through a quick admin review before it appears in the market.
            </p>
            <button
              className="btn-primary"
              onClick={handleBecomeSeller}
              disabled={isBecomingSeller}
              data-testid="become-seller-button"
            >
              {isBecomingSeller ? 'Setting up…' : 'Become a seller'}
            </button>
          </>
        )}
      </section>
      )}

      {user.is_seller && !user.is_admin && (
        <section className="cabinet-card" data-testid="seller-listings-section">
          <h2>My listings</h2>

          <form onSubmit={handleCreateFruit} className="cabinet-form" data-testid="create-fruit-form">
            <label htmlFor="fruit-name">Name</label>
            <input
              id="fruit-name"
              value={fruitForm.name}
              onChange={(e) => {
                const name = e.target.value;
                setFruitForm((f) => ({ ...f, name, slug: slugTouched ? f.slug : slugify(name) }));
              }}
              required
              data-testid="fruit-name-input"
            />

            <label htmlFor="fruit-slug">Slug</label>
            <input
              id="fruit-slug"
              value={fruitForm.slug}
              onChange={(e) => { setSlugTouched(true); setFruitForm((f) => ({ ...f, slug: e.target.value })); }}
              required
              data-testid="fruit-slug-input"
            />

            <label htmlFor="fruit-description">Description</label>
            <textarea
              id="fruit-description"
              value={fruitForm.description}
              onChange={(e) => setFruitForm((f) => ({ ...f, description: e.target.value }))}
              rows={2}
              data-testid="fruit-description-input"
            />

            <label htmlFor="fruit-origin">Origin</label>
            <input
              id="fruit-origin"
              value={fruitForm.origin}
              onChange={(e) => setFruitForm((f) => ({ ...f, origin: e.target.value }))}
              data-testid="fruit-origin-input"
            />

            <label htmlFor="fruit-price">Reference price (EUR)</label>
            <input
              id="fruit-price"
              type="number"
              min={0}
              step="0.05"
              value={fruitForm.base_price_hint_eur}
              onChange={(e) => setFruitForm((f) => ({ ...f, base_price_hint_eur: e.target.value }))}
              data-testid="fruit-price-input"
            />

            <label htmlFor="fruit-image">Image URL</label>
            <input
              id="fruit-image"
              value={fruitForm.image_url}
              onChange={(e) => setFruitForm((f) => ({ ...f, image_url: e.target.value }))}
              placeholder="/images/my-fruit.svg"
              data-testid="fruit-image-input"
            />

            <label htmlFor="fruit-tags">Tags (comma-separated)</label>
            <input
              id="fruit-tags"
              value={fruitForm.tags}
              onChange={(e) => setFruitForm((f) => ({ ...f, tags: e.target.value }))}
              placeholder="tropical, sweet"
              data-testid="fruit-tags-input"
            />

            <label htmlFor="fruit-months">In season (months 1-12, comma-separated)</label>
            <input
              id="fruit-months"
              value={fruitForm.seasonal_months}
              onChange={(e) => setFruitForm((f) => ({ ...f, seasonal_months: e.target.value }))}
              placeholder="6, 7, 8"
              data-testid="fruit-months-input"
            />

            <label className="cabinet-checkbox">
              <input
                type="checkbox"
                checked={fruitForm.is_organic}
                onChange={(e) => setFruitForm((f) => ({ ...f, is_organic: e.target.checked }))}
                data-testid="fruit-organic-input"
              />
              Organic
            </label>

            {createError && <p className="cabinet-form__error" role="alert" data-testid="create-fruit-error">{createError}</p>}

            <button type="submit" className="btn-primary" disabled={isCreatingFruit} data-testid="create-fruit-button">
              <PlusIcon /> {isCreatingFruit ? 'Submitting…' : 'Submit for approval'}
            </button>
          </form>

          {isLoadingMyFruits && <p data-testid="loading-indicator">Loading your listings…</p>}
          {!isLoadingMyFruits && myFruits.length === 0 && (
            <p data-testid="empty-my-fruits">You haven't listed anything yet.</p>
          )}

          <ul className="cabinet-fruit-list" data-testid="my-fruits-list">
            {myFruits.map((fruit) => (
              <li key={fruit._id} className="cabinet-fruit-row" data-testid="my-fruit-row">
                <span className="cabinet-fruit-row__name">{fruit.name}</span>
                <FruitStatusBadge status={fruit.status} />
                <button
                  className="icon-button icon-button--danger"
                  onClick={() => handleDeleteFruit(fruit, loadMyFruits)}
                  aria-label={`Delete ${fruit.name}`}
                  data-testid="delete-my-fruit-button"
                >
                  <TrashIcon />
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}

      {user.is_admin && (
        <section className="cabinet-card" data-testid="moderation-section">
          <h2><ShieldIcon /> Moderation queue</h2>
          {moderationError && <p className="cabinet-form__error" role="alert">{moderationError}</p>}
          {isLoadingPending && <p data-testid="loading-indicator">Loading the queue…</p>}
          {!isLoadingPending && pendingFruits.length === 0 && (
            <p data-testid="empty-pending-fruits">Nothing waiting for review.</p>
          )}
          <ul className="cabinet-fruit-list" data-testid="pending-fruits-list">
            {pendingFruits.map((fruit) => (
              <li key={fruit._id} className="cabinet-fruit-row" data-testid="pending-fruit-row">
                <Link to={`/fruits/${fruit.slug}`} className="cabinet-fruit-row__name">{fruit.name}</Link>
                <span className="cabinet-fruit-row__meta">seller: {fruit.seller_id ?? 'unknown'}</span>
                <button
                  className="icon-button icon-button--success"
                  onClick={() => handleApprove(fruit)}
                  aria-label={`Approve ${fruit.name}`}
                  data-testid="approve-fruit-button"
                >
                  <CheckIcon />
                </button>
                <button
                  className="icon-button"
                  onClick={() => handleReject(fruit)}
                  aria-label={`Reject ${fruit.name}`}
                  data-testid="reject-fruit-button"
                >
                  <XIcon />
                </button>
                <button
                  className="icon-button icon-button--danger"
                  onClick={() => handleDeleteFruit(fruit, loadPendingFruits)}
                  aria-label={`Delete ${fruit.name}`}
                  data-testid="delete-pending-fruit-button"
                >
                  <TrashIcon />
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
