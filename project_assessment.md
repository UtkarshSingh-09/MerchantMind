# MerchantMind — Zero-Buttering Technical Autopsy

*Every file read. Every pattern inspected. Every weakness documented.*

---

## 1. What This Project Actually Is

MerchantMind is a **conversational commerce platform** for Razorpay merchants. A customer opens a chat interface, browses products via natural language, builds a cart, and pays via an auto-generated Razorpay payment link. A merchant can use a separate admin console to view sales and manage inventory.

The system is built as:
- **Backend**: Python FastAPI (async) + PostgreSQL 16 + Redis 7 + Groq LLM API + Razorpay SDK
- **Frontend**: Next.js 16 (App Router) + TypeScript + Tailwind CSS + Framer Motion
- **Infra**: Docker Compose (5 services: backend, frontend, postgres, redis, nginx)

**Total codebase**: ~13,191 lines of application code + 1,430 lines of tests across 17 test files.

---

## 2. Backend Architecture — File-by-File Honest Assessment

### 2.1 Agents (3,165 lines across 5 files)

| File | Lines | What It Does | Honest Take |
|:---|:---:|:---|:---|
| [`agent_router.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/agents/agent_router.py) | 128 | Routes to Discovery/Shopping/Merchant agent based on `merchant_id` presence | **Simple but correct.** The routing logic is just a null check on `merchant_id`. No ML-based intent disambiguation. No timeout handling on agent calls. The senior dev was right — this is a clean skeleton without connective tissue. |
| [`shopping_agent.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/agents/shopping_agent.py) | 1,021 | Core conversational shopping agent with LLM tool-use, cart management, upselling | **The heaviest file in the project.** Contains the LLM system prompt, tool definitions for add/remove/search/checkout, and the ReAct loop. This is where the actual AI behavior lives. Genuine tool-calling via Groq function-calling API. |
| [`discovery_agent.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/agents/discovery_agent.py) | 723 | Multi-store search, budget extraction, store-locking handoff | Functional. Queries across multiple merchants and locks the session to one once chosen. Budget extraction is delegated to `budget_extractor.py`. |
| [`checkout_agent.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/agents/checkout_agent.py) | 894 | Handles checkout flows, fulfillment mode selection, payment link generation | Large file, mostly orchestration around `order_service` and `checkout_saga`. |
| [`merchant_agent.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/agents/merchant_agent.py) | 399 | Merchant-facing natural language admin (inventory, sales queries) | Tool-calling for stock overrides, sales queries. **No authentication check here** — any request routed to this agent can modify stock. The auth gap the senior dev noted is real. |

### 2.2 Services (3,460 lines across 23 files)

#### Genuinely Strong Services:

| Service | Lines | Honest Take |
|:---|:---:|:---|
| [`checkout_saga.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/services/checkout_saga.py) | 256 | **The best-engineered file in the project.** Real 3-phase saga: (1) Row-lock stock with `SELECT FOR UPDATE`, (2) Create Razorpay order + payment link, (3) Commit or compensate. If Razorpay API fails, stock is explicitly restored. Server-side price immutability now enforced — prices come from DB, not client. Idempotency key checked before any work begins. |
| [`idempotency_service.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/services/idempotency_service.py) | 76 | SHA-256 hash over `(conv_id, merchant_id, sorted_items_in_paise, total_in_paise)`. Redis primary cache with in-memory fallback. Now uses integer paise to eliminate float drift. **Solid.** |
| [`razorpay_service.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/services/razorpay_service.py) | 150 | Real Razorpay SDK calls (`razorpay.Client`). Creates orders in paise, generates payment links, verifies HMAC-SHA256 webhook signatures. Has a test-mode fallback when sandbox quota is exceeded. **This is real integration, not mocked.** |
| [`reconciliation_service.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/services/reconciliation_service.py) | 117 | Polls orders stuck in `PAYMENT_LINK_SENT` between 5–60 minutes, queries Razorpay API directly, marks paid or releases stock for expired links. **Actually useful for a real payments system.** |
| [`entity_resolver.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/services/entity_resolver.py) | 179 | Parses compound cart edits ("remove that cake and add 2 coffees") using Fast-tier LLM → then fuzzy-matches against catalog using `SequenceMatcher`. Handles ambiguity with clarification prompts. **Thoughtful design.** |
| [`circuit_breaker.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/services/circuit_breaker.py) | 67 | Async timeout circuit breaker (3.5s default) with consecutive-failure threshold and half-open recovery. **Clean and tested.** |

#### Adequate Services:

| Service | Lines | Honest Take |
|:---|:---:|:---|
| [`prompt_sanitizer.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/services/prompt_sanitizer.py) | 83 | 12 regex patterns catching: system overrides, control tokens, price tampering, roleplay, base64, markdown injection. **First line of defense only** — sophisticated paraphrased attacks will still pass through. But the server-side price immutability in `checkout_saga.py` is the real defense layer, making the LLM's output irrelevant to pricing. |
| [`groq_client.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/services/groq_client.py) | 135 | Dual-tier with exponential backoff: `gpt-oss-20b` for fast extraction, `gpt-oss-120b` for reasoning, with automatic fallback between tiers. **Real retry logic with increasing delay.** |
| [`upsell_engine.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/services/upsell_engine.py) | 151 | Association-rule-based cross-sell (Cakes → Party Supplies, Pastries → Beverages). **Budget-bounded** — suggestions are filtered by `budget_remaining`. Not ML-based, but correct for a hackathon scope. |
| [`budget_extractor.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/services/budget_extractor.py) | 87 | LLM-based structured extraction returning `{budget_amount, is_hard_limit, currency}`. Uses Fast-tier for speed. |
| [`dlq_service.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/services/dlq_service.py) | 58 | Records failed webhooks into `webhook_dead_letters` table. Retrieves pending entries for retry (max 5 retries). **Simple but present.** |
| [`trace_service.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/services/trace_service.py) | 91 | Custom span-based latency tracking using `time.perf_counter()`. Not real OpenTelemetry (no OTel SDK, no Jaeger/Zipkin export). It's a **homegrown microsecond profiler** that feeds the frontend flamegraph. **Calling it "OpenTelemetry" is a stretch** — it's structured latency tracing that looks OTel-inspired. |

#### Weaker / Thin Services:

| Service | Lines | Honest Take |
|:---|:---:|:---|
| [`whatsapp_service.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/services/whatsapp_service.py) | 164 | Meta Cloud API message sender. **Cannot be live-demoed** without Meta-verified sandbox phone. It's code that would work if credentials were configured, but it's untestable in a live demo. |
| [`whatsapp_session.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/services/whatsapp_session.py) | 91 | In-memory session store for WhatsApp conversations. **Not production-grade** (no persistence, lost on restart). |
| [`campaign_service.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/services/campaign_service.py) | 111 | Abandoned cart recovery and campaign creation. **Feature exists but thin** — no actual scheduled delivery mechanism. |
| [`memory_service.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/services/memory_service.py) | 105 | Summarizes conversation context for LLM context window management. |
| [`inventory_sync_service.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/services/inventory_sync_service.py) | 150 | Parses UrbanPiper POS webhook payloads. **Never tested against real POS output.** |

