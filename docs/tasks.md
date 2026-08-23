# ✅ MerchantMind — Tasks

> Unified task tracker. `[ ]` todo, `[/]` in progress, `[x]` done.

---

## Phase 1: Foundation & Catalog (Aug 24-25)

### Day 1 Critical — External Accounts
- [ ] Register WhatsApp Business API on Meta for Developers
- [ ] Create Razorpay test account → get `rzp_test_` keys
- [ ] Create Groq account → get API key
- [ ] Create public GitHub repo → `merchantmind`

### Docker & Infrastructure
- [x] Create `docker-compose.yml` (FastAPI, PostgreSQL, Redis, Nginx)
- [x] Create `backend/Dockerfile`
- [/] Create `frontend/Dockerfile` (Next.js initializing)
- [x] Create `nginx/nginx.conf`
- [x] Create `.env.example` with all required vars
- [ ] Verify `docker-compose up --build` works

### CI/CD
- [x] Create `.github/workflows/ci.yml` (lint + test + build)
- [ ] Create `.github/workflows/deploy.yml` (on main push)
- [ ] Verify CI pipeline runs on push

### Backend Foundation
- [x] FastAPI app structure (`app/main.py`, config, routes, services)
- [x] Pydantic settings (`app/config.py`)
- [x] SQLAlchemy 2.0 async models (Merchant, Product, Customer, Order, Conversation, Campaign)
- [ ] Alembic migration setup + initial migration
- [x] Database connection + session management
- [x] Health check endpoint (`GET /health`)
- [x] CORS middleware
- [ ] Error handling middleware

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
- [ ] Test catalog CRUD endpoints
- [ ] Test Schema.org export format

---

## Phase 2: Conversational Checkout (Aug 26-28)

### Groq Agent
- [ ] Groq SDK integration (`pip install groq`)
- [ ] Checkout agent system prompt
- [ ] Natural language → product search mapping
- [ ] Product recommendation with reasoning
- [ ] Cart management (add/remove/modify via natural language)
- [ ] Conversation history tracking (PostgreSQL)
- [ ] Agent fallback: llama-3.3-70b → llama-3.1-8b

### Chat UI (Next.js)
- [ ] Chat message component
- [ ] Product card component (image, name, price, rating)
- [ ] Cart summary sidebar
- [ ] Message input with send button
- [ ] Auto-scroll on new messages
- [ ] Loading state while agent thinks
- [ ] Responsive design (mobile-first)

### API Endpoints
- [ ] `POST /api/chat` — send message, get agent response
- [ ] `GET /api/conversations/{id}` — get conversation history
- [ ] `GET /api/cart/{conversation_id}` — get current cart
- [ ] `POST /api/cart/{conversation_id}/update` — modify cart

---

## Phase 3: Razorpay Payment Flow (Aug 29-30)

### Integration
- [ ] Install Razorpay Python SDK (`pip install razorpay`)
- [ ] Create Razorpay client with test keys
- [ ] `POST /api/orders` — create Razorpay order from cart
- [ ] Generate Payment Link from order
- [ ] Webhook endpoint: `POST /api/webhooks/razorpay`
- [ ] Verify webhook signature
- [ ] Handle `payment.captured` event
- [ ] Handle `payment.failed` event
- [ ] Update order status in database

### Error Handling
- [ ] Payment failure → agent suggests retry
- [ ] Payment link expiry handling
- [ ] Duplicate payment prevention

---

## Phase 4: Upsell + WhatsApp (Aug 31 - Sep 1)

### Upsell Agent
- [ ] Context-aware product suggestions
- [ ] Budget-bounded recommendations
- [ ] "Birthday cake → candles + party combo" logic
- [ ] Upsell reasoning in agent response

### WhatsApp Integration
- [ ] Meta Cloud API setup (webhook URL)
- [ ] Incoming message handler (`POST /api/webhooks/whatsapp`)
- [ ] Webhook verification (GET challenge)
- [ ] Send text messages
- [ ] Send interactive button messages
- [ ] Session management (customer ↔ merchant ↔ conversation)
- [ ] Link WhatsApp flow to existing checkout agent

### Campaign Orchestrator (Stretch Goal)
- [ ] Query: find customers with no order in 14+ days
- [ ] Generate personalized re-engagement message (Groq)
- [ ] Create Razorpay Payment Link with discount
- [ ] Send via WhatsApp
- [ ] Track conversion (did they pay?)

---

## Phase 5: Guardrails + Audit (Sep 2-3)

### Audit Trail
- [ ] Log every agent decision with reasoning (JSON)
- [ ] Log every Razorpay API call (request + response)
- [ ] Log every WhatsApp message (in + out)
- [ ] Audit trail API: `GET /api/orders/{id}/audit`
- [ ] Budget enforcement check before payment

### Failure Handling
- [ ] Groq API timeout → auto-fallback to llama-3.1-8b
- [ ] Razorpay payment failure → retry with different method
- [ ] WhatsApp delivery failure → retry + log
- [ ] Demonstrate 1 intentional failure in demo

### Multi-Tenant Verification
- [ ] Create 2nd merchant ("Fashion Hub")
- [ ] Verify data isolation between merchants
- [ ] Verify each merchant uses their own Razorpay keys

### Deferred Work
- [ ] Finalize Schema.org/JSON-LD export (from Phase 1)

---

## Phase 6: Polish + Demo (Sep 4-5)

### UI Polish
- [ ] Chat interface final design
- [ ] Product cards with real images
- [ ] Cart animations
- [ ] Loading states
- [ ] Error states
- [ ] Mobile responsive

### Demo Video
- [ ] Write final demo script
- [ ] Practice run (time it!)
- [ ] Record demo (≤ 5 min)
- [ ] Edit if needed

### GitHub Repo
- [ ] Write README.md (project description, setup, architecture)
- [ ] Add architecture diagram
- [ ] Add .env.example (no real secrets)
- [ ] Clean commit history
- [ ] Verify repo is public

### Submission
- [ ] Fill Google Form
- [ ] Link GitHub repo
- [ ] Upload/link demo video
- [ ] Submit before Sept 5
