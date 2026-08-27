/**
 * MerchantMind Frontend API Client
 */

export interface ProductRecommendation {
  product_id: string;
  name: string;
  price: number;
  description?: string;
  image_url?: string;
  category?: string;
  reasoning?: string;
}

export interface CartItem {
  product_id: string;
  name: string;
  price: number;
  quantity: number;
  image_url?: string;
}

export interface ChatResponse {
  conversation_id: string;
  message: string;
  recommendations?: ProductRecommendation[] | null;
  cart?: CartItem[] | null;
  cart_total: number;
  action?: string | null;
  payment_link?: string | null;
}

export interface OrderResponse {
  id: string;
  merchant_id: string;
  customer_id?: string | null;
  conversation_id?: string | null;
  items: CartItem[];
  subtotal: number;
  total: number;
  rzp_order_id?: string | null;
  rzp_payment_id?: string | null;
  payment_link?: string | null;
  status: string;
  created_at: string;
  paid_at?: string | null;
}

export interface OrderStatusResponse {
  id: string;
  status: string;
  total: number;
  rzp_order_id?: string | null;
  rzp_payment_id?: string | null;
  payment_link?: string | null;
  paid_at?: string | null;
}

export interface Merchant {
  id: string;
  name: string;
  email: string;
  phone?: string;
  description?: string;
  whatsapp_number?: string;
  is_active: boolean;
}

export interface ConversationDetail {
  id: string;
  merchant_id: string;
  channel: string;
  status: string;
  messages: Array<{
    role: "user" | "assistant" | "system";
    content: string;
    timestamp?: string;
    metadata?: {
      recommendations?: ProductRecommendation[];
      action?: string;
      payment_link?: string;
    };
  }>;
  cart: {
    items: CartItem[];
    total: number;
  };
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchMerchants(): Promise<Merchant[]> {
  try {
    const res = await fetch(`${API_BASE}/api/merchants/`, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch merchants");
    return await res.json();
  } catch (error) {
    console.error("fetchMerchants error:", error);
    return [];
  }
}

export async function sendChatMessage(payload: {
  merchant_id: string;
  conversation_id?: string | null;
  message: string;
}): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/api/chat/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: "Network error" }));
    throw new Error(errData.detail || "Failed to send chat message");
  }

  return await res.json();
}

export async function fetchConversation(conversationId: string): Promise<ConversationDetail | null> {
  try {
    const res = await fetch(`${API_BASE}/api/chat/conversations/${conversationId}`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return await res.json();
  } catch (error) {
    console.error("fetchConversation error:", error);
    return null;
  }
}

export async function updateCartDirectly(
  conversationId: string,
  items: CartItem[]
): Promise<{ items: CartItem[]; total: number }> {
  const res = await fetch(`${API_BASE}/api/chat/conversations/${conversationId}/cart`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ items }),
  });

  if (!res.ok) {
    throw new Error("Failed to update cart");
  }

  return await res.json();
}

export async function createOrder(payload: {
  conversation_id: string;
  merchant_id: string;
  customer_name?: string;
  customer_phone?: string;
  customer_email?: string;
  callback_url?: string;
}): Promise<OrderResponse> {
  const res = await fetch(`${API_BASE}/api/orders/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: "Order creation failed" }));
    throw new Error(errData.detail || "Failed to create order");
  }

  return await res.json();
}

export async function fetchOrderStatus(orderId: string): Promise<OrderStatusResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/api/orders/${orderId}/status`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return await res.json();
  } catch (error) {
    console.error("fetchOrderStatus error:", error);
    return null;
  }
}
