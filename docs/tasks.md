# ✅ MerchantMind — Tasks

> Unified task tracker. `[ ]` todo, `[/]` in progress, `[x]` done.

---

## Phase 1: Foundation & Catalog (Aug 24-25)

### Day 1 Critical — External Accounts
- [x] Register WhatsApp Business API on Meta for Developers
- [x] Create Razorpay test account → get `rzp_test_` keys
- [x] Create Groq account → get API key
- [x] Create public GitHub repo → `merchantmind`

### Docker & Infrastructure
- [x] Create `docker-compose.yml` (FastAPI, PostgreSQL, Redis, Nginx)
- [x] Create `backend/Dockerfile`
- [x] Create `frontend/Dockerfile` (Next.js initializing)
- [x] Create `nginx/nginx.conf`
- [x] Create `.env.example` with all required vars
- [x] Verify `docker-compose up --build` works

### CI/CD
- [x] Create `.github/workflows/ci.yml` (lint + test + build)
- [x] Create `.github/workflows/deploy.yml` (on main push)
- [x] Verify CI pipeline runs on push

### Backend Foundation
- [x] FastAPI app structure (`app/main.py`, config, routes, services)
- [x] Pydantic settings (`app/config.py`)
- [x] SQLAlchemy 2.0 async models (Merchant, Product, Customer, Order, Conversation, Campaign)
- [x] Alembic migration setup + initial migration
- [x] Database connection + session management
- [x] Health check endpoint (`GET /health`)
- [x] CORS middleware
- [x] Error handling middleware

### Merchant Catalog API
- [x] `POST /api/merchants` — register merchant
- [x] `GET /api/merchants/{id}` — get merchant
- [x] `POST /api/merchants/{id}/products` — add product
- [x] `GET /api/merchants/{id}/products` — list products
- [x] `PUT /api/merchants/{id}/products/{pid}` — update product
- [x] `DELETE /api/merchants/{id}/products/{pid}` — delete product
- [x] `GET /api/merchants/{id}/catalog.json` — Schema.org JSON-LD export

### Seed Data
- [x] Create seed script (`scripts/seed.py`)
- [x] Sample merchant: "Sweet Bakes Bakery"
- [x] 16 products (cakes, pastries, combos, breads, beverages) with prices, descriptions, categories

### Tests
- [x] Test health check endpoint
- [x] Test catalog CRUD endpoints
- [x] Test Schema.org export format

---

## Phase 2: Conversational Checkout (Aug 26-28)

### Groq Agent
- [x] Groq SDK integration (`pip install groq`)
- [x] Checkout agent system prompt
- [x] Natural language → product search mapping
- [x] Product recommendation with reasoning
- [x] Cart management (add/remove/modify via natural language)
- [x] Conversation history tracking (PostgreSQL)
- [x] Agent fallback: model fallback support

### Chat UI (Next.js)
- [x] Chat message component
- [x] Product card component (image, name, price, rating)
- [x] Cart summary sidebar
- [x] Message input with send button
- [x] Auto-scroll on new messages
- [x] Loading state while agent thinks
- [x] Responsive design (mobile-first)

### API Endpoints
- [x] `POST /api/chat` — send message, get agent response
- [x] `GET /api/conversations/{id}` — get conversation history
- [x] `GET /api/cart/{conversation_id}` — get current cart
- [x] `POST /api/cart/{conversation_id}/update` — modify cart

---

## Phase 3: Razorpay Payment Flow (Aug 29-30)

### Integration
- [x] Install Razorpay Python SDK (`pip install razorpay`)
- [x] Create Razorpay client with test keys
- [x] `POST /api/orders` — create Razorpay order from cart
- [x] Generate Payment Link from order
- [x] Webhook endpoint: `POST /api/webhooks/razorpay`
- [x] Verify webhook signature
- [x] Handle `payment.captured` event
- [x] Handle `payment.failed` event
- [x] Update order status in database

### Error Handling
- [x] Payment failure → agent suggests retry
- [x] Payment link expiry handling
- [x] Duplicate payment prevention (idempotent webhook)

---

## Phase 4: Upsell + WhatsApp (Aug 31 - Sep 1)

### Upsell Agent
- [x] Context-aware product suggestions
- [x] Budget-bounded recommendations
- [x] "Birthday cake → candles + party combo" logic
- [x] Upsell reasoning in agent response

### WhatsApp Integration
- [x] Meta Cloud API setup (webhook URL)
- [x] Incoming message handler (`POST /api/webhooks/whatsapp`)
- [x] Webhook verification (GET challenge)
- [x] Send text messages
- [x] Send interactive button messages
- [x] Session management (customer ↔ merchant ↔ conversation)
- [x] Link WhatsApp flow to existing checkout agent

### Campaign Orchestrator (Stretch Goal)
- [x] Query: find customers with no order in 14+ days
- [x] Generate personalized re-engagement message (Groq)
- [x] Create Razorpay Payment Link with discount
- [x] Send via WhatsApp
- [x] Track conversion (did they pay?)

---

## Phase 5: Guardrails + Audit (Sep 2-3)

### Audit Trail
- [x] Log every agent decision with reasoning (JSON)
- [x] Log every Razorpay API call (request + response)
- [x] Log every WhatsApp message (in + out)
- [x] Audit trail API: `GET /api/orders/{id}/audit`
- [x] Budget enforcement check before payment

### Failure Handling
- [x] Groq API timeout → auto-fallback with exponential backoff
- [x] Razorpay payment failure → audit log + retry with different method
- [x] WhatsApp delivery failure → retry + log
- [x] Demonstrate 1 intentional failure in demo (budget guardrail breach)

### Multi-Tenant Verification
- [x] Create 2nd merchant ("Fashion Hub")
- [x] Verify data isolation between merchants
- [x] Verify each merchant uses their own Razorpay keys

### Deferred Work
- [x] Finalize Schema.org/JSON-LD export (from Phase 1)

---

## Phase 6: Polish + Demo (Sep 4-5)

### UI Polish
- [x] Chat interface final design
- [x] Product cards with real images & gradient borders
- [x] Cart animations & steppers
- [x] Loading states & typing indicator
- [x] Error states & toast notifications
- [x] Mobile responsive drawer

### Demo Video
- [x] Write final demo script (`docs/demo_script.md`)
- [ ] Practice run (time it!)
- [ ] Record demo (≤ 5 min)
- [ ] Edit if needed

### GitHub Repo
- [x] Write README.md (project description, setup, architecture)
- [x] Add architecture diagram & API reference
- [x] Add .env.example (no real secrets)
- [x] Clean commit history & .gitignore verified
- [ ] Verify repo is public

### Submission
- [ ] Fill Google Form
- [ ] Link GitHub repo
- [ ] Upload/link demo video
- [ ] Submit before Sept 5
