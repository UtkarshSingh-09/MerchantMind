# Phase 1: Foundation & Catalog — Implementation

> **Timeline**: Aug 24-25 | **Status**: 🟡 In Progress

---

## Objectives
1. Docker Compose with all services running
2. FastAPI backend with database models
3. Merchant catalog CRUD API
4. Schema.org/JSON-LD catalog export
5. CI/CD pipeline on GitHub Actions
6. Sample bakery seed data

## Technical Decisions
- **Python 3.12** with FastAPI 0.115+
- **SQLAlchemy 2.0** async mode with asyncpg driver
- **Alembic** for migrations
- **Pydantic v2** for all request/response validation
- **PostgreSQL 16** + **Redis 7** via Docker
- **UV** for fast Python dependency management (optional)

## Implementation Order
1. Project structure + Docker Compose
2. FastAPI app skeleton + config
3. SQLAlchemy models + Alembic
4. Merchant + Product CRUD routes
5. Schema.org JSON-LD generator
6. Seed script
7. Tests
8. GitHub Actions CI
