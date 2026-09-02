/**
 * MerchantMind Frontend API Client
 * Includes automatic proxy fallback for zero-CORS reliability across all browsers.
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

export interface ReasoningEvent {
  type: "thinking" | "budget_check" | "tool_call" | "tool_result" | "handoff" | "handoff_context_applied" | "answer" | "error";
  agent?: string;
  content?: string;
  tool?: string;
  tool_display?: string;
  args?: Record<string, any>;
  summary?: string;
  data?: any;
  target_agent?: string;
  store_name?: string;
  chat_response?: ChatResponse;
  timestamp?: string;
}

export interface ChatResponse {
  conversation_id: string;
  merchant_id?: string | null;
  merchant_name?: string | null;
  message: string;
  recommendations?: ProductRecommendation[] | null;
  cart?: CartItem[] | null;
  cart_total: number;
  action?: string | null;
  payment_link?: string | null;
  agent_reasoning?: Array<{
    action: string;
    reasoning: string;
    timestamp?: string;
  }> | null;
}

export interface TrackingData {
  order_id: string;
  status: string;
  fulfillment_mode: "delivery" | "pickup";
  store_name: string;
  store_address: string;
  store_latitude: number;
  store_longitude: number;
  customer_latitude: number;
  customer_longitude: number;
  haversine_distance_km: number;
  average_speed_kmh: number;
  prep_time_minutes: number;
  total_estimated_eta_minutes: number;
  remaining_eta_minutes: number;
  elapsed_minutes: number;
  live_progress_percentage: number;
  current_stage: string;
  is_pickup: boolean;
  driver_name: string;
  driver_vehicle: string;
  pickup_otp: string;
  created_at: string;
  rzp_payment_id?: string | null;
  total: number;
  delivery_address?: string | null;
}

export interface OrderResponse {
  id: string;
  merchant_id: string;
  customer_id?: string | null;
  conversation_id?: string | null;
  items: CartItem[];
  subtotal: number;
  total: number;
  fulfillment_mode?: "delivery" | "pickup";
  delivery_address?: string | null;
  pickup_time?: string | null;
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
  store_address?: string;
  latitude?: number;
  longitude?: number;
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

const PRIMARY_API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const PROXY_API = "/api-proxy";

/**
 * Resilient fetcher: Tries direct API first, falls back to Next.js proxy if CORS/network blocked
 */
async function resilientFetch(endpoint: string, options: RequestInit = {}): Promise<Response> {
  const url1 = `${PRIMARY_API}${endpoint}`;
  try {
    const res = await fetch(url1, options);
    return res;
  } catch (err1) {
    // If client-side and direct fails, try internal proxy
    if (typeof window !== "undefined") {
      try {
        const url2 = `${PROXY_API}${endpoint.replace(/^\/api/, "")}`;
        const res2 = await fetch(url2, options);
        return res2;
      } catch (err2) {
        console.warn("API proxy fallback also failed:", err2);
      }
    }
    throw err1;
  }
}

export async function fetchMerchants(): Promise<Merchant[]> {
  try {
    const res = await resilientFetch("/api/merchants/", { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch merchants");
    return await res.json();
  } catch (error) {
    console.error("fetchMerchants error:", error);
    return [];
  }
}

export async function sendChatMessage(payload: {
  merchant_id?: string | null;
  conversation_id?: string | null;
  customer_id?: string | null;
  message: string;
}): Promise<ChatResponse> {
  // Remove null/undefined merchant_id from payload for clean JSON
  const cleanPayload: Record<string, unknown> = {
    message: payload.message,
  };
  if (payload.merchant_id) cleanPayload.merchant_id = payload.merchant_id;
  if (payload.conversation_id) cleanPayload.conversation_id = payload.conversation_id;
  if (payload.customer_id) cleanPayload.customer_id = payload.customer_id;

  const res = await resilientFetch("/api/chat/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(cleanPayload),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: "Network error" }));
    throw new Error(errData.detail || "Failed to send chat message");
  }

  return await res.json();
}

export async function sendChatMessageStreaming(
  payload: {
    merchant_id?: string | null;
    conversation_id?: string | null;
    customer_id?: string | null;
    message: string;
  },
  onEvent: (event: ReasoningEvent) => void
): Promise<ChatResponse | null> {
  const cleanPayload: Record<string, unknown> = {
    message: payload.message,
  };
  if (payload.merchant_id) cleanPayload.merchant_id = payload.merchant_id;
  if (payload.conversation_id) cleanPayload.conversation_id = payload.conversation_id;
  if (payload.customer_id) cleanPayload.customer_id = payload.customer_id;

  const res = await resilientFetch("/api/chat/stream", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(cleanPayload),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: "Streaming error" }));
    throw new Error(errData.detail || "Failed to initiate streaming chat");
  }

  const reader = res.body?.getReader();
  if (!reader) {
    throw new Error("No readable stream received from server");
  }

  const decoder = new TextDecoder("utf-8");
  let buffer = "";
  let finalResponse: ChatResponse | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() || "";

    for (const block of lines) {
      const trimmed = block.trim();
      if (trimmed.startsWith("data:")) {
        try {
          const jsonStr = trimmed.slice(5).trim();
          const parsed: ReasoningEvent = JSON.parse(jsonStr);
          onEvent(parsed);
          if (parsed.type === "answer" && parsed.chat_response) {
            finalResponse = parsed.chat_response;
          }
        } catch (e) {
          console.warn("Failed to parse SSE event chunk:", e, trimmed);
        }
      }
    }
  }

  return finalResponse;
}

