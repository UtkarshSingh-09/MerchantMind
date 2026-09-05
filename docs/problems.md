# 🔴 MerchantMind — Problems Log

> Every problem faced and how we solved it. Gold for the demo video.

---

## How to Log

```markdown
### Problem: [Short description]
- **Phase**: Phase X
- **Date**: Aug XX
- **Impact**: [What was blocked?]
- **Root Cause**: [Why did it happen?]
- **Solution**: [How we fixed it]
- **Time Lost**: [How long to resolve]
- **Lesson**: [What we'd do differently]
```

---

## Phase 1 Problems

### Problem: Pydantic-settings can't parse comma-separated list from env
- **Phase**: Phase 1
- **Date**: Aug 23
- **Impact**: Backend wouldn't start — crashed on config load
- **Root Cause**: `pydantic-settings` tries to JSON-parse `list[str]` fields from env vars before validators run. `CORS_ORIGINS=http://localhost:3000,http://localhost:80` isn't valid JSON.
- **Solution**: Changed to `cors_origins_str: str` with a `@property` that splits the comma-separated string.
- **Time Lost**: 15 min
- **Lesson**: Always use `str` type for env vars that contain lists, then parse them yourself.

### Problem: Docker port conflicts (PostgreSQL 5432, Redis 6379)
- **Phase**: Phase 1
- **Date**: Aug 23
- **Impact**: Docker Compose failed to start — ports already allocated by local services
- **Root Cause**: Local PostgreSQL and Redis were running on the default ports
- **Solution**: Mapped to different host ports: PostgreSQL → 5433, Redis → 6380. Internal Docker networking still uses standard ports.
- **Time Lost**: 5 min
- **Lesson**: Always use non-standard host ports in docker-compose for dev environments.

---

## Phase 2 Problems

### Problem: Python 3.12 distutils deprecation & missing httpx dependency
- **Phase**: Phase 2
- **Date**: Aug 27
- **Impact**: Backend container build and local server failed to boot when initializing LLM agents and Groq SDK dependencies.
- **Root Cause**: Python 3.12 removed the standard `distutils` library. Legacy build hooks in transitive packages crashed without `setuptools`, and `httpx` async client was missing from `requirements.txt`.
- **Solution**: Added explicit `setuptools>=68.0.0` and `httpx>=0.27.0` to backend dependencies in `pyproject.toml` and `requirements.txt`.
- **Time Lost**: 25 min
- **Lesson**: Python 3.12 container base images require explicit declaration of core packaging utilities (`setuptools`) and HTTP transports.

### Problem: ReAct catalog search N+1 query cascade (10.6s latency spike)
- **Phase**: Phase 2
- **Date**: Aug 28
- **Impact**: Conversational agent turns took over 10.5 seconds, causing timeouts and making real-time chat and voice interaction completely sluggish.
- **Root Cause**: `get_all_merchants_summary` executed 192 individual SQL queries in an unbatched loop across merchants, categories, and inventory items on every conversational turn to assemble context.
- **Solution**: Consolidated the N+1 queries into a single aggregated PostgreSQL query (`json_agg` + `GROUP BY`) backed by an in-memory 5-minute TTL cache, dropping turn response time from 10.6s down to 611ms.
- **Time Lost**: 45 min
- **Lesson**: Never let agent system prompts or tool handlers perform unbatched relational database traversals on live user messages.

### Problem: Keyword tokenization failure on complex conversational retail queries
- **Phase**: Phase 2
- **Date**: Aug 28
- **Impact**: Inquiries like "suggest something sweet under 500 for birthday" failed catalog matching because full sentence strings were passed to SQL `ILIKE` clauses.
- **Root Cause**: Catalog search lacked multi-word tokenization, stop-word stripping, and category synonym expansion for Indian retail terminology (e.g., "mithai", "eggless", "pastry").
- **Solution**: Built a tokenization pipeline with regex token extraction, conversational stop-word removal, and fallback multi-word substring scoring.
- **Time Lost**: 30 min
- **Lesson**: Conversational search queries must undergo deterministic token cleansing and fallback scoring before hitting SQL catalog filters.

---

## Phase 3 Problems

