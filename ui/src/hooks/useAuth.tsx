import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import type { TokenPair, User } from '../types';

interface ProfileUpdate {
  email?: string;
  full_name?: string;
  password?: string;
}

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
  updateProfile: (update: ProfileUpdate) => Promise<void>;
  becomeSeller: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  const loadCurrentUser = useCallback(async () => {
    const token = localStorage.getItem('tf_access_token');
    if (!token) {
      setIsLoading(false);
      return;
    }
    try {
      const me = await api.get<User>('/auth/me');
      setUser(me);
    } catch {
      localStorage.removeItem('tf_access_token');
      localStorage.removeItem('tf_refresh_token');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCurrentUser();
  }, [loadCurrentUser]);

  useEffect(() => {
    // If the browser restores this page from the back/forward cache (most
    // common on Safari), the entire React tree — including whichever user
    // was logged in at the time — comes back frozen exactly as it was. Force
    // a re-check against the token that's actually in localStorage now, so
    // switching users in the meantime can't leave stale admin/seller UI showing.
    function onPageShow(event: PageTransitionEvent) {
      if (event.persisted) {
        loadCurrentUser();
      }
    }
    window.addEventListener('pageshow', onPageShow);
    return () => window.removeEventListener('pageshow', onPageShow);
  }, [loadCurrentUser]);

  const login = useCallback(async (email: string, password: string) => {
    const form = new URLSearchParams();
    form.set('username', email);
    form.set('password', password);
    const tokens = await api.postForm<TokenPair>('/auth/login', form);
    localStorage.setItem('tf_access_token', tokens.access_token);
    localStorage.setItem('tf_refresh_token', tokens.refresh_token);
    await loadCurrentUser();
  }, [loadCurrentUser]);

  const register = useCallback(async (email: string, password: string, fullName: string) => {
    await api.post('/auth/register', { email, password, full_name: fullName });
    await login(email, password);
  }, [login]);

  const logout = useCallback(() => {
    localStorage.removeItem('tf_access_token');
    localStorage.removeItem('tf_refresh_token');
    setUser(null);
    // `replace` (not push) so the back button can't return to a page that was
    // rendered while authenticated — same class of leak the no-store/pageshow
    // fixes address, just for the in-app navigation stack instead of the cache.
    navigate('/', { replace: true });
  }, [navigate]);

  const updateProfile = useCallback(async (update: ProfileUpdate) => {
    const updated = await api.patch<User>('/auth/me', update);
    setUser(updated);
  }, []);

  const becomeSeller = useCallback(async () => {
    // The seller flag is embedded in the access token, so we need a fresh one.
    const tokens = await api.post<TokenPair>('/auth/become-seller');
    localStorage.setItem('tf_access_token', tokens.access_token);
    localStorage.setItem('tf_refresh_token', tokens.refresh_token);
    await loadCurrentUser();
  }, [loadCurrentUser]);

  const value = useMemo(
    () => ({ user, isLoading, login, register, logout, updateProfile, becomeSeller }),
    [user, isLoading, login, register, logout, updateProfile, becomeSeller]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
