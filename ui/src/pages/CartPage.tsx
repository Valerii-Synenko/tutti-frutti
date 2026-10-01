import { useEffect, useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useCart } from '../hooks/useCart';
import { useAuth } from '../hooks/useAuth';
import { api, ApiError } from '../api/client';
import type { Order } from '../types';
import './CartPage.css';

interface CheckoutForm {
  fullName: string;
  phone: string;
  street: string;
  city: string;
  postalCode: string;
  country: string;
  cardholderName: string;
  cardNumber: string;
  expiry: string;
  cvc: string;
}

// "4242424242424242" -> "4242 4242 4242 4242"
function formatCardNumber(value: string): string {
  return value.replace(/\D/g, '').slice(0, 19).replace(/(.{4})(?=.)/g, '$1 ');
}

// "1230" -> "12/30"
function formatExpiry(value: string): string {
  const digits = value.replace(/\D/g, '').slice(0, 4);
  return digits.length > 2 ? `${digits.slice(0, 2)}/${digits.slice(2)}` : digits;
}

export function CartPage() {
  const { lines, updateQuantity, removeFromCart, clearCart, totalEur } = useCart();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [isPlacing, setIsPlacing] = useState(false);
  const [placedOrder, setPlacedOrder] = useState<Order | null>(null);
  const [form, setForm] = useState<CheckoutForm>({
    fullName: user?.full_name ?? '',
    phone: '',
    street: '',
    city: '',
    postalCode: '',
    country: '',
    cardholderName: user?.full_name ?? '',
    cardNumber: '',
    expiry: '',
    cvc: '',
  });

  // The user may still be loading on first render; prefill their name once known.
  useEffect(() => {
    if (!user?.full_name) return;
    setForm((prev) => ({
      ...prev,
      fullName: prev.fullName || user.full_name,
      cardholderName: prev.cardholderName || user.full_name,
    }));
  }, [user?.full_name]);

  function setField(field: keyof CheckoutForm, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleCheckout(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsPlacing(true);
    try {
      const order = await api.post<Order>('/orders', {
        items: lines.map((line) => ({ fruit_sku: line.fruit.slug, quantity: line.quantity })),
        contact: { full_name: form.fullName.trim(), phone: form.phone.trim() },
        shipping_address: {
          street: form.street.trim(),
          city: form.city.trim(),
          postal_code: form.postalCode.trim(),
          country: form.country.trim(),
        },
        payment: {
          cardholder_name: form.cardholderName.trim(),
          card_number: form.cardNumber,
          expiry: form.expiry,
          cvc: form.cvc,
        },
      });
      clearCart();
      setPlacedOrder(order);
      window.scrollTo({ top: 0 });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not place the order. Please try again.');
    } finally {
      setIsPlacing(false);
    }
  }

  if (placedOrder) {
    return (
      <div className="container cart-page" data-testid="cart-page">
        <section className="order-success" role="status" data-testid="order-success">
          <span className="order-success__icon" aria-hidden="true">🧺</span>
          <h1 data-testid="order-success-title">Thank you — your order is placed and paid!</h1>
          <p data-testid="order-success-message">
            We&rsquo;re packing your fruit now and will ship it as soon as possible
            {placedOrder.shipping_address && <> to {placedOrder.shipping_address.city}</>}.
          </p>
          <dl className="order-success__details">
            <div>
              <dt>Order</dt>
              <dd data-testid="order-success-id">#{placedOrder.id.slice(0, 8)}</dd>
            </div>
            <div>
              <dt>Paid</dt>
              <dd data-testid="order-success-total">€{placedOrder.total_eur.toFixed(2)}</dd>
            </div>
            {placedOrder.payment && (
              <div>
                <dt>Card</dt>
                <dd data-testid="order-success-card">•••• {placedOrder.payment.card_last4}</dd>
              </div>
            )}
          </dl>
          <button
            className="btn-primary order-success__continue"
            onClick={() => navigate('/')}
            data-testid="continue-shopping-button"
          >
            Continue shopping
          </button>
        </section>
      </div>
    );
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

      {!user ? (
        <Link to="/login" className="btn-primary cart-page__checkout" data-testid="checkout-login-link">
          Log in to check out
        </Link>
      ) : (
        <form className="checkout" onSubmit={handleCheckout} data-testid="checkout-form">
          <fieldset className="checkout__section">
            <legend>Contact</legend>
            <div className="checkout__field">
              <label htmlFor="checkout-full-name">Full name</label>
              <input
                id="checkout-full-name"
                autoComplete="name"
                required
                maxLength={120}
                value={form.fullName}
                onChange={(e) => setField('fullName', e.target.value)}
                data-testid="checkout-full-name-input"
              />
            </div>
            <div className="checkout__field">
              <label htmlFor="checkout-phone">Mobile phone</label>
              <input
                id="checkout-phone"
                type="tel"
                autoComplete="tel"
                required
                placeholder="+385 91 234 5678"
                pattern="\+?[0-9][0-9 \(\)\-]{6,19}"
                title="Digits, optionally starting with +; spaces, dashes and brackets allowed"
                value={form.phone}
                onChange={(e) => setField('phone', e.target.value)}
                data-testid="checkout-phone-input"
              />
            </div>
          </fieldset>

          <fieldset className="checkout__section">
            <legend>Delivery address</legend>
            <div className="checkout__field">
              <label htmlFor="checkout-street">Street and house number</label>
              <input
                id="checkout-street"
                autoComplete="street-address"
                required
                maxLength={200}
                value={form.street}
                onChange={(e) => setField('street', e.target.value)}
                data-testid="checkout-street-input"
              />
            </div>
            <div className="checkout__row">
              <div className="checkout__field">
                <label htmlFor="checkout-city">City</label>
                <input
                  id="checkout-city"
                  autoComplete="address-level2"
                  required
                  maxLength={100}
                  value={form.city}
                  onChange={(e) => setField('city', e.target.value)}
                  data-testid="checkout-city-input"
                />
              </div>
              <div className="checkout__field">
                <label htmlFor="checkout-postal-code">Postal code</label>
                <input
                  id="checkout-postal-code"
                  autoComplete="postal-code"
                  required
                  pattern="[A-Za-z0-9 \-]{3,10}"
                  value={form.postalCode}
                  onChange={(e) => setField('postalCode', e.target.value)}
                  data-testid="checkout-postal-code-input"
                />
              </div>
            </div>
            <div className="checkout__field">
              <label htmlFor="checkout-country">Country</label>
              <input
                id="checkout-country"
                autoComplete="country-name"
                required
                minLength={2}
                maxLength={100}
                value={form.country}
                onChange={(e) => setField('country', e.target.value)}
                data-testid="checkout-country-input"
              />
            </div>
          </fieldset>

          <fieldset className="checkout__section">
            <legend>Payment</legend>
            <div className="checkout__field">
              <label htmlFor="checkout-cardholder">Name on card</label>
              <input
                id="checkout-cardholder"
                autoComplete="cc-name"
                required
                maxLength={120}
                value={form.cardholderName}
                onChange={(e) => setField('cardholderName', e.target.value)}
                data-testid="checkout-cardholder-input"
              />
            </div>
            <div className="checkout__field">
              <label htmlFor="checkout-card-number">Card number</label>
              <input
                id="checkout-card-number"
                inputMode="numeric"
                autoComplete="cc-number"
                required
                placeholder="1234 5678 9012 3456"
                pattern="[0-9 ]{13,23}"
                value={form.cardNumber}
                onChange={(e) => setField('cardNumber', formatCardNumber(e.target.value))}
                data-testid="checkout-card-number-input"
              />
            </div>
            <div className="checkout__row">
              <div className="checkout__field">
                <label htmlFor="checkout-expiry">Expiry (MM/YY)</label>
                <input
                  id="checkout-expiry"
                  inputMode="numeric"
                  autoComplete="cc-exp"
                  required
                  placeholder="MM/YY"
                  pattern="(0[1-9]|1[0-2])/[0-9]{2}"
                  value={form.expiry}
                  onChange={(e) => setField('expiry', formatExpiry(e.target.value))}
                  data-testid="checkout-expiry-input"
                />
              </div>
              <div className="checkout__field">
                <label htmlFor="checkout-cvc">CVC</label>
                <input
                  id="checkout-cvc"
                  inputMode="numeric"
                  autoComplete="cc-csc"
                  required
                  placeholder="123"
                  pattern="[0-9]{3,4}"
                  maxLength={4}
                  value={form.cvc}
                  onChange={(e) => setField('cvc', e.target.value.replace(/\D/g, ''))}
                  data-testid="checkout-cvc-input"
                />
              </div>
            </div>
            <p className="checkout__note">This is a demo shop — no real payment is taken.</p>
          </fieldset>

          {error && <p className="cart-page__error" role="alert" data-testid="checkout-error">{error}</p>}

          <button
            type="submit"
            className="btn-primary cart-page__checkout"
            disabled={isPlacing}
            data-testid="checkout-button"
          >
            {isPlacing ? 'Placing order…' : `Place order · €${totalEur.toFixed(2)}`}
          </button>
        </form>
      )}
    </div>
  );
}