### Problem: Razorpay integer paise vs. decimal rupee precision drift
- **Phase**: Phase 3
- **Date**: Aug 29
- **Impact**: Razorpay rejected order creation with `BAD_REQUEST_ERROR: Amount cannot have decimal places`, or carts were priced at 1/100th of actual cost.
- **Root Cause**: Frontend and agent passed decimal rupee floats (e.g., `450.50`), whereas Razorpay API strictly mandates integer atomic paise (`45050`). IEEE 754 float rounding also caused precision drift (`45049.99999999999`).
- **Solution**: Enforced `int(round(amount_in_rupees * 100))` across all Pydantic schemas, database models, and payment SDK wrappers, storing all financial amounts as atomic integer paise.
- **Time Lost**: 20 min
- **Lesson**: Always store and manipulate money in atomic integer units (paise/cents) internally; only format decimals at the UI rendering layer.

### Problem: Razorpay webhook HMAC-SHA256 signature verification failure
- **Phase**: Phase 3
- **Date**: Aug 30
- **Impact**: Razorpay webhook callbacks (`payment.captured`, `payment.failed`) were rejected with HTTP 400 Invalid Signature.
- **Root Cause**: FastAPI's `Request.json()` parsed and reformatted JSON before calculating HMAC signatures. Minor whitespace, key ordering, and character encoding differences broke crypto hashes.
- **Solution**: Modified webhook handler to extract `await request.body()` (raw unparsed bytes) directly before any JSON parsing, passing raw bytes into `hmac.new()` for cryptographic verification.
- **Time Lost**: 35 min
- **Lesson**: Payment gateway webhooks must ALWAYS verify cryptographic signatures against the raw binary request payload before JSON deserialization.

---

## Phase 4 Problems

### Problem: Unconstrained upsell engine violating customer hard budget
- **Phase**: Phase 4
- **Date**: Aug 31
- **Impact**: ReAct upsell agent recommended high-margin cross-sell items (e.g., designer cake topper + luxury gift box) that breached the customer's explicitly declared budget limit (e.g., "under ₹800").
- **Root Cause**: Recommendation heuristic scored products solely by affinity and merchant margin without applying a hard algebraic boundary against the active conversation budget.
- **Solution**: Implemented a pre-recommendation hard budget guardrail (`BudgetValidator`) that filters candidate upsells: `(current_cart_total + upsell_price) <= customer_budget`. If no items qualify, upselling is gracefully suppressed.
- **Time Lost**: 30 min
- **Lesson**: Autonomous sales agents must enforce deterministic mathematical guardrails surrounding probabilistic LLM reasoning.

### Problem: Meta WhatsApp Cloud API webhook handshake rejection & retry flood
- **Phase**: Phase 4
- **Date**: Sep 1
- **Impact**: Meta WhatsApp Cloud API failed initial endpoint verification (`hub.challenge`), and transient server lag caused Meta to storm the webhook with duplicate messages.
- **Root Cause**: Meta expects a raw plain-text integer response for `hub.challenge` (not JSON), and missing idempotency tracking on incoming message IDs led to duplicate agent responses.
- **Solution**: Returned `PlainTextResponse(hub_challenge)` for Meta GET verification, and added Redis-backed idempotency keys (`SETNX whatsapp:msg:{id} EX 86400`) to deduplicate incoming messages.
- **Time Lost**: 40 min
- **Lesson**: WhatsApp Meta Cloud API requires raw plain text handshake responses and strict Redis deduplication to avoid webhook storms.

---

## Phase 5 Problems

### Problem: Inventory race condition during concurrent multi-customer checkout
- **Phase**: Phase 5
- **Date**: Sep 2
- **Impact**: Stress tests with concurrent shoppers purchasing the final unit of stock caused overselling (inventory dropped below zero).
- **Root Cause**: Standard SQLAlchemy `SELECT` followed by `UPDATE` allowed interleaving read-modify-write transactions between concurrent requests.
- **Solution**: Added pessimistic row-level locking (`SELECT ... FOR UPDATE`) inside an atomic 3-phase checkout saga with automated compensation rollback.
- **Time Lost**: 45 min
- **Lesson**: Inventory reservation in e-commerce checkout sagas must enforce atomic row locks or transactional compare-and-swap (CAS).

### Problem: Frontend runtime ReferenceError hoisting `handleSendMessage` in chat page
- **Phase**: Phase 5
- **Date**: Sep 2
- **Impact**: Chat page crashed on initial load in production builds with `ReferenceError: Cannot access 'handleSendMessage' before initialization`.
- **Root Cause**: `handleSendMessage` was declared as an arrow function after `useEffect` hooks and VoiceOrb event listeners that referenced it during the first render pass.
- **Solution**: Hoisted `handleSendMessage` using `useCallback` defined above all dependent lifecycle hooks and synchronized via an execution ref.
- **Time Lost**: 20 min
- **Lesson**: Always declare core dispatch functions before dependent effect hooks in React functional components.

---

## Phase 6 Problems

