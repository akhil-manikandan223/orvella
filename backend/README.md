# Orvella Backend

FastAPI backend for Orvella. See `../ORVELLA_PROJECT_PLAN.md` for the full architecture spec.

## Running locally

The backend runs via Docker Compose (from the repo root):

```bash
cp .env.example .env   # fill in real values
docker compose up --build
```

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Health check: http://localhost:8000/health

Migrations run inside the container:

```bash
docker compose exec backend alembic upgrade head
```

Seed the first platform/super-admin (idempotent, run once — reads
`PLATFORM_ADMIN_EMAIL`/`PLATFORM_ADMIN_PASSWORD` from `.env`):

```bash
docker compose exec backend python -m scripts.seed_platform_admin
```

Log in and call the protected demo endpoint:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@yourorg.com", "password": "<PLATFORM_ADMIN_PASSWORD>"}'

curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```

## Auth stub — what this is and isn't

Phase 1 ships a **minimal, intentionally throwaway** auth stub: one seeded
platform admin, Argon2id password hashing, and a JWT that gates
`/api/v1/auth/me`. It exists only to protect the platform-admin module while
it's being built.

Not built (deferred to Phase 3 — Authentication and Access): refresh tokens,
session revocation/blacklist, roles/permissions, rate limiting on login,
password reset, MFA, audit logging of auth events.

## Phase 2 — organization taxonomy, features, tenants

Platform admins can define an `OrganizationCategory` → `OrganizationType`
taxonomy (e.g. Education → High School), maintain a `Feature` catalog, attach
default features to a type as a template, and create tenants classified by
type. Tenant creation copies the type's template features into `TenantFeature`
rows once, at creation time — `TenantFeature` (not the template) is the only
enforced source of truth for what's actually on for a tenant afterward.

`Tenant.max_users` (nullable seat cap; null = unlimited) exists as a schema
field only. There is no tenant-user model or tenant-user-creation endpoint
yet, so nothing exists to count against the cap — **live enforcement is
Phase 3 work**, once tenant-scoped users exist. Don't mistake the missing
enforcement for a bug.

Similarly, `core/hostnames.py` + `api/deps.py:get_tenant_from_host` can
resolve a `Tenant` from a request's `Host` header, but this is **not** wired
into any middleware or route yet — there's nothing to enforce it against
until Phase 3 adds tenant-scoped routes/auth.

## Development commands

Create a virtualenv and install dev dependencies:

```bash
python -m venv .venv
.venv/Scripts/activate   # or `source .venv/bin/activate` on macOS/Linux
pip install -r requirements/dev.txt
```

Lint and format:

```bash
ruff check .
ruff format .
```

Run tests (requires a reachable Postgres — `DATABASE_URL` env var, or run via
Docker Compose and `docker compose exec backend pytest`):

```bash
pytest
```

Create a new migration after changing models:

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Project structure

```
app/
├── api/        # HTTP boundary only — no SQL, no JWT/hashing logic here
├── core/       # cross-cutting infra: settings, security, logging, exceptions
├── db/         # engine/session lifecycle, shared declarative Base
├── domains/    # vertical feature slices (models/schemas/repository/service)
├── middleware/ # ASGI-level concerns (request correlation IDs)
└── services/   # reserved for future cross-domain infra
```
