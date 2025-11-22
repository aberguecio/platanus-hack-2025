# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Full-stack application with Next.js 14 (TypeScript frontend), FastAPI (Python backend), and SQLite database. The project uses Docker Compose with two deployment configurations: local development and production with Traefik reverse proxy.

## Architecture

### Backend (FastAPI)
- **Entry point**: `backend/main.py` - FastAPI application with CORS enabled
- **Database layer**: SQLAlchemy ORM with SQLite
  - `backend/database.py` - DB connection and session management
  - `backend/models.py` - SQLAlchemy models (currently only `Item` model)
  - `backend/schemas.py` - Pydantic schemas for request/response validation
- **Migrations**: Alembic manages database schema changes
  - `backend/alembic/env.py` - Alembic configuration imports Base and models
  - Migration files in `backend/alembic/versions/`
  - Database URL configured via `DATABASE_URL` environment variable
- **Startup**: `backend/entrypoint.sh` runs migrations then starts uvicorn with hot reload

### Frontend (Next.js)
- **Framework**: Next.js 14 with TypeScript and App Router
- **Structure**: Uses Next.js 14 app directory structure
  - `frontend/app/layout.tsx` - Root layout
  - `frontend/app/page.tsx` - Main page with API integration
- **API Connection**:
  - Local dev: `NEXT_PUBLIC_API_URL=http://localhost:8000`
  - Production: Backend accessed via `/api` path through Traefik

### Deployment Configurations

**Local Development** (`docker-compose.local.yml`):
- Direct port exposure (3000 for frontend, 8000 for backend)
- Hot reload enabled for both services
- No reverse proxy

**Production** (`docker-compose.yml`):
- Uses external `webapp` network shared with Traefik
- Traefik labels configure routing:
  - Frontend: root domain (`ph.berguecio.cl`)
  - Backend: `/api` prefix with stripprefix middleware
- SSL certificates handled by Traefik

## Development Commands

### Starting the Application

**Local development:**
```bash
docker compose -f docker-compose.local.yml up -d
docker compose -f docker-compose.local.yml logs -f
```

Access at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

**Production (requires Traefik):**
```bash
docker network create webapp  # First time only
docker compose up -d
docker compose logs -f
```

### Database Migrations

**Creating a new migration after modifying models:**
```bash
docker compose exec backend alembic revision --autogenerate -m "description"
```

**Applying migrations:**
```bash
docker compose exec backend alembic upgrade head
# or
docker compose exec backend bash migrate.sh
```

**Viewing migration history:**
```bash
docker compose exec backend alembic history
docker compose exec backend alembic current
```

**Reverting a migration:**
```bash
docker compose exec backend alembic downgrade -1
```

### Rebuilding and Restarting

```bash
# Rebuild images after Dockerfile or dependency changes
docker compose up -d --build

# Restart a single service
docker compose restart backend

# Stop everything
docker compose down

# Nuclear option - removes volumes (deletes database)
docker compose down -v
```

### Database Access

```bash
# Access SQLite from backend container
docker compose exec backend sqlite3 app.db

# From host (if SQLite installed)
sqlite3 backend/app.db
```

## Key Patterns

### Adding New Database Models

1. Add model class to `backend/models.py` inheriting from `Base`
2. Import the new model in `backend/alembic/env.py` (Alembic needs this for autogeneration)
3. Create Pydantic schemas in `backend/schemas.py` (Base, Create, Update, and response schemas)
4. Create migration: `docker compose exec backend alembic revision --autogenerate -m "add model_name"`
5. Apply migration: `docker compose exec backend alembic upgrade head`
6. Add API endpoints in `backend/main.py`

### API Endpoint Pattern

All endpoints follow FastAPI dependency injection pattern:
```python
@app.get("/endpoint/", response_model=schemas.ResponseSchema)
def endpoint_name(db: Session = Depends(get_db)):
    # Use db session here
    return result
```

### CORS Configuration

CORS is fully open (`allow_origins=["*"]`) in `backend/main.py:11-17`. Restrict this for production by configuring specific origins.

## Current API Endpoints

- `GET /` - Welcome message
- `GET /health` - Health check
- `GET /items/` - List items (supports `skip` and `limit` query params)
- `GET /items/{item_id}` - Get single item
- `POST /items/` - Create item (body: `{title, description?, completed?}`)
- `PUT /items/{item_id}` - Update item (partial updates supported)
- `DELETE /items/{item_id}` - Delete item

## Important Notes

- Backend uses `--reload` flag so Python changes auto-reload in development
- Frontend uses Next.js dev mode with hot module replacement
- SQLite database persists in mounted volume at `backend/app.db`
- Alembic must be able to import all models - ensure new models are imported in `backend/alembic/env.py`
- When adding environment variables, update both docker-compose files
- Traefik configuration assumes SSL certificates are managed externally
