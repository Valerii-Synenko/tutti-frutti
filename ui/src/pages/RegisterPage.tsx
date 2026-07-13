import { useState, type FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { ApiError } from '../api/client';
import './AuthPages.css';

export function RegisterPage() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await register(email, password, fullName);
      navigate('/');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="container auth-page" data-testid="register-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>Create an account</h1>

        <label htmlFor="fullName">Full name</label>
        <input
          id="fullName"
          type="text"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          required
          data-testid="register-name-input"
        />

        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          data-testid="register-email-input"
        />

        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength={8}
          data-testid="register-password-input"
        />

        {error && <p className="auth-card__error" role="alert" data-testid="register-error">{error}</p>}

        <button type="submit" className="btn-primary" disabled={isSubmitting} data-testid="register-submit-button">
          {isSubmitting ? 'Creating account…' : 'Create account'}
        </button>

        <p className="auth-card__switch">
          Already have an account? <Link to="/login" data-testid="go-to-login-link">Log in</Link>
        </p>
      </form>
    </div>
  );
}
