# 📅 MerchantMind — Phases

> Master plan. 6 phases. 13 days. Sept 5 deadline.

---

## Phase 1: Foundation & Catalog
**Timeline**: Aug 24-25 (Day 1-2)
**Status**: 🟡 Starting

### Scope
- Docker Compose setup (FastAPI, PostgreSQL, Redis, Nginx)
- GitHub repo (public) + CI/CD (GitHub Actions)
- FastAPI project structure with Pydantic config
- SQLAlchemy 2.0 models + Alembic migrations
- Merchant catalog CRUD API
- Schema.org/JSON-LD catalog generator
- Sample merchant seed data ("Sweet Bakes Bakery")
- Day 1: Register WhatsApp API, Razorpay test account, Groq API

### Done Criteria
- [ ] `docker-compose up` starts all services
- [ ] GitHub Actions CI passes (lint + test + build)
- [ ] POST/GET/PUT/DELETE products for a merchant works
- [ ] GET `/merchants/{id}/catalog.json` returns Schema.org JSON-LD
- [ ] Sample bakery with 15+ products seeded

### Deliverables
- Working Docker stack
- Catalog API with tests
- CI pipeline green

---

## Phase 2: Conversational Checkout
**Timeline**: Aug 26-28 (Day 3-5)
**Status**: ⏳ Waiting

### Scope
- Groq-powered checkout agent (llama-3.3-70b)
- Natural language product search over merchant catalog
- Product recommendation with reasoning
- Cart management (add, remove, modify)
- Conversation history in PostgreSQL
- Next.js chat UI (web version)
- Product cards with images, prices in chat
- Cart summary sidebar

### Done Criteria
- [ ] User types "I want a chocolate cake under ₹800" → gets relevant results
- [ ] Agent explains WHY it recommended each product
- [ ] Cart persists across messages
- [ ] Chat UI renders product cards beautifully
- [ ] Conversation history is retrievable

### Deliverables
- Working conversational checkout (web)
- Chat UI with product cards

---

## Phase 3: Razorpay Payment Flow
**Timeline**: Aug 29-30 (Day 6-7)
**Status**: ⏳ Waiting

### Scope
- Razorpay test-mode integration (Python SDK)
- Create orders from cart
- Generate Payment Links (shareable via chat/WhatsApp)
- Webhook handler for payment.captured / payment.failed
- Payment status tracking in database
- Error handling: failed payment → retry with different method

### Done Criteria
- [ ] Cart → Razorpay order → Payment Link → Pay with test card → Webhook confirms
- [ ] Payment status updates in real-time
- [ ] Failed payment triggers agent retry flow
- [ ] Order saved with rzp_order_id and rzp_payment_id

### Deliverables
- End-to-end payment flow working
- Payment failure handling demonstrated

---

## Phase 4: Upsell + WhatsApp
**Timeline**: Aug 31 - Sep 1 (Day 8-9)
**Status**: ⏳ Waiting

### Scope
- **Upsell/Cross-sell Agent**: Context-aware suggestions based on cart
- Budget-bounded recommendations
- "Birthday cake? → Add candles + party combo"
- **WhatsApp Business API**: Meta Cloud API integration
- Incoming message webhook handler
- Outgoing messages (text + interactive buttons)
- Session management per customer per merchant
- **Campaign Orchestrator** (if time permits):
  - Identify dormant customers (no order in 14+ days)
  - Generate personalized re-engagement messages
  - Send Razorpay Payment Links via WhatsApp

### Done Criteria
- [ ] Agent suggests relevant upsells when items added to cart
- [ ] Upsell respects customer's stated budget
- [ ] WhatsApp: Send message → receive → agent responds → payment link sent
- [ ] Campaign: dormant customers identified and messaged (stretch goal)

### Deliverables
- Upsell agent working in checkout flow
- WhatsApp end-to-end flow (at least sandbox)

---

## Phase 5: Guardrails + Audit
**Timeline**: Sep 2-3 (Day 10-11)
**Status**: ⏳ Waiting

### Scope
- Audit trail system: every agent decision logged with reasoning
- Every Razorpay API call logged with request/response
- Budget enforcement (won't exceed customer's stated limit)
- User confirmation gates before payment
- Failure handling: Groq down → fallback to llama-3.1-8b
- WhatsApp delivery failure → retry + notify
- Schema.org export finalization (deferred from Phase 1)
- Multi-merchant data isolation verification

### Done Criteria
- [ ] Full audit trail viewable for any order
- [ ] Budget enforcement prevents overspending
- [ ] Intentional failure → graceful handling demonstrated
- [ ] 2+ merchants with isolated data verified

### Deliverables
- Audit trail dashboard/API
- Failure handling demo-ready

---

## Phase 6: Polish + Demo
**Timeline**: Sep 4-5 (Day 12-13)
**Status**: ⏳ Waiting

### Scope
- UI/UX polish (chat interface, product cards, cart)
- Demo video recording (MAX 5 minutes)
- GitHub repo cleanup (README, architecture doc, .env.example)
- Remove secrets, clean commit history
- Submission via Google Form

### Done Criteria
- [ ] Demo video is ≤ 5 minutes and compelling
- [ ] GitHub repo is public with clear README
- [ ] Architecture doc is in repo
- [ ] .env.example has all required vars (no real secrets)
- [ ] Submitted via Google Form before Sept 5

### Deliverables
- 5-min demo video
- Public GitHub repo
- Submitted application
