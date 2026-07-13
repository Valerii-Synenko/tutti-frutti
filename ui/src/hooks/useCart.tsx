import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react';
import type { CartLine, Fruit } from '../types';

interface CartContextValue {
  lines: CartLine[];
  addToCart: (fruit: Fruit, quantity?: number) => void;
  removeFromCart: (slug: string) => void;
  updateQuantity: (slug: string, quantity: number) => void;
  clearCart: () => void;
  totalItems: number;
  totalEur: number;
}

const CartContext = createContext<CartContextValue | undefined>(undefined);

export function CartProvider({ children }: { children: ReactNode }) {
  const [lines, setLines] = useState<CartLine[]>([]);

  const addToCart = useCallback((fruit: Fruit, quantity = 1) => {
    setLines((prev) => {
      const existing = prev.find((line) => line.fruit.slug === fruit.slug);
      if (existing) {
        return prev.map((line) =>
          line.fruit.slug === fruit.slug ? { ...line, quantity: line.quantity + quantity } : line
        );
      }
      return [...prev, { fruit, quantity }];
    });
  }, []);

  const removeFromCart = useCallback((slug: string) => {
    setLines((prev) => prev.filter((line) => line.fruit.slug !== slug));
  }, []);

  const updateQuantity = useCallback((slug: string, quantity: number) => {
    setLines((prev) =>
      quantity <= 0
        ? prev.filter((line) => line.fruit.slug !== slug)
        : prev.map((line) => (line.fruit.slug === slug ? { ...line, quantity } : line))
    );
  }, []);

  const clearCart = useCallback(() => setLines([]), []);

  const totalItems = lines.reduce((sum, line) => sum + line.quantity, 0);
  const totalEur = lines.reduce(
    (sum, line) => sum + (line.fruit.live_price_eur ?? line.fruit.base_price_hint_eur) * line.quantity,
    0
  );

  const value = useMemo(
    () => ({ lines, addToCart, removeFromCart, updateQuantity, clearCart, totalItems, totalEur }),
    [lines, addToCart, removeFromCart, updateQuantity, clearCart, totalItems, totalEur]
  );

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart(): CartContextValue {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error('useCart must be used within CartProvider');
  return ctx;
}
