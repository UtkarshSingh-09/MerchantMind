# MerchantMind 🧠

> AI-Powered Growth Agent for Razorpay Merchants

**Track 01: AI Growth & Agentic Commerce** | Razorpay AI Buildathon 2026

---

## 🎯 What is MerchantMind?

MerchantMind is an AI agent that helps Razorpay merchants grow revenue through:

1. **🛒 Conversational Checkout** — Customers chat in natural language, browse products, and pay via Razorpay
2. **📈 Intelligent Upselling** — AI suggests relevant add-ons that increase average order value
3. **📱 WhatsApp Commerce** — Full checkout flow on WhatsApp (550M+ Indian users)
4. **🎯 Campaign Orchestrator** — Re-engage dormant customers with personalized Razorpay Payment Links
5. **🤖 AI-Readable Catalog** — Schema.org/JSON-LD makes merchants discoverable by AI buyers

## 🏗️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Next.js 14 (React) |
| Backend | FastAPI (Python 3.12) |
| LLM | Groq API (Llama 3.3 70B) |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| Payments | Razorpay Test-mode APIs |
| Messaging | WhatsApp Business Cloud API |
| Infra | Docker + Nginx + GitHub Actions CI/CD |

## 🚀 Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/merchantmind.git
cd merchantmind

# 2. Set up environment
cp .env.example .env
# Edit .env with your API keys (Groq, Razorpay, WhatsApp)

# 3. Start everything
docker-compose up --build

# 4. Seed the database
docker-compose exec backend python scripts/seed.py

# 5. Open
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
# Health:   http://localhost:8000/health
```

## 📁 Project Structure

```
merchantmind/
├── backend/           # FastAPI (Python 3.12)
│   ├── app/
│   │   ├── main.py    # App entry point
│   │   ├── config.py  # Pydantic settings
│   │   ├── models/    # SQLAlchemy models
│   │   ├── schemas/   # Pydantic schemas
│   │   ├── routes/    # API endpoints
│   │   ├── services/  # Business logic
│   │   └── agents/    # Groq-powered AI agents
│   └── tests/
├── frontend/          # Next.js (React)
├── docs/              # Architecture & project docs
├── docker-compose.yml # All services
└── nginx/             # Reverse proxy config
```

## 🎬 Demo Video

[Watch the 5-minute demo →](#) *(coming soon)*

## 📄 License

MIT
