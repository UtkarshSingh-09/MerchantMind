# 📡 MerchantMind — API Reference

> Quick reference for all external APIs. Saves time looking up docs.

---

## Razorpay (Test Mode)

### Credentials
```
Key ID:     rzp_test_XXXXXXXXXX   (from Dashboard → API Keys)
Key Secret: XXXXXXXXXXXXXXXXXXXXXX
Base URL:   https://api.razorpay.com/v1
Auth:       Basic Auth (key_id:key_secret)
```

### Python SDK
```bash
pip install razorpay
```
```python
import razorpay
client = razorpay.Client(auth=("rzp_test_XXX", "secret_XXX"))
```

### Key Endpoints

| Action | SDK Method | Docs |
|--------|-----------|------|
| Create Order | `client.order.create(data)` | [docs](https://razorpay.com/docs/api/orders/) |
| Create Payment Link | `client.payment_link.create(data)` | [docs](https://razorpay.com/docs/api/payment-links/) |
| Fetch Payment | `client.payment.fetch(payment_id)` | [docs](https://razorpay.com/docs/api/payments/) |
| Verify Signature | `client.utility.verify_payment_signature(params)` | [docs](https://razorpay.com/docs/payments/server-integration/python/payment-gateway/build-integration/) |

### Test Cards
| Card | Number | CVV | Expiry |
|------|--------|-----|--------|
| Success | 4111 1111 1111 1111 | Any | Any future |
| Failure | Use dashboard "Fail" button | — | — |

### Test UPI
| Handle | Result |
|--------|--------|
| `success@razorpay` | Payment succeeds |
| `failure@razorpay` | Payment fails |

### Webhooks
- URL: `POST /api/webhooks/razorpay`
- Events: `payment.captured`, `payment.failed`, `order.paid`
- Signature verification: HMAC SHA256 with webhook secret

---

## Groq API (Paid)

### Credentials
```
API Key:    gsk_XXXXXXXXXX   (from console.groq.com)
Base URL:   https://api.groq.com/openai/v1
```

### Python SDK
```bash
pip install groq
```
```python
from groq import Groq
client = Groq(api_key="gsk_XXX")

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "..."}],
    temperature=0.7,
    max_tokens=1024,
)
```

### Models
| Model | Use Case | Speed |
|-------|----------|-------|
| `llama-3.3-70b-versatile` | Primary — recommendations, reasoning | ~100ms |
| `llama-3.1-8b-instant` | Fallback — classification, simple tasks | ~50ms |

---

## WhatsApp Business Cloud API (Meta)

### Setup
1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Create App → Add WhatsApp product
3. Get: Phone Number ID, WABA ID, Access Token

### Key Endpoints
```
Base URL: https://graph.facebook.com/v21.0
```

| Action | Method | Path |
|--------|--------|------|
| Send Text | POST | `/{phone_number_id}/messages` |
| Send Interactive | POST | `/{phone_number_id}/messages` (type: interactive) |
| Webhook Verify | GET | `/api/webhooks/whatsapp` (challenge) |
| Receive Message | POST | `/api/webhooks/whatsapp` |

### Send Text Message
```python
import httpx

async def send_whatsapp(to: str, message: str):
    url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload, headers=headers)
```

### Webhook Payload (Incoming Message)
```json
{
  "entry": [{
    "changes": [{
      "value": {
        "messages": [{
          "from": "919XXXXXXXXX",
          "type": "text",
          "text": {"body": "I want a chocolate cake"}
        }]
      }
    }]
  }]
}
```

---

## Docker Quick Reference

```bash
# Start all services
docker-compose up --build

# Stop all
docker-compose down

# View logs
docker-compose logs -f backend

# Run migrations
docker-compose exec backend alembic upgrade head

# Seed database
docker-compose exec backend python scripts/seed.py
```
