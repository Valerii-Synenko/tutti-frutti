import { useState, type FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { ApiError } from '../api/client';
import './AuthPages.css';

export function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login(email, password);
      navigate('/');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="container auth-page" data-testid="login-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>Log in</h1>

        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          data-testid="login-email-input"
        />

        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          data-testid="login-password-input"
        />

        {error && <p className="auth-card__error" role="alert" data-testid="login-error">{error}</p>}

        <button type="submit" className="btn-primary" disabled={isSubmitting} data-testid="login-submit-button">
          {isSubmitting ? 'Logging in…' : 'Log in'}
        </button>

        <p className="auth-card__switch">
          New here? <Link to="/register" data-testid="go-to-register-link">Create an account</Link>
        </p>
      </form>
    </div>
  );
}
