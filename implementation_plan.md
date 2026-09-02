# MerchantMind — Production Hardening & Architectural Upgrade Plan (7.5 → 9.5+/10)

This implementation plan directly resolves every architectural gap, data integrity risk, security vulnerability, and ungrounded claim documented in the [project_assessment.md](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/project_assessment.md). 

It is designed to be **100% self-contained**, giving technical evaluators, judges, and developers complete visibility into the architectural transformations, code modifications, database migrations, security controls, and verification suites.

---

## 1. Executive Summary of Upgrades

| Dimension | Current State (7.5/10) | Target State (9.5+/10) | Technical Strategy |
| :--- | :--- | :--- | :--- |
| **Financial Integrity** | `Float` columns for `total`, `subtotal`, `price` in PostgreSQL; float-to-paise on the fly. | Integer-paise authoritative database schema with explicit Decimal precision models. | Add `amount_paise`, `subtotal_paise`, `unit_price_paise` columns; DB-level check constraints (`>= 0`). |
| **Authentication & RBAC** | Zero authentication across all merchant management & agent chat routes. | Timing-safe API Key Header authentication (`X-Merchant-Key`) with multi-tenant merchant isolation. | FastAPI dependency injection (`get_authenticated_merchant`), hash-checked keys in PostgreSQL. |
| **Reconciliation & DLQ** | Manual poller endpoint only; no autonomous worker. | Autonomous background async worker with exponential backoff & DLQ retry engine. | `asyncio.create_task` lifespan daemon running every 60s with DB lock guard to prevent split-brain. |
| **Webhook Deduplication** | In-memory `set()` lost on process restart; Redis failover silently dropped. | Distributed atomic Redis `SETNX` with 24h TTL + database transaction unique constraint. | Redis cluster-safe idempotency with DB-backed `webhook_events` fallback table. |
| **Abuse & Rate Limiting** | No rate limiting; susceptible to LLM quota exhaustion. | Sliding-window token-bucket rate limiting on `/api/chat` and `/api/orders`. | Redis-backed sliding-window middleware (60 req/min per IP/phone). |
| **Telemetry & Observability** | Homegrown profiler labeled as "OpenTelemetry". | Clean, honest nomenclature: Structured Distributed Latency Tracing + real W3C TraceContext headers. | Standardize span formats, trace context propagation across agent hops. |
| **Test Coverage** | 38 tests (concurrency, saga, jailbreaks). | 55+ tests including auth validation, paise drift, background poller, and synthetic load. | New test modules for RBAC, DB constraints, worker lifecycle, and rate limits. |

---

## 2. Proposed Architectural Changes by Component

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   CLIENT / GATEWAYS                                    │
│   Next.js 16 Web Storefront  │  Merchant Ops Console  │  Razorpay Webhook Dispatcher   │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        SECURITY & INGRESS MIDDLEWARE LAYER                             │
│   ├── Strict CORS Policy (Restricted Origins)                                          │
│   ├── Sliding Window Rate Limiter (Redis Token Bucket)                                 │
│   ├── Timing-Safe Merchant Authentication (`X-Merchant-Key` & SHA-256 HMAC)           │
│   └── Prompt Injection & Jailbreak Neutralizer (`PromptSanitizer`)                    │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              MULTI-AGENT ROUTING CORE                                  │
│   ├── CircuitBreaker (3.5s SLA Bounding & Graceful Fallback)                           │
│   ├── TraceContext (Micro-Span Profiler with W3C Trace Headers)                        │
│   ├── DiscoveryAgent (Cross-Merchant City Search & Structured Budget Guardrail)        │
│   ├── ShoppingAgent (ReAct Catalog Intelligence & Budget-Bounded Upselling)            │
│   └── MerchantAgent (Authenticated Inventory Overrides & Operational Telemetry)        │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                           TRANSACTIONAL SAGA & DATA LAYER                              │
│   ├── 3-Phase Checkout Saga (Row-Level Locking `SELECT FOR UPDATE`)                    │
│   ├── Integer-Paise Authoritative Ledger (Zero Float Precision Drift)                  │
│   ├── Distributed Idempotency Engine (SHA-256 State Hashing in Redis)                 │
│   ├── Autonomous Background Reconciliation Daemon (Periodic Razorpay Poller)           │
│   └── Dead-Letter Queue (DLQ) & Audit Log Trail (PostgreSQL 16)                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Phase-by-Phase Implementation Specifications

### Phase 1: Database Financial Precision Refactor (Paise-First Architecture)

#### Problem
PostgreSQL columns `orders.total`, `orders.subtotal`, and `products.price` use IEEE-754 `Float` / `double precision`. While idempotency hashing was upgraded to integer paise, the persistence layer is vulnerable to floating-point rounding errors (e.g. `₹199.99` represented as `199.990000000000009`).

#### Implementation Details

