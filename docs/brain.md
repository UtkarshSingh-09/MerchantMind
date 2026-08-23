# 🧠 MerchantMind — Brain

> Living dashboard. Updated after every work session.

---

## Status Dashboard

| Phase | Name | Status | Progress | Deadline | Blockers |
|-------|------|--------|----------|----------|----------|
| 1 | Foundation & Catalog | 🟡 Starting | 0% | Aug 25 | None |
| 2 | Conversational Checkout | ⏳ Waiting | 0% | Aug 28 | Needs Phase 1 catalog |
| 3 | Razorpay Payment Flow | ⏳ Waiting | 0% | Aug 30 | Needs Phase 2 cart |
| 4 | Upsell + WhatsApp | ⏳ Waiting | 0% | Sep 1 | Needs Phase 3 payment + WhatsApp API approval |
| 5 | Guardrails + Audit | ⏳ Waiting | 0% | Sep 3 | Needs Phase 3-4 |
| 6 | Polish + Demo | ⏳ Waiting | 0% | Sep 5 | Needs all phases |

## Cross-Phase Dependencies

```
Phase 1 (Catalog) ──→ Phase 2 (Checkout) ──→ Phase 3 (Payment)
                                                    │
                                          Phase 4 (Upsell + WhatsApp)
                                                    │
                                          Phase 5 (Guardrails + Audit)
                                                    │
                                          Phase 6 (Polish + Demo)
```

### Specific Dependencies
- Phase 2 needs Phase 1's catalog API + database models
- Phase 3 needs Phase 2's cart management system
- Phase 4 (WhatsApp) can partially start early — register Meta API on Day 1
- Phase 4 (Upsell) needs Phase 2's cart context
- Phase 5 needs Phase 3-4 to have working payment + messaging flows
- Phase 6 needs all phases functional

### Deferred Work
- Phase 1: 20% of catalog work (Schema.org export) can be deferred until Phase 5

## Active Decisions

| Date | Decision | Reasoning |
|------|----------|-----------|
| Aug 23 | Use Groq paid tier | No rate limit concerns, production-realistic multi-user |
| Aug 23 | FastAPI over Express | Python AI ecosystem is stronger, Pydantic built-in |
| Aug 23 | PostgreSQL over SQLite | Multi-user support, production-grade |
| Aug 23 | Track 01: Agentic Commerce | Best PS match, Razorpay's #1 strategic priority |

## Notes for Next Session
- Register WhatsApp Business API on Meta for Developers (Day 1 priority!)
- Create Razorpay test account and get API keys
- Get Groq API key from console.groq.com
- Set up public GitHub repo

## External Accounts Needed
- [ ] Razorpay test account → `rzp_test_` keys
- [ ] Groq API → `gsk_` key
- [ ] Meta for Developers → WhatsApp Business API
- [ ] GitHub → public repo
