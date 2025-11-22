# Memories Bot API

Telegram bot for storing and organizing memories (photos and text) using AI agent-based architecture.

## Stack

- **Backend**: FastAPI with Python
- **Database**: PostgreSQL with pgvector extension
- **Agent**: Anthropic Claude (via tool calling)
- **Storage**: AWS S3 (optional, has placeholder mode)
- **Containerization**: Docker & Docker Compose

## Architecture

```
Telegram Bot → /webhook (raw JSON) → AI Agent → Decides Action → Executes → Responds to user
```

The API receives raw Telegram updates, processes them with an AI agent (Claude), which decides what action to take, executes it, and responds back to the user.

### Key Features

- **Agentic**: No traditional REST CRUD endpoints - everything goes through the AI agent
- **Conversational**: Users interact naturally, agent understands intent
- **Event-based**: Memories are organized into events
- **Multi-user**: Events can have multiple participants
- **Image support**: Stores photos in S3 (or mock storage)
- **Vector-ready**: Database supports embeddings (not yet implemented)

## Database Schema

### Users
- `telegram_id` (unique)
- `username`, `first_name`, `last_name`
- Many-to-many relationship with Events

### Events
- `name`, `description`, `event_date`
- Can have multiple users and memories

### Memories
- `event_id`, `user_id`
- `text`, `image_url`
- `embedding` (vector, for future semantic search)

**Acceso:**

- **Frontend**: <http://localhost:3000>
- **Backend API**: <http://localhost:8000>
- **API Docs (Swagger)**: <http://localhost:8000/docs>
- **API Redoc**: <http://localhost:8000/redoc>
## Setup

### 1. Environment Variables

Copy `.env.example` to `.env` and fill in:

```bash
cp .env.example .env
```

**Acceso (requiere Traefik configurado):**

- **Frontend**: <https://ph.berguecio.cl>
- **Backend API**: <https://ph.berguecio.cl/api>
- **API Docs**: <https://ph.berguecio.cl/api/docs>

**Arquitectura:**

- Frontend accesible en raíz del dominio
- Backend accesible en `/api` (el middleware stripprefix quita `/api` antes de enviar al backend)
- Ambos servicios en la red `webapp` compartida con Traefik
- Certificados SSL automáticos vía Traefik
**Important:** The `.env` file includes `COMPOSE_FILE=docker-compose.local.yml` which makes Docker Compose use the local development file by default. This means you can run `docker compose up` instead of `docker compose -f docker-compose.local.yml up`.

Required:
- `ANTHROPIC_API_KEY` - Get from https://console.anthropic.com/

Optional:
- `AWS_S3_BUCKET` - Leave empty to use mock storage
- `COMPOSE_FILE` - Set to `docker-compose.local.yml` for local dev (already in .env.example)

### 2. Local Development

```bash
# Start services (uses docker-compose.local.yml via .env)
docker compose up

```

### Migration
```bash
# Create initial migration
docker compose exec backend alembic revision --autogenerate -m "initial schema"

# Apply migrations
docker compose exec backend alembic upgrade head
```

**Access:**
- API: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc
- Health check: http://localhost:8000/health
- Database: localhost:5432

### 3. Production Deployment

```bash
# Ensure webapp network exists
docker network create webapp

# Start services (with Traefik)
docker compose up -d

# Create and apply migrations
docker compose exec backend alembic revision --autogenerate -m "initial schema"
docker compose exec backend alembic upgrade head
```

**Access:**
- API: https://ph.berguecio.cl
- Webhook: https://ph.berguecio.cl/webhook

## Agent Actions

The AI agent can decide to perform these actions:

### create_event
Create a new event for storing memories.
```
User: "Create event Birthday Party on Dec 25"
```

### join_event
Add user to an existing event.
```
User: "Join event #3"
```

### add_memory
Add a memory (text and/or photo) to an event.
```
User: *sends photo* "Here's from the party! #2"
```

### list_events
Show all events the user is part of.
```
User: "What events am I in?"
```

### list_memories
Show all memories from an event.
```
User: "Show memories from event #2"
```

## API Endpoints

### POST /webhook
Main endpoint that receives Telegram updates from your bot.

**Flow:**
1. Your Telegram bot receives a message from a user
2. Bot makes POST request to this endpoint with the update
3. API processes with AI agent, executes action
4. API responds with Telegram Bot API format
5. Your bot sends the response back to the user

**Request:** Raw Telegram update JSON (from Telegram Bot API)

**Response:** Telegram Bot API method format
```json
{
  "method": "sendMessage",
  "chat_id": 123456789,
  "text": "Event 'Birthday Party' created with ID 5!",
  "parse_mode": "Markdown"
}
```

Your bot should execute this method to respond to the user.

### GET /health
Health check endpoint

### GET /docs
Interactive API documentation (Swagger UI) - **Available in development**

### GET /redoc
Alternative API documentation (ReDoc) - **Available in development**

## Telegram Bot

The Telegram bot is included in the Docker Compose setup and will start automatically.

**Setup:**
1. Create bot with [@BotFather](https://t.me/botfather) on Telegram
2. Get bot token with `/newbot`
3. Add `TELEGRAM_BOT_TOKEN` to your `.env` file
4. Bot will start automatically with `docker compose up`

**How it works:**
- Bot receives messages from users
- Forwards raw Telegram updates to API at `/webhook`
- API processes with Claude and responds
- Bot sends response back to user

## Database Migrations

### Create Migration

```bash
# Local (uses docker-compose.local.yml via .env)
docker compose exec backend alembic revision --autogenerate -m "description"

# Production (on server, uses default docker-compose.yml)
docker compose exec backend alembic revision --autogenerate -m "description"
```

### Apply Migrations

```bash
# Local
docker compose exec backend alembic upgrade head

# Production
docker compose exec backend alembic upgrade head
```

### Rollback

```bash
docker compose exec backend alembic downgrade -1
```

## Project Structure

```
backend/
├── agent/
│   ├── base.py              # Abstract LLM agent interface
│   ├── anthropic_agent.py   # Claude implementation
│   └── __init__.py
├── services/
│   ├── database.py          # Database operations
│   ├── telegram.py          # Telegram API client
│   ├── s3.py               # S3 storage (with mock)
│   └── __init__.py
├── alembic/                 # Database migrations
├── main.py                  # FastAPI app & webhook
├── models.py                # SQLAlchemy models
├── database.py              # DB connection
└── requirements.txt
```

## Future Enhancements

- [ ] Implement embeddings generation
- [ ] Semantic search using pgvector
- [ ] WhatsApp integration
- [ ] Web frontend for browsing memories
- [ ] Face recognition in photos
- [ ] Automatic event suggestions
- [ ] Memory highlights/summaries

## Development

### Add New Action

1. Add tool definition in `agent/anthropic_agent.py`
2. Add action handler in `main.py` → `execute_action()`
3. Add database method if needed in `services/database.py`

### Swap LLM Provider

1. Create new agent class extending `agent/base.py`
2. Implement `process_message()` and `generate_response()`
3. Update `main.py` to use new agent

## License

- Agregar autenticación (JWT)
- Implementar tests
- Agregar validación de datos
- Implementar paginación
- Agregar filtros y búsqueda
- Implementar cache con Redis
- Implementar CSS framework (Tailwind CSS con Shadcn UI?)
- LLM integration (Claude, OpenAI, etc.)
MIT
