# MerchantMind 🧠

> **Autonomous AI Shopping & Growth Agent for Razorpay Merchants**  
> *Track 01: AI Growth & Agentic Commerce | Razorpay AI Buildathon 2026*

---

## 💡 What is MerchantMind?

**MerchantMind** transforms traditional e-commerce catalogs into **intelligent, agentic commerce engines**. Powered by Groq LLMs (`openai/gpt-oss-120b` and `openai/gpt-oss-20b`), Razorpay payment infrastructure, and the Telegram Bot API, it provides customers with a human-like shopping experience while driving revenue growth and higher Average Order Value (AOV) for merchants.

```
                    ┌──────────────────────────────────┐
                    │       CUSTOMER TOUCHPOINTS       │
                    │   • Web Chat UI (Next.js 16)     │
                    │   • Telegram Bot (Bot API)       │
                    └─────────────────┬────────────────┘
                                      │
                                      ▼
                    ┌──────────────────────────────────┐
                    │        CHECKOUT AGENT ENGINE     │
                    │  1. Intent & Budget Extraction   │
                    │  2. Catalog Semantic Search      │
                    │  3. Context-Aware Upsell Engine  │
                    │  4. Hard Budget Guardrails       │
                    └─────────────────┬────────────────┘
                                      │
                                      ▼
                    ┌──────────────────────────────────┐
                    │     RAZORPAY PAYMENT LIFECYCLE   │
                    │  • Order Creation API            │
                    │  • Instant Payment Links (Inline)│
                    │  • HMAC Webhook Verification     │
                    │  • Immutable Audit Trail         │
                    └──────────────────────────────────┘
```

---

## 🌟 Core Pillars & Key Features

### 1. 🛒 Conversational Checkout
- **Natural Language Shopping**: Understands intent, flavors, occasions, quantities, and price constraints (e.g. *"I need a dark chocolate birthday cake under ₹800"*).
- **Reasoning for Recommendations**: Explains *why* every product is recommended based on dietary preferences, servings, and budget fit.
- **Multi-Turn Cart Management**: Automatically handles adding, incrementing, decrementing, and clearing cart items via function calling.

### 2. 📈 Context-Aware Upselling & Cross-Selling
- **Pairing Rules Engine**: Proactively detects occasions (e.g., Cake ➔ Birthday Candles Set + Balloon Combo; Pastries ➔ Freshly brewed Artisan Coffee).
- **Budget-Bounded Recommendations**: Computes `remaining_budget = stated_budget - cart_total` and guarantees recommendations never exceed customer limits.

### 3. 💳 Full Razorpay Payment Integration
- **Automated Order & Payment Link Generation**: Creates Razorpay orders and generates secure short URLs for instant payment.
- **Cryptographic Webhook Verification**: Validates all incoming payment events (`payment.captured`, `payment.failed`, `payment_link.paid`) using HMAC-SHA256 signatures.
- **Real-Time Payment Polling**: Chat UI automatically detects captured payments and updates order status to `PAID`.

### 4. 📱 Telegram Conversational Commerce
- **Telegram Bot API**: Customers can explore 214 stores, query dishes, add items via inline keyboard buttons, and receive instant Razorpay payment links directly in Telegram.
- **24-Hour Session Persistence**: Maintains cart state and agent memory across Telegram chats.

### 5. 🛡️ Hard Guardrails & Full Audit Trail
- **Budget Enforcement Guardrail**: Hard validation blocks payment link creation if `cart_total > stated_budget`, raising a `BUDGET_VIOLATION` event.
- **Immutable Decision Logging**: Every agent tool call, reasoning string, Razorpay API transaction, and WhatsApp message is logged to PostgreSQL and queryable via `GET /api/orders/{id}/audit`.
- **Fault-Tolerant Resilience**: Groq client automatically fails over from primary model to fallback with exponential backoff on transient network spikes.

### 6. 🌐 AI-Readable Catalog (Schema.org / JSON-LD)
- `GET /api/merchants/{id}/catalog.json` exports merchant catalogs in standards-compliant Schema.org `ItemList` + `Product` + `Offer` format for discovery by autonomous AI agents and search engines.

---

## 🏗️ Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | Next.js 16 (App Router), React 19, Tailwind CSS v4, Lucide Icons, TypeScript |
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2.0 (Async), Pydantic v2 |
| **AI / LLM** | Groq API (`openai/gpt-oss-120b`, fallback: `openai/gpt-oss-20b`), Function Calling |
| **Payments** | Razorpay SDK (Orders, Payment Links, Webhooks HMAC-SHA256) |
| **Messaging** | Telegram Bot API (Interactive Keyboards & Razorpay Pay Buttons) |
| **Data & Cache** | PostgreSQL 16 (Relational & JSONB), Redis 7 (Sessions) |
| **DevOps & Infra** | Docker, Docker Compose, NGINX Reverse Proxy, GitHub Actions CI/CD |

---

## 🚀 Quick Start (Dockerized)

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/merchantmind.git
cd merchantmind
```

### 2. Configure Environment Variables
```bash
cp .env.example .env
```
Fill in your API credentials in `.env`:
- `GROQ_API_KEY` (from [Groq Console](https://console.groq.com/))
- `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET` (from [Razorpay Dashboard](https://dashboard.razorpay.com/))
- `TELEGRAM_BOT_TOKEN` (from [@BotFather](https://t.me/botfather))

### 3. Launch Services via Docker Compose
```bash
docker-compose up --build -d
```

### 4. Seed Demo Catalog Data
```bash
docker-compose exec backend python scripts/seed.py
```

### 5. Access the Application
- **Frontend Chat Store**: [http://localhost:3000/chat](http://localhost:3000/chat)
- **Interactive Landing Page**: [http://localhost:3000](http://localhost:3000)
- **FastAPI Interactive Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Backend Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 📡 Key API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat/` | Send message to AI Checkout Agent (search, upsell, cart) |
| `POST` | `/api/orders/` | Create order from cart & generate Razorpay Payment Link |
| `GET` | `/api/orders/{id}/status` | Poll payment confirmation status |
| `GET` | `/api/orders/{id}/audit` | View full chronological audit trail and AI reasoning |
| `POST` | `/api/webhooks/razorpay` | Cryptographic HMAC webhook handler for Razorpay |
| `POST` | `/api/webhooks/telegram` | Telegram Bot update handler with inline buttons & Razorpay links |
| `GET/POST` | `/api/webhooks/whatsapp` | Meta WhatsApp verification challenge & incoming message handler |
| `POST` | `/api/campaigns/dispatch` | Identify dormant customers & dispatch personalized AI offers |
| `GET` | `/api/merchants/{id}/catalog.json` | Schema.org/JSON-LD AI-readable catalog export |

---

## 🧪 Running Automated Tests

```bash
# Run backend test suite
cd backend
pytest tests/ -v
```

Tests include:
- `test_orders.py`: Full order lifecycle & webhook payment capture
- `test_upsell.py`: Occasion pairing & budget-bounded recommendations
- `test_audit.py`: Decision audit logs & hard budget guardrail enforcement
- `test_multi_tenant.py`: Strict data isolation across multiple merchants
- `test_whatsapp.py`: Meta GET challenge verification & incoming message flow

---

## 🎬 5-Minute Demo Video

*(Link will be updated upon recording submission)*

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