### 2.3 Models (8 tables, 452 lines)

| Table | Key Columns | Notes |
|:---|:---|:---|
| `merchants` | id, name, email, phone, latitude, longitude, store_address | GPS coordinates for Haversine distance. |
| `products` | id, merchant_id, name, price, category, stock_quantity, in_stock, schema_json | `price` is **Float, not Decimal/Integer** — the senior dev's critique. `stock_quantity` was added later. `schema_json` stores Schema.org JSON-LD. |
| `customers` | id, merchant_id, name, phone, email | Linked per merchant (multi-tenant). |
| `conversations` | id, merchant_id, customer_id, messages (JSONB), cart (JSONB), channel | The entire conversation + cart state lives in a single JSONB column. |
| `orders` | id, merchant_id, conversation_id, items (JSONB), **subtotal (Float), total (Float)**, rzp_order_id, rzp_payment_link_id, payment_link, status (Enum), fulfillment_mode, delivery coords, audit_trail (JSONB) | **`total` and `subtotal` are Float columns** — this is the exact smell the senior dev flagged. For a payments system, these should be Integer paise or Decimal. The idempotency layer now normalizes to paise before hashing, but the DB column itself is still Float. |
| `campaigns` | id, merchant_id, name, target_segment, sent_count, converted_count, revenue_generated | Campaign tracking. |
| `audit_logs` | id, event_type (Enum), merchant_id, conversation_id, order_id, action, reasoning, input_data (JSONB), output_data (JSONB) | Immutable decision log. Events: CHECKOUT_INITIATED, PAYMENT_CAPTURED, PAYMENT_FAILED, BUDGET_VIOLATION, BUDGET_CHECK, AGENT_DECISION. |
| `webhook_dead_letters` | id, event_id, event_type, source, payload (JSONB), error_message, retry_count, status | Dead-letter queue for failed webhooks. |