1. **Modify Models ([`models/order.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/models/order.py), [`models/product.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/models/product.py))**:
   - Add `total_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)`
   - Add `subtotal_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)`
   - Add `price_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)`
   - Maintain `@property` getters/setters for backward compatibility returning standard rupees:
     ```python
     @property
     def total(self) -> float:
         return self.total_paise / 100.0

     @property
     def price(self) -> float:
         return self.price_paise / 100.0
     ```

2. **Update Core Services**:
   - [`backend/app/services/checkout_saga.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/services/checkout_saga.py): Calculate subtotal and total purely in integer paise arithmetic (`int(item['unit_price_paise'] * qty)`).
   - [`backend/app/services/order_service.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/services/order_service.py): Pass integer paise to Razorpay SDK without float division/multiplication round trips.

---

### Phase 2: Security, Authentication & Role-Based Access Control (RBAC)

#### Problem
Merchant administrative routes (`/api/merchants`, `/api/merchants/{id}/products`, `/api/merchant-chat`, `/api/audit`) have no authentication. Any client can alter stock quantities, view financial sales KPIs, or delete merchant accounts.

#### Implementation Details

1. **Create Merchant Authentication Dependency ([NEW] `backend/app/middleware/auth.py`)**:
   - Implement `get_authenticated_merchant` using FastAPI's `Security(APIKeyHeader(name="X-Merchant-Key"))`.
   - Store hashed API keys (`api_key_hash`) in `merchants` table with SHA-256.
   - Use `hmac.compare_digest` for constant-time cryptographic verification to prevent timing attacks.
   - Inject verified `Merchant` model into route handlers.

2. **Protect Merchant Routes**:
   - [`backend/app/routes/merchants.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/routes/merchants.py): Require auth for `POST /`, `PUT /{id}`, `DELETE /{id}`.
   - [`backend/app/routes/products.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/routes/products.py): Require auth for stock updates, catalog additions, and product deletions.
   - [`backend/app/routes/merchant_chat.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/routes/merchant_chat.py): Verify that the requesting agent session matches the merchant's authenticated key.

3. **CORS & Environment Lockdown**:
   - Update [`backend/app/main.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/main.py): Replace `allow_origins=["*"]` with explicit origins from `settings.cors_origins` (`http://localhost:3000`, production domain).

---

### Phase 3: Autonomous Background Reconciliation & Webhook Persistence

#### Problem
`ReconciliationService` was static code triggered only via manual HTTP call. If a customer paid via QR code/UPI and Razorpay webhook delivery was delayed or dropped, the order remained stuck in `PAYMENT_LINK_SENT` indefinitely unless manually refreshed.

#### Implementation Details

1. **Lifespan Background Daemon ([`backend/app/main.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/main.py))**:
   - Spawn an `asyncio.create_task(reconciliation_daemon())` during application startup.
   - Run on an autonomous 60-second cycle:
     ```python
     async def reconciliation_daemon():
         while True:
             try:
                 async with async_session_maker() as db:
                     await reconciliation_service.reconcile_pending_orders(db, min_age_minutes=3, max_age_minutes=120)
             except asyncio.CancelledError:
                 break
             except Exception as exc:
                 logger.error("Reconciliation worker tick failed: %s", exc)
             await asyncio.sleep(60)
     ```
   - Gracefully cancel and await task termination in the FastAPI `lifespan` shutdown handler.

2. **Persistent Webhook Deduplication ([`backend/app/routes/webhooks.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/routes/webhooks.py))**:
   - Replace the transient `set()` with an atomic Redis `SETNX` operation (`ex=86400`).
   - If Redis is unavailable, fallback to querying the `orders.audit_trail` and `webhook_dead_letters` database tables rather than an in-memory set.

---

### Phase 4: Rate Limiting & Abuse Protection

#### Problem
AI agent endpoints (`/api/chat`, `/api/chat/stream`) and transactional checkout (`/api/orders`) are open to automated scripting or rapid-fire token exhaustion.

#### Implementation Details

1. **Rate Limiting Middleware ([NEW] `backend/app/middleware/rate_limiter.py`)**:
   - Sliding-window counter using Redis `INCR` + `EXPIRE` keyed by client IP or customer phone.
   - Thresholds:
     - `/api/chat/stream`: 30 requests / minute
     - `/api/orders`: 10 requests / minute
     - `/api/merchant-chat`: 60 requests / minute
   - Returns structured `429 Too Many Requests` with `Retry-After` header.

---

### Phase 5: Observability Alignment & Clean Nomenclature

#### Problem
Documentation and frontend UI previously referred to the custom latency profiler as "OpenTelemetry Flamegraphs", inviting immediate critique regarding actual OpenTelemetry collector / exporter compliance.

#### Implementation Details