export async function fetchConversation(conversationId: string): Promise<ConversationDetail | null> {
  try {
    const res = await resilientFetch(`/api/chat/conversations/${conversationId}`, {
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
  const res = await resilientFetch(`/api/chat/conversations/${conversationId}/cart`, {
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
  fulfillment_mode?: "delivery" | "pickup";
  delivery_address?: string;
  pickup_time?: string;
  items?: CartItem[];
}): Promise<OrderResponse> {
  const res = await resilientFetch("/api/orders/", {
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
    const res = await resilientFetch(`/api/orders/${orderId}/status`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return await res.json();
  } catch (error) {
    console.error("fetchOrderStatus error:", error);
    return null;
  }
}

export async function fetchOrder(orderId: string): Promise<OrderResponse | null> {
  try {
    const res = await resilientFetch(`/api/orders/${orderId}`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return await res.json();
  } catch (error) {
    console.error("fetchOrder error:", error);
    return null;
  }
}

export async function verifyOrderPayment(
  orderId: string,
  razorpayPaymentId?: string
): Promise<OrderResponse | null> {
  try {
    const res = await resilientFetch(`/api/orders/${orderId}/verify-payment`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ razorpay_payment_id: razorpayPaymentId }),
    });
    if (!res.ok) return null;
    return await res.json();
  } catch (error) {
    console.error("verifyOrderPayment error:", error);
    return null;
  }
}

export async function fetchTrackingData(orderId: string): Promise<TrackingData | null> {
  try {
    const res = await resilientFetch(`/api/orders/${orderId}/tracking-data`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return await res.json();
  } catch (error) {
    console.error("fetchTrackingData error:", error);
    return null;
  }
}

export interface MerchantChatResponse {
  conversation_id: string;
  merchant_id: string;
  merchant_name: string;
  message: string;
  action_data?: Record<string, any> | null;
}

export async function sendMerchantChatMessage(payload: {
  merchant_id: string;
  message: string;
  conversation_id?: string | null;
}): Promise<MerchantChatResponse> {
  const res = await resilientFetch("/api/merchant-chat/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: "Merchant agent request failed" }));
    throw new Error(errData.detail || "Failed to reach Merchant Agent");
  }

  return await res.json();
}

export async function fetchMerchantProducts(merchantId: string): Promise<any[]> {
  try {
    const res = await resilientFetch(`/api/products/${merchantId}/products`, {
      cache: "no-store",
    });
    if (!res.ok) return [];
    return await res.json();
  } catch (error) {
    console.error("fetchMerchantProducts error:", error);
    return [];
  }
}

export async function toggleProductStock(
  merchantId: string,
  productId: string,
  inStock: boolean
): Promise<{ success: boolean; in_stock: boolean; name: string }> {
  const res = await resilientFetch(
    `/api/products/${merchantId}/products/${productId}/stock?in_stock=${inStock}`,
    {
      method: "PATCH",
    }
  );
  if (!res.ok) {
    throw new Error("Failed to update product stock status");
  }
  return await res.json();
}

export async function syncMerchantInventory(
  merchantId: string,
  updates: Array<{ name: string; in_stock?: boolean; price?: number; quantity?: number }>
): Promise<{ success: boolean; updated_count: number; merchant_name: string }> {
  const res = await resilientFetch("/api/webhooks/inventory/sync", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      merchant_id: merchantId,
      source: "pos_simulator",
      updates,
    }),
  });
  if (!res.ok) {
    throw new Error("Failed to trigger inventory sync webhook");
  }
  return await res.json();
}

export async function fetchEvaluationBenchmarks(): Promise<any> {
  try {
    const res = await resilientFetch("/api/analytics/benchmarks", { cache: "no-store" });
    if (!res.ok) return null;
    return await res.json();
  } catch (error) {
    console.error("fetchEvaluationBenchmarks error:", error);
    return null;
  }
}

export async function runReconciliationJob(): Promise<any> {
  const res = await resilientFetch("/api/analytics/reconciliation/run", {
    method: "POST",
  });
  if (!res.ok) {
    throw new Error("Failed to execute reconciliation");
  }
  return await res.json();
}

export interface CustomerAddress {
  label: string;
  address: string;
  lat?: number;
  lng?: number;
  is_default?: boolean;
}

export interface CustomerProfile {
  id: string;
  name: string;
  phone: string;
  email?: string;
  saved_addresses: CustomerAddress[];
  preferences?: Record<string, any>;
  favorite_merchants?: Array<{ name: string; last_item?: string; rating?: number }>;
  order_count: number;
  total_spent: number;
  formatted_memory?: string;
}

export async function fetchDemoCustomer(): Promise<CustomerProfile | null> {
  try {
    const res = await resilientFetch("/api/customers/demo", { cache: "no-store" });
    if (!res.ok) return null;
    return await res.json();
  } catch (error) {
    console.error("fetchDemoCustomer error:", error);
    return null;
  }
}

export async function fetchVoiceStatus(): Promise<{ deepgram_enabled: boolean; provider: string } | null> {
  try {
    const res = await resilientFetch("/api/voice/status", { cache: "no-store" });
    if (!res.ok) return null;
    return await res.json();
  } catch (error) {
    console.error("fetchVoiceStatus error:", error);
    return null;
  }
}

export async function fetchDeepgramVoiceAudio(text: string): Promise<Blob | null> {
  try {
    const res = await resilientFetch("/api/voice/speak", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text }),
    });

    if (!res.ok) {
      return null;
    }

    const contentType = res.headers.get("content-type") || "";
    if (!contentType.includes("audio")) {
      return null;
    }

    return await res.blob();
  } catch (error) {
    console.warn("Deepgram TTS fetch failed, will fallback:", error);
    return null;
  }
}