### 2.4 Routes (11 route modules, 1,296 lines)

| Route | Endpoints | Honest Take |
|:---|:---|:---|
| `/api/chat` | POST `/`, POST `/stream`, GET `/{id}`, PUT `/{id}/cart` | Core chat with SSE streaming. Cart CRUD. **Working and tested.** |
| `/api/orders` | POST `/`, GET `/{id}`, GET `/{id}/tracking-data` | Order creation delegates to `checkout_saga`. Tracking returns simulated GPS. |
| `/api/webhooks/razorpay` | POST | HMAC verification → Redis dedup → `handle_payment_captured` / `handle_payment_failed` → DLQ on error. **This is real webhook handling.** |
| `/api/webhooks/whatsapp` | GET (verify), POST (message) | Meta verification challenge + message routing. |
| `/api/merchants` | CRUD | Standard REST. **No auth required** — anyone can create/delete merchants. |
| `/api/merchants/{id}/products` | CRUD + JSON-LD export | Standard product CRUD with Schema.org export. |
| `/api/merchant-chat` | POST | Routes to MerchantAgent. **No auth.** |
| `/api/campaigns` | GET, POST | Campaign listing and creation. |
| `/api/audit` | GET `/conversation/{id}`, GET `/merchant/{id}` | Audit trail queries. |
| `/api/analytics/benchmarks` | GET | Triggers reconciliation or returns eval results. |

---

## 3. Frontend — File-by-File

**Total frontend application code**: ~4,619 lines across 14 files.

| File | Lines | What It Does | Honest Take |
|:---|:---:|:---|:---|
| [`chat/page.tsx`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/frontend/src/app/chat/page.tsx) | 955 | Customer storefront: merchant selector, SSE streaming chat, cart sidebar, checkout flow | **The most complete page.** Dual-mode (Discovery/Shopping), live ReAct event stream display, real checkout with Razorpay link generation, order tracking with payment polling. Heavy use of Framer Motion. |
| [`merchant/page.tsx`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/frontend/src/app/merchant/page.tsx) | 674 | Merchant admin: chat-based ops console, inventory management, sales KPIs | Natural language merchant tools. |
| [`AgentReasoningPanel.tsx`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/frontend/src/components/AgentReasoningPanel.tsx) | 267 | Side drawer showing reasoning logs + dynamic flamegraph bars | Flamegraph widths driven by `duration_ms / total_ms * 100` from backend spans. |
| [`CartSidebar.tsx`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/frontend/src/components/CartSidebar.tsx) | 365 | Cart management, delivery/pickup mode selector, Razorpay checkout button | Handles fulfillment mode, order tracking link. |
| [`ChatMessage.tsx`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/frontend/src/components/ChatMessage.tsx) | 298 | Renders chat bubbles, product recommendation cards, payment links | Markdown rendering, product cards with add-to-cart. |
| [`ChatInput.tsx`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/frontend/src/components/ChatInput.tsx) | 276 | Input bar with quick suggestions, mic button UI | Suggestion chips change per merchant type. |
| [`ProductCard.tsx`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/frontend/src/components/ProductCard.tsx) | 340 | Product card with stock badge, quantity controls | Stock-awareness (shows "Out of Stock" badge). |
| [`api.ts`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/frontend/src/lib/api.ts) | 505 | Typed fetch client for all backend endpoints, SSE stream parser | EventSource-based SSE consumer, cart sync, order creation. |
| Landing page components (`ParticleConstellation`, `CommerceDataChaos`, `ConvergenceSingularity`, etc.) | ~938 | Animated landing page with particle effects, terminal CTA | **Pure visual polish.** These are cosmetic — impressive for demo but not functional substance. |

