import http from "k6/http";
import { check, sleep, group } from "k6";
import { Counter, Rate, Trend } from "k6/metrics";

// Custom Performance Metrics
export const errorRate = new Rate("error_rate");
export const nonLlmDuration = new Trend("non_llm_duration_ms");
export const checkoutSagaDuration = new Trend("checkout_saga_duration_ms");
export const successfulCheckouts = new Counter("successful_checkouts");
export const rejectedCheckouts = new Counter("rejected_checkouts");

// Test Configuration: 300 VUs sustained + burst checkout load
export const options = {
  scenarios: {
    // Scenario 1: Sustained customer chat & catalog exploration (300 VUs for 5 minutes)
    sustained_chat_and_catalog: {
      executor: "ramping-vus",
      startVUs: 10,
      stages: [
        { duration: "30s", target: 100 },
        { duration: "1m", target: 300 },
        { duration: "3m", target: 300 },
        { duration: "30s", target: 0 },
      ],
      gracefulRampDown: "15s",
      exec: "chatScenario",
    },

    // Scenario 2: High-concurrency burst checkout on constrained stock (50 concurrent checkouts)
    burst_checkout_stress: {
      executor: "per-vu-iterations",
      vus: 50,
      iterations: 2,
      maxDuration: "1m",
      startTime: "1m", // Burst fires at 1 minute mark
      exec: "burstCheckoutScenario",
    },
  },

  thresholds: {
    error_rate: ["rate<0.01"], // Error rate under 1%
    non_llm_duration_ms: ["p(95)<800"], // p95 response time < 800ms for non-LLM endpoints
    http_req_duration: ["p(95)<2500"], // p95 response time < 2.5s overall
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

// --- Scenario 1: Chat and Catalog Navigation ---
export function chatScenario() {
  group("Health and Store Discovery", () => {
    // 1. Health check
    const healthRes = http.get(`${BASE_URL}/health`);
    nonLlmDuration.add(healthRes.timings.duration);
    check(healthRes, {
      "health is 200": (r) => r.status === 200,
    }) || errorRate.add(1);

    // 2. List Merchants
    const merchantsRes = http.get(`${BASE_URL}/api/merchants/`);
    nonLlmDuration.add(merchantsRes.timings.duration);
    const pass = check(merchantsRes, {
      "merchants 200": (r) => r.status === 200,
      "merchants has data": (r) => JSON.parse(r.body).length > 0,
    });
    if (!pass) errorRate.add(1);

    const merchants = JSON.parse(merchantsRes.body);
    if (merchants && merchants.length > 0) {
      const merchantId = merchants[0].id;

      // 3. List Products
      const productsRes = http.get(`${BASE_URL}/api/merchants/${merchantId}/products`);
      nonLlmDuration.add(productsRes.timings.duration);
      check(productsRes, {
        "products 200": (r) => r.status === 200,
      }) || errorRate.add(1);
    }
  });

  sleep(1);
}

// --- Scenario 2: Burst Checkout Concurrency ---
export function burstCheckoutScenario() {
  group("Burst Checkout Saga", () => {
    // 1. Fetch available store
    const merchantsRes = http.get(`${BASE_URL}/api/merchants/`);
    if (merchantsRes.status !== 200) return;
    const merchants = JSON.parse(merchantsRes.body);
    if (!merchants || merchants.length === 0) return;

    const merchantId = merchants[0].id;
    const productsRes = http.get(`${BASE_URL}/api/merchants/${merchantId}/products`);
    if (productsRes.status !== 200) return;
    const products = JSON.parse(productsRes.body);
    if (!products || products.length === 0) return;

    const targetProduct = products[0];

    // 2. Submit concurrent checkout
    const checkoutPayload = JSON.stringify({
      merchant_id: merchantId,
      fulfillment_mode: "delivery",
      delivery_address: "100 Feet Road, Indiranagar, Bangalore",
      items: [
        {
          product_id: targetProduct.id,
          name: targetProduct.name,
          price: targetProduct.price,
          quantity: 1,
        },
      ],
    });

    const headers = { "Content-Type": "application/json" };
    const start = new Date().getTime();
    const orderRes = http.post(`${BASE_URL}/api/orders/`, checkoutPayload, { headers });
    checkoutSagaDuration.add(new Date().getTime() - start);

    if (orderRes.status === 200 || orderRes.status === 201) {
      successfulCheckouts.add(1);
      check(orderRes, {
        "order created with payment link": (r) => {
          const body = JSON.parse(r.body);
          return body.payment_link !== null || body.status === "payment_link_sent";
        },
      });
    } else if (orderRes.status === 400 && orderRes.body.includes("stock")) {
      // Clean rejection under row-level lock (expected behavior when stock reaches 0)
      rejectedCheckouts.add(1);
    } else {
      errorRate.add(1);
    }
  });

  sleep(0.5);
}
