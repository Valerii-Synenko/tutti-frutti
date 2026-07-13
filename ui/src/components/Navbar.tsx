import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useCart } from '../hooks/useCart';
import './Navbar.css';

export function Navbar() {
  const { user, logout } = useAuth();
  const { totalItems } = useCart();

  return (
    <header className="navbar" data-testid="navbar">
      <div className="container navbar__inner">
        <Link to="/" className="navbar__brand" data-testid="nav-home-link">
          <span className="navbar__brand-mark">🍊</span> Tutti Frutti
        </Link>

        <nav className="navbar__links">
          <Link to="/" data-testid="nav-catalogue-link">Market</Link>
          {user && <Link to="/orders" data-testid="nav-orders-link">My Orders</Link>}
          <Link to="/cart" className="navbar__cart" data-testid="nav-cart-link">
            Cart
            {totalItems > 0 && (
              <span className="navbar__cart-badge" data-testid="cart-count">{totalItems}</span>
            )}
          </Link>

          {user ? (
            <div className="navbar__user">
              <span data-testid="nav-user-name">{user.full_name}</span>
              <button className="btn-secondary navbar__logout" onClick={logout} data-testid="logout-button">
                Log out
              </button>
            </div>
          ) : (
            <Link to="/login" className="btn-primary navbar__login" data-testid="nav-login-link">
              Log in
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}
