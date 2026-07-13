import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { api } from '../api/client';
import type { TokenPair, User } from '../types';

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

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
  }, []);

  const value = useMemo(
    () => ({ user, isLoading, login, register, logout }),
    [user, isLoading, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