### Problem: Premature silence cutoff cutting off natural conversational voice pauses
- **Phase**: Phase 6
- **Date**: Sep 3
- **Impact**: Users speaking with natural hesitation (e.g., "I need a birthday cake... [1.2s pause] ...with eggless frosting") were cut off mid-sentence, submitting incomplete queries.
- **Root Cause**: Default browser Web Speech API / STT activity detector had an aggressive 800ms silence timeout designed for short voice commands, not conversational commerce.
- **Solution**: Implemented an adaptive silence buffer (2.2s to 3.0s based on phrase completeness) and speech pause heuristics before dispatching to the ReAct agent.
- **Time Lost**: 35 min
- **Lesson**: Conversational voice agents require longer, context-aware silence timeouts (2.0s+) compared to command-and-control assistants.

### Problem: Browser autoplay policy blocking Deepgram Flux Meena TTS audio playback
- **Phase**: Phase 6
- **Date**: Sep 3
- **Impact**: Voice response audio from Deepgram Flux Meena failed silently on first user interaction with `DOMException: play() failed because the user didn't interact with the document first`.
- **Root Cause**: Modern browser autoplay security blocks programmatic `AudioContext` and `.play()` calls if an unlocked user gesture has not primed the audio context.
- **Solution**: Built an invisible AudioContext primer that unlocks and resumes `AudioContext` on the very first mic click/tap, ensuring Deepgram audio buffers stream without autoplay rejection.
- **Time Lost**: 30 min
- **Lesson**: Always initialize and resume Web Audio `AudioContext` within direct user gesture handlers (tap/click) before attempting async audio playback.

### Problem: Cloud PostgreSQL connection crash due to missing `+asyncpg` dialect prefix
- **Phase**: Phase 6
- **Date**: Sep 5
- **Impact**: Cloud backend deployment on Railway/Render crashed on boot with `NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:postgresql`.
- **Root Cause**: Cloud hosting providers inject `DATABASE_URL` starting with `postgres://` or `postgresql://`, but SQLAlchemy async engine requires the explicit async driver dialect `postgresql+asyncpg://`.
- **Solution**: Added auto-conversion in `backend/app/config.py`:
  `url = url.replace("postgres://", "postgresql+asyncpg://").replace("postgresql://", "postgresql+asyncpg://")`.
- **Time Lost**: 15 min
- **Lesson**: Never assume cloud platform `DATABASE_URL` contains async driver prefixes; sanitize dialect strings in application settings.

### Problem: Sticky localStorage state triggering tracking redirect loop on `/chat` mount
- **Phase**: Phase 6
- **Date**: Sep 5
- **Impact**: After completing an order, navigating to `/chat` immediately forced an automatic redirect back to `/orders/{id}/tracking`, locking the user out of placing a new order or starting a new conversation.
- **Root Cause**: The chat component read `merchantmind_active_order_id` from `localStorage` on mount and unconditionally triggered `router.push('/orders/.../tracking')` without verifying whether that order was already paid or completed.
- **Solution**: Separated active tracking state (`merchantmind_last_order_id`), made tracking redirects conditional on incomplete pending payment, and added `?new=true` query param support to wipe stale order sessions and reset cart state.
- **Time Lost**: 40 min
- **Lesson**: Separate persistent order history IDs from active session lock IDs; never unconditionally redirect on mount based on historical `localStorage` keys.

### Problem: Three.js 3D canvas event stealing and viewport stacking overlap
- **Phase**: Phase 6
- **Date**: Aug 27 / Sep 1
- **Impact**: Three.js 3D radar canvas intercepted pointer events and rendered visually over text hero elements, causing unclickable buttons and visual jitter.
- **Root Cause**: WebGL canvas was positioned with default elevation and absorbed mouse raycaster events across the viewport.
- **Solution**: Lowered WebGL canvas elevation, applied `pointer-events: none` to ambient particle canvases, and layered a radial obsidian gradient backdrop (`z-index: 1`) under UI controls (`z-index: 20`).
- **Time Lost**: 25 min
- **Lesson**: 3D background canvases must explicitly set `pointer-events: none` unless interactive raycasting is specifically bounded to a dedicated viewport.

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total problems encountered | 16 |
| Total problems resolved | 16 (100%) |
| Total time lost to problems | ~7.6 hrs (460 min) |
| Most problematic phase | Phase 6 (Voice Intelligence, Deployment & Real-Time Hardening) |
| Most common root cause | Protocol & Asynchronous State Disconnects (raw bytes vs JSON, asyncpg dialects, audio autoplay, localStorage session locks, N+1 SQL cascades) |
