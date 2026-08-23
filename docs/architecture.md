# 🏗️ MerchantMind — Architecture

> Single source of truth. Updated when architecture changes.

---

## System Overview

**MerchantMind** is an AI-powered growth agent for Razorpay merchants. It helps merchants grow revenue through conversational checkout, intelligent upselling, and campaign orchestration — all with payments via Razorpay.

## High-Level Architecture

```
                    ┌──────────────────────┐
                    │     NGINX (Docker)    │
                    │   Reverse Proxy       │
                    │   Port 80 → 3000/8000 │
                    └──────────┬───────────┘
                               │
                    ┌──────────┴───────────┐
                    │                      │
            ┌───────┴──────┐    ┌──────────┴──────┐
            │  NEXT.JS     │    │   FASTAPI        │
            │  Frontend    │    │   Backend        │
            │  Port 3000   │    │   Port 8000      │
            │              │    │                  │
            │  • Chat UI   │    │  • REST API      │
            │  • Dashboard │    │  • Agent Engine  │
            │  • Cart View │    │  • Webhook Hdlr  │
            └──────────────┘    └────────┬─────────┘
                                         │
                      ┌──────────────────┼──────────────────┐
                      │                  │                  │
               ┌──────┴─────┐    ┌───────┴──────┐   ┌──────┴──────┐
               │ GROQ API   │    │  RAZORPAY    │   │  WHATSAPP   │
               │ (LLM)      │    │  (Payments)  │   │  (Meta API) │
               │            │    │              │   │             │
               │ llama-3.3  │    │ Test Mode    │   │ Cloud API   │
               │ -70b       │    │ Orders       │   │ Send/Recv   │
               │            │    │ Pay Links    │   │ Webhooks    │
               └────────────┘    │ Webhooks     │   └─────────────┘
                                 └──────────────┘
                      │
       ┌──────────────┼──────────────┐
       │              │              │
┌──────┴─────┐ ┌──────┴─────┐ ┌─────┴──────┐
│ PostgreSQL │ │   Redis    │ │ Audit Log  │
│ (Docker)   │ │  (Docker)  │ │ (in PG)    │
│            │ │            │ │            │
│ • Merchants│ │ • Sessions │ │ • Decisions│
│ • Products │ │ • Cache    │ │ • API calls│
│ • Orders   │ │ • Agent    │ │ • Reasoning│
│ • Customers│ │   state    │ └────────────┘
│ • Convos   │ └────────────┘
└────────────┘
```

## Agent Architecture

```
Customer Message: "I want a chocolate cake for a birthday, under ₹800"
    │
    ▼
┌─────────────────────────────────────────────┐
│            ORCHESTRATOR AGENT               │
│         (Groq: llama-3.3-70b)               │
│                                             │
│  1. Parse intent → PRODUCT_SEARCH           │
│  2. Extract: category=cake, flavor=choco,   │
│     occasion=birthday, budget=800           │
│  3. Query merchant catalog (SQL)            │
│  4. Rank results by relevance               │
│  5. Generate recommendation + reasoning     │
│  6. Check: should I upsell?                 │
│     → YES: birthday → candles, combo        │
│  7. Present options to customer             │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│     Customer: "I'll take option 2,          │
│                add candles too"              │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│            CHECKOUT FLOW                    │
│                                             │
│  1. Update cart (cake + candles)             │
│  2. Calculate total: ₹700                   │
│  3. Verify: ₹700 < ₹800 budget ✓           │
│  4. Create Razorpay Order (test mode)       │
│  5. Generate Payment Link                   │
│  6. Send to customer (chat / WhatsApp)      │
│  7. Wait for webhook: payment.captured      │
│  8. Confirm order to customer               │
│  9. Log FULL audit trail                    │
└─────────────────────────────────────────────┘
```

## Data Model

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   MERCHANT   │─1:N─→│   PRODUCT    │      │   CUSTOMER   │
│              │      │              │      │              │
│ id (UUID)    │      │ id (UUID)    │      │ id (UUID)    │
│ name         │      │ merchant_id  │      │ phone        │
│ email        │      │ name         │      │ name         │
│ rzp_key_id   │      │ price        │      │ email        │
│ rzp_secret   │      │ description  │      │ merchant_id  │
│ whatsapp_no  │      │ category     │      │ last_order_at│
│ is_active    │      │ tags[]       │      │ total_spent  │
│ created_at   │      │ image_url    │      │ created_at   │
└──────────────┘      │ in_stock     │      └──────┬───────┘
       │              │ schema_json  │             │
       │              └──────────────┘             │
       │                                           │
       │         ┌──────────────┐                  │
       └──1:N──→ │    ORDER     │ ←──N:1───────────┘
                 │              │
                 │ id (UUID)    │
                 │ merchant_id  │
                 │ customer_id  │
                 │ items (JSON) │
                 │ subtotal     │
                 │ total        │
                 │ rzp_order_id │
                 │ rzp_payment_id│
                 │ payment_link │
                 │ status       │
                 │ audit_trail[]│
                 │ created_at   │
                 └──────┬───────┘
                        │
          ┌─────────────┼──────────────┐
          │             │              │
   ┌──────┴──────┐ ┌───┴──────┐ ┌─────┴────────┐
   │ CONVERSATION│ │ CAMPAIGN │ │  AUDIT_LOG   │
   │             │ │          │ │              │
   │ id          │ │ id       │ │ id           │
   │ customer_id │ │ merch_id │ │ order_id     │
   │ merchant_id │ │ cust_id  │ │ action       │
   │ messages[]  │ │ type     │ │ reasoning    │
   │ cart (JSON) │ │ offer    │ │ input        │
   │ status      │ │ rzp_link │ │ output       │
   │ created_at  │ │ status   │ │ timestamp    │
   └─────────────┘ │ sent_at  │ └──────────────┘
                   │ converted│
                   └──────────┘
```

## Docker Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| `frontend` | Node 20 + Next.js | 3000 | Chat UI, merchant dashboard |
| `backend` | Python 3.12 + FastAPI | 8000 | API, agent, webhooks |
| `postgres` | PostgreSQL 16 | 5432 | Primary database |
| `redis` | Redis 7 | 6379 | Sessions, cache, agent state |
| `nginx` | Nginx Alpine | 80 | Reverse proxy, route to frontend/backend |

## API Routes Overview

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Health check |
| POST | `/api/merchants` | Register merchant |
| GET | `/api/merchants/{id}` | Get merchant |
| CRUD | `/api/merchants/{id}/products` | Manage catalog |
| GET | `/api/merchants/{id}/catalog.json` | Schema.org export |
| POST | `/api/chat` | Send chat message |
| GET | `/api/conversations/{id}` | Get conversation |
| GET | `/api/cart/{conv_id}` | Get cart |
| POST | `/api/orders` | Create order + Razorpay |
| POST | `/api/webhooks/razorpay` | Razorpay webhook |
| GET/POST | `/api/webhooks/whatsapp` | WhatsApp webhook |
| POST | `/api/campaigns/send` | Send campaign |
| GET | `/api/orders/{id}/audit` | Audit trail |

---

## Changelog

*Architecture changes are logged here with reasoning.*

### v1 (Aug 23, 2026) — Initial Architecture
- **Decision**: FastAPI (Python) + Next.js + PostgreSQL + Redis + Docker
- **Reasoning**: Python AI ecosystem, FastAPI async, Pydantic validation, Docker for reproducibility
- **Impact**: All phases designed around this stack
