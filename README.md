# orvella

A multi-tenant platform for managing organizations, people, roles, and operations.

See [`ORVELLA_PROJECT_PLAN.md`](ORVELLA_PROJECT_PLAN.md) for the full product and technical
architecture spec.

## Running locally

### Frontend

```bash
cd frontend
npm install
npm start   # http://localhost:6200
```

### Backend

The backend (FastAPI + PostgreSQL) runs via Docker Compose; the frontend keeps running via
`ng serve` above, not in Docker.

```bash
cp .env.example .env   # fill in real values
docker compose up --build
docker compose exec backend alembic upgrade head
docker compose exec backend python -m scripts.seed_platform_admin
```

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs

See [`backend/README.md`](backend/README.md) for day-to-day backend commands (migrations, tests,
lint).
