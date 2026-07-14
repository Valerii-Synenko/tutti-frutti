export interface Fruit {
  id: string;
  name: string;
  slug: string;
  description: string;
  origin: string;
  is_organic: boolean;
  seasonal_months: number[];
  tags: string[];
  image_url: string | null;
  base_price_hint_eur: number;
  attributes: Record<string, unknown>;
  live_price_eur: number | null;
  quantity_available: number | null;
  in_stock: boolean;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface OrderItem {
  fruit_sku: string;
  quantity: number;
  unit_price_eur: number;
}

export interface Order {
  id: string;
  status: string;
  total_eur: number;
  created_at: string;
  items: OrderItem[];
}

export interface CartLine {
  fruit: Fruit;
  quantity: number;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface Comment {
  _id: string;
  fruit_slug: string;
  author: string;
  body: string;
  created_at: string;
  user_id: string | null;
}