1. **Nomenclature & Standard Trace Context ([`backend/app/services/trace_service.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/services/trace_service.py))**:
   - Accurately label the service as **Structured Distributed Latency Profiler**.
   - Format trace headers conforming to W3C `traceparent` specifications (`00-{trace_id}-{span_id}-01`).
   - Update documentation (`architecture.md`, `brain.md`, `README.md`) to reflect actual architecture without hyperbole.

---

## 4. Specific File-by-File Changes

### [`backend/app/models/order.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/models/order.py)
- **[MODIFY]**: Replace `subtotal: Float` and `total: Float` with `BigInteger` paise fields (`subtotal_paise`, `total_paise`).
- Add property methods to support floating-point rupee presentation seamlessly.

### [`backend/app/models/product.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/models/product.py)
- **[MODIFY]**: Add `price_paise: BigInteger`, add DB CheckConstraint `stock_quantity >= 0`.

### [`backend/app/models/merchant.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/models/merchant.py)
- **[MODIFY]**: Add `api_key_hash: String(64)` column for authenticated merchant access.

### [`backend/app/middleware/auth.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/middleware/auth.py)
- **[NEW]**: Fast, timing-safe API key dependency `get_authenticated_merchant` with constant-time HMAC comparison.

### [`backend/app/middleware/rate_limiter.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/middleware/rate_limiter.py)
- **[NEW]**: Sliding-window rate limiter using Redis backend with in-memory fallback.

### [`backend/app/services/checkout_saga.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/services/checkout_saga.py)
- **[MODIFY]**: Calculate and store order totals exclusively using `total_paise` integers.

### [`backend/app/services/reconciliation_service.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/services/reconciliation_service.py)
- **[MODIFY]**: Add lock prevention flag so multiple worker ticks don't overlap under heavy database load.

### [`backend/app/main.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/main.py)
- **[MODIFY]**: Register background reconciliation worker in `lifespan`. Lock CORS to configured origins.

### [`backend/app/routes/merchants.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/routes/merchants.py) & [`backend/app/routes/products.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/routes/products.py)
- **[MODIFY]**: Protect administrative endpoints with `Depends(get_authenticated_merchant)`.

### [`backend/tests/test_auth_and_rbac.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/tests/test_auth_and_rbac.py)
- **[NEW]**: Automated test suite for API key authentication, missing header rejections, and multi-tenant key isolation.

### [`backend/tests/test_reconciliation_worker.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/tests/test_reconciliation_worker.py)
- **[NEW]**: Automated test suite for autonomous background polling, order status state transitions, and stock release on expired links.

---

## 5. Verification & Test Plan

### Automated Test Suites
Execute the complete test suite verifying zero regressions across all 55+ test cases:

```bash
# 1. Run all existing tests + new security, auth, precision, and worker tests
pytest backend/tests/ -v

# 2. Run concurrency race condition verification
pytest backend/tests/test_concurrency_race.py -v

# 3. Run distributed saga compensation verification
pytest backend/tests/test_saga_compensation.py -v

# 4. Run adversarial jailbreak & price tampering fuzzing
pytest backend/tests/test_adversarial_jailbreaks.py -v

# 5. Run new authentication & RBAC tests
pytest backend/tests/test_auth_and_rbac.py -v

# 6. Run autonomous reconciliation daemon tests
pytest backend/tests/test_reconciliation_worker.py -v
```

### Manual End-to-End Verification
1. **Merchant Security**:
   - Attempt updating product stock without `X-Merchant-Key` → verify `401 Unauthorized`.
   - Provide valid `X-Merchant-Key` → verify `200 OK` and stock updated.
2. **Autonomous Background Polling**:
   - Create order in `PAYMENT_LINK_SENT` state.
   - Simulate payment in Razorpay test sandbox without webhook firing.
   - Wait 60s → observe background daemon automatically transitioning order to `PAID`.
3. **Conversational Checkout Flow**:
   - Customer opens `/chat`, asks for items under budget limit.
   - Verify server-side pricing enforces exact catalog price.
   - Verify payment link generated and rendered in UI with live telemetry pill indicators.

---

## 6. Reviewer & Judge Handoff Notes

When presenting this project to technical evaluators:
1. **Highlight the 3-Phase Checkout Saga**: Walk them through [`backend/app/services/checkout_saga.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/services/checkout_saga.py) to show row-level locking (`SELECT FOR UPDATE`), database-authoritative pricing, and automated stock compensation.
2. **Demonstrate Concurrency Safety**: Show `backend/tests/test_concurrency_race.py` running 2 simultaneous checkouts on the last remaining stock item.
3. **Demonstrate Defense-in-Depth**: Show `backend/tests/test_adversarial_jailbreaks.py` proving that even if prompt injection bypasses regex filters, server-side price immutability makes it mathematically impossible to checkout with tampered prices.
4. **Show Autonomous Self-Healing**: Point to the background reconciliation daemon in [`backend/app/main.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/main.py) which eliminates reliance on webhooks alone.
