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

*Not started.*

---

## Phase 3 Problems

*Not started.*

---

## Phase 4 Problems

*Not started.*

---

## Phase 5 Problems

*Not started.*

---

## Phase 6 Problems

*Not started.*

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total problems encountered | 0 |
| Total problems resolved | 0 |
| Total time lost to problems | 0 hrs |
| Most problematic phase | — |
| Most common root cause | — |