---

## 4. Testing — Honest Assessment

**38 tests across 17 files, 1,430 lines of test code. All 38 pass in ~42s.**

### Tests That Are Genuinely Good:

| Test | What It Proves |
|:---|:---|
| [`test_concurrency_race.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/tests/test_concurrency_race.py) | Two parallel buyers on the last item → exactly 1 succeeds, 1 fails, stock = 0. **This is above-bar for a hackathon.** |
| [`test_saga_compensation.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/tests/test_saga_compensation.py) | Injected 504 gateway timeout → saga rollback restores stock. **Real distributed failure test.** |
| [`test_adversarial_jailbreaks.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/tests/test_adversarial_jailbreaks.py) | 10 adversarial payloads flagged by sanitizer + price tampering (₹0.01) overridden by DB price (₹850). **Server-side immutability proven.** |
| [`test_idempotency_precision.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/tests/test_idempotency_precision.py) | `0.1 + 0.2` float drift produces identical hash to `0.30`. Item order permutation invariance. |
| [`test_circuit_breaker.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/tests/test_circuit_breaker.py) | Timeout triggers fallback. Consecutive failures open circuit. |
| [`test_orders.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/tests/test_orders.py) | Order creation → status polling → webhook capture (paid) → webhook capture (failed). End-to-end order lifecycle. |
| [`test_multi_tenant.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/tests/test_multi_tenant.py) | Two merchants' catalogs and orders are properly isolated. Schema.org JSON-LD export works. |

### Tests That Are Standard CRUD:
`test_merchants.py`, `test_products.py`, `test_chat.py`, `test_health.py` — necessary but not differentiating.

### What's NOT Tested:
- No load/stress testing (100 concurrent users)
- No fuzzing of the entity resolver with adversarial product names
- No test for the WhatsApp flow end-to-end
- No test that `reconciliation_service` actually transitions order states
- No test for float precision in the actual `order.total` DB column (only in idempotency hashing)

---

## 5. Infrastructure & DevOps

| Component | What's There | Honest Take |
|:---|:---|:---|
| `docker-compose.yml` | 5 services (backend, frontend, postgres, redis, nginx) with healthchecks and named volumes | **Clean and complete.** Postgres healthcheck gates backend startup. |
| `Dockerfile` (backend) | Python slim + pip install | Standard. |
| `nginx/nginx.conf` | Reverse proxy for frontend and backend | Basic but functional. |
| `alembic/` | Alembic migration setup | Present but **tables are auto-created via `Base.metadata.create_all` in dev** — migrations aren't actively used. |
| `.env` | Real Razorpay test keys, Groq API key, Postgres credentials | **Credentials committed to repo** — `.env` is in `.gitignore` but the `.env` file exists locally with real keys. |

---

## 6. Documentation (10 files in `docs/`)

| Doc | Lines | What It Covers |
|:---|:---:|:---|
| `architecture.md` | ~250 | System diagrams, agent personas, state machine flows |
| `unit_economics.md` | ~63 | Token cost breakdown with variance distributions |
| `api_reference.md` | ~100 | Endpoint reference |
| `demo_script.md` | ~150 | Step-by-step demo walkthrough |
| `submission_checklist.md` | ~50 | Hackathon submission items |
| `problems.md` | ~50 | Known issues |
| `brain.md` | ~60 | Agent reasoning architecture |

**The documentation is thorough for a hackathon.** The senior dev's criticism about promotional register ("Zero Inventory Leaked," "98.1% cheaper") in the unit economics doc is fair — some claims are presented with more confidence than the evidence warrants.

---

## 7. What's Genuinely Good (No Buttering — These Are Real Strengths)

1. **`checkout_saga.py` is legitimate distributed transaction engineering.** `SELECT FOR UPDATE` → Razorpay API → Commit/Compensate, within a single async SQLAlchemy session. The compensation path explicitly restores `stock_quantity` and logs an audit event. Most hackathon chatbots skip this entirely.

2. **Server-side price immutability.** The checkout saga now reads prices from PostgreSQL under row lock. If an LLM hallucinates `price: 0` or an attacker sends `price: 0.01`, it's discarded. This is a real defense-in-depth pattern that matters for payments.

3. **Real Razorpay integration** (not mocked). `razorpay.Client` SDK creates actual orders and payment links in test mode. HMAC-SHA256 webhook verification. Payment link polling in reconciliation.

4. **The concurrency test is genuine.** `test_concurrency_race.py` runs two `asyncio.gather` checkouts on `stock_quantity=1` and proves exactly one succeeds. This is the kind of test that separates engineering from demos.

5. **Entity resolution with ambiguity handling.** The resolver parses "remove that cake and add 2 coffees" via Fast-tier LLM, then fuzzy-matches against the catalog with confidence scoring and generates clarification prompts when ambiguous. That's non-trivial.

6. **Integer-paise idempotency hashing** eliminates the classic `0.1 + 0.2 ≠ 0.3` float-equality bug in deduplication keys.

7. **Dual-tier LLM routing** is a real cost optimization pattern — cheap model for structured extraction, expensive model for reasoning.

---

## 8. What's Weak or Missing (No Buttering — These Are Real Problems)

### Critical Issues:

1. **`order.total` and `order.subtotal` are still `Float` columns in PostgreSQL.** The idempotency layer normalizes to paise, but the actual stored monetary value in the database is still a Python float → PostgreSQL `double precision`. For a payments system, this is a data model smell. Should be `Integer` (paise) or `Numeric(12, 2)`.

2. **Zero authentication/authorization.** No `X-Merchant-Key`, no JWT, no session tokens. Anyone who knows the endpoint can:
   - Create/delete merchants (`POST /api/merchants`)
   - Modify any catalog (`PUT /api/merchants/{id}/products/{id}`)
   - Trigger merchant agent operations (`POST /api/merchant-chat`)
   - View any audit trail (`GET /api/audit/merchant/{id}`)
   
   For a hackathon demo this is acceptable if acknowledged. For the "production-grade" framing the docs use, it's a gap.

3. **`trace_service.py` is not OpenTelemetry.** It's a custom `time.perf_counter()` profiler that emits span-like JSON. There's no OTel SDK, no W3C trace context, no collector, no Jaeger/Zipkin export. Calling it "OpenTelemetry" in documentation is inaccurate. Call it "structured latency tracing" and it's fine.

4. **WhatsApp channel is untestable in live demo.** The code exists and would work with verified Meta credentials, but without those, it's dead code during a demo. A judge who asks "show me the WhatsApp flow" will get nothing.

5. **CORS is `allow_origins=["*"]`** — wide open. Fine for dev, but contradicts "production-grade" claims.

### Moderate Issues:

6. **Reconciliation service is never automatically scheduled.** It exists as code that can be triggered manually via `/api/analytics/benchmarks`, but there's no background worker, no cron, no APScheduler. In a real deployment, stuck orders would stay stuck until someone manually hits the endpoint.

7. **Webhook deduplication uses an in-memory set (`_PROCESSED_WEBHOOK_EVENTS`).** On server restart, all dedup state is lost. Redis dedup is attempted but failures are silently swallowed. In a multi-instance deployment, the in-memory set provides zero protection.

8. **Campaign service has no delivery mechanism.** You can create campaigns and they're stored in PostgreSQL, but nothing actually sends messages on a schedule.

9. **The upsell engine is rule-based, not ML.** Hardcoded category association rules (Cakes → Party Supplies). This is fine for the scope, but calling it "intelligent" or "AI-powered" upselling is a stretch — it's a lookup table with budget filtering.

10. **No rate limiting on any endpoint.** A malicious client can spam `/api/chat` or `/api/orders` without throttling.

---

## 9. Code Quality Metrics

| Metric | Value |
|:---|:---|
| Total application code | **13,191 lines** |
| Total test code | **1,430 lines** |
| Test-to-code ratio | **~10.8%** (adequate for hackathon, low for production) |
| Passing tests | **38/38** |
| Backend services | **23 service modules** |
| Database tables | **8 tables** |
| API endpoints | **~25 endpoints** |
| External integrations | **3** (Razorpay SDK, Groq API, Meta WhatsApp API) |
| Docker services | **5** (backend, frontend, postgres, redis, nginx) |

---

## 10. Honest Rating: 7.5 / 10

### Why 7.5 and Not Higher:

The transactional engineering (`checkout_saga.py`, concurrency test, idempotency, reconciliation, DLQ) is **genuinely above the hackathon bar** — most teams building "AI chatbot for shopping" never think about row locks, saga compensation, or webhook deduplication. The server-side price immutability and adversarial jailbreak test suite added in the latest round address the senior dev's most critical feedback.

But:
- **Float for money columns** is still in the DB schema (only fixed in idempotency hashing, not in the `orders` table itself)
- **Zero auth** on all endpoints
- **Trace service misrepresented as OpenTelemetry**
- **WhatsApp is dead code** for demo purposes
- **No background workers** for reconciliation or campaigns
- **Documentation tone** still leans promotional in places

### What Would Move It to 8.5+:
1. Change `order.total` and `order.subtotal` to `Integer` (paise) or `Numeric(12,2)` in the SQLAlchemy model
2. Add even basic API key auth on merchant mutation endpoints
3. Rename "OpenTelemetry" to "Structured Latency Tracing" in docs
4. Add a background reconciliation worker (even a simple `asyncio.create_task` at startup)
5. Remove WhatsApp references from the demo flow if it can't be shown live

### What Would Move It to 9+:
All of the above, plus:
- Real OTel SDK integration with collector
- Load testing results (even 50 concurrent users)
- Decimal/Integer money types end-to-end
- JWT or API key auth with role separation
- Fuzzing suite for entity resolver edge cases

---

## 11. Summary Table

| Dimension | Score | Notes |
|:---|:---:|:---|
| **Architecture & System Design** | 7.5/10 | Clean layering, but thin agent connective tissue |
| **Transactional Engineering** | 8.5/10 | Saga + row locks + idempotency + compensation + reconciliation + DLQ. Strongest dimension. |
| **Security** | 6/10 | Multi-layer sanitizer + price immutability are good. Zero auth, open CORS, no rate limiting are bad. |
| **Testing** | 7.5/10 | Concurrency + saga + adversarial + precision tests are above-bar. No load/fuzz testing. |
| **Frontend / UI** | 8/10 | Polished, animated, responsive. SSE streaming works. Visual landing page is impressive for demos. |
| **Razorpay Integration** | 8.5/10 | Real SDK, real payment links, HMAC verification, webhook handling, reconciliation. Not mocked. |
| **LLM / AI Engineering** | 7/10 | Dual-tier routing, tool-calling, entity resolution. Upsell is rule-based, not learned. |
| **Documentation** | 7.5/10 | Thorough but occasionally promotional. |
| **DevOps / Infra** | 7/10 | Docker Compose is clean. No CI/CD, no staging, no health dashboards. |
| **Code Quality** | 7.5/10 | Well-structured, consistent patterns. Float money is the main smell. |
| **Overall** | **7.5/10** | Strong transactional core, real Razorpay integration, and above-average testing lift this above typical hackathon chatbots. Loses points for auth gaps, Float money, misrepresented tracing, and undemostrable WhatsApp. |
