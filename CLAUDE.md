# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

**Telegram bot de memorias conversacional** basado en agente AI que permite a usuarios almacenar y organizar recuerdos (fotos y texto) en eventos.

**Stack técnico:**
- **Backend:** FastAPI + PostgreSQL (con pgvector) + Anthropic Claude (agente)
- **Bot:** python-telegram-bot (polling mode)
- **Storage:** AWS S3 (con modo mock para desarrollo)
- **Embeddings:** Voyage AI (1024 dimensiones)
- **Vision:** Claude Haiku para descripción de imágenes

**Característica clave:** No hay endpoints REST tradicionales. Todo el sistema funciona a través de conversación natural con un agente AI que usa tool calling para ejecutar acciones.

## Arquitectura

### Backend (FastAPI)

**Entry point:** `backend/main.py`
- FastAPI con CORS habilitado
- Endpoint principal: `POST /webhook` (recibe updates de Telegram)
- Health check: `GET /health`

**Database Layer:**
- `backend/database.py` - Configuración de conexión PostgreSQL
- `backend/models.py` - Modelos SQLAlchemy con pgvector
- `backend/schemas.py` - Schemas Pydantic (TelegramUpdate, etc.)
- `backend/services/database.py` - CRUD operations (DatabaseService)

**Modelos de datos:**
1. **users** - Usuarios de Telegram (telegram_id único, username, first_name, etc.)
2. **events** - Eventos para organizar memorias (name, description, event_date)
3. **memories** - Memorias individuales (text, image_url, **embedding Vector(1024)**)
4. **user_events** - Tabla de unión many-to-many

**Migraciones:**
- Alembic maneja cambios de schema
- `backend/alembic/env.py` importa Base y models
- Migrations en `backend/alembic/versions/`
- DATABASE_URL configurado via environment

### Sistema de Agente AI

**Arquitectura:**

```
backend/agent/
├── base.py                    # Interface abstracta LLMAgent
├── anthropic_agent.py         # Implementación con Claude
├── services/
│   └── messaging_service.py   # Orquestador de mensajes
└── tools/
    ├── base_tool.py           # Clase base para tools
    ├── tool_registry.py       # Registro global singleton
    └── implementations/       # Tools concretas
        ├── create_event_tool.py
        ├── join_event_tool.py
        ├── add_memory_tool.py
        ├── list_events_tool.py
        ├── list_memories_tool.py
        └── get_faq_tool.py
```

**Flujo de procesamiento:**

1. Update de Telegram → `POST /webhook`
2. `MessagingService.process_telegram_message()`:
   - Extrae datos (texto, foto, usuario)
   - Get/create usuario en BD
   - Construye `ExecutionContext` con dependencias
3. `AnthropicAgent.process_message()`:
   - Genera system prompt dinámico con contexto del usuario
   - Obtiene schemas de tools del registry
   - Loop de tool calling (max 5 iteraciones):
     - Llama API Claude con tools disponibles
     - Claude decide qué tool(s) usar
     - Ejecuta tools via registry
     - Retorna resultados a Claude
     - Claude genera respuesta final o usa más tools
4. Retorna respuesta al usuario

**ExecutionContext:**
Dataclass que inyecta todas las dependencias a los tools:
- `db`: Session de SQLAlchemy
- `user`: Objeto User
- `s3_service`, `telegram_service`: Servicios
- `metadata`: Dict con telegram_id, has_photo, photo_file_id, etc.

**Tool Registry Pattern:**
- Tools se auto-registran al importar (en `implementations/__init__.py`)
- Registry singleton global: `get_registry()`
- Métodos:
  - `register(tool)`: Registra una tool
  - `get_schemas()`: Retorna schemas para Anthropic API
  - `execute(name, input, ctx)`: Ejecuta tool por nombre

### Servicios Core

**TelegramService** (`backend/services/telegram.py`):
- `download_file(file_id)`: Descarga archivos de Telegram
- `extract_message_data(update)`: Extrae texto, caption, photo
  - Lógica: usa caption si hay foto, sino text
  - Mensaje default: "📸 [Usuario envió una foto]" si solo hay foto
- `format_response()`, `format_error_response()`: Formateo de mensajes

**S3Service** (`backend/services/s3.py`):
- Modo mock si `AWS_S3_BUCKET` no está configurado
- `upload_image(content, filename)`: Sube a S3 o retorna URL placeholder
- `generate_presigned_url(key, expiration)`: URLs temporales (default 1 hora)

**EmbeddingService** (`backend/services/embedding.py`):
- Proveedor: **Voyage AI, modelo voyage-2 (1024 dims)**
- `embed_text(text, input_type)`: Single embedding
  - input_type: "document" o "query"
  - Retry con backoff exponencial
  - Rate limit handling
- `embed_texts_batch()`: Batch processing (max 128 textos)

**SearchService** (`backend/services/search.py`):
- Búsqueda semántica con pgvector
- `search_memories(query, event_id, user_id, top_k, threshold)`:
  - Usa cosine distance: `embedding <=> query_embedding`
  - Índice HNSW para performance
- `search_across_user_events()`: Busca en todos los eventos del usuario
- `find_similar_memories()`: Memories similares a una dada

**ImageService** (`backend/services/image.py`):
- `describe_image(image_bytes)`: Claude Vision genera descripción
  - Modelo: claude-haiku-4-5-20251001
  - Soporta JPEG, PNG, WebP, GIF
- `process_telegram_photo()`: Download → Describe → Store S3

**DatabaseService** (`backend/services/database.py`):
Métodos estáticos para operaciones CRUD:
- `get_or_create_user()`, `create_event()`, `join_event()`
- `add_memory()` - **Valida que usuario esté en el evento**
- `list_user_events()`, `list_event_memories()`, `get_event()`

### Telegram Bot

**Ubicación:** `telegram-bot/bot.py`
**Modo:** Polling (usa python-telegram-bot v21.0)

**Handlers:**
- `/start` - Mensaje de bienvenida
- Text messages → Forward a `/webhook`
- Photos → Forward a `/webhook`

**Flujo:**
1. Recibe Update de Telegram
2. Convierte a dict: `update.to_dict()`
3. POST a `API_URL/webhook` (timeout 30s)
4. Parsea respuesta JSON (método "sendMessage")
5. Envía respuesta al usuario

**Configuración:**
- `TELEGRAM_BOT_TOKEN`: Token del bot
- `API_URL`: Default `http://backend:8000/webhook` (dentro de Docker)

### Deployment Configurations

**Local Development** (`docker-compose.local.yml`):
```bash
docker compose up  # usa .env con COMPOSE_FILE=docker-compose.local.yml
```

**Servicios:**
- `postgres_db_local`: PostgreSQL 16 + pgvector, puerto 5432
- `fastapi_backend_local`: FastAPI, puerto 8000
- `telegram_bot_local`: Bot en modo polling

**Acceso:**
- API: http://localhost:8000
- API docs: http://localhost:8000/docs
- Database: localhost:5432 (user: postgres, db: postgres)

**Production** (`docker-compose.yml`):
- Red externa `webapp` compartida con Traefik
- Sin puertos expuestos (solo via Traefik)
- Labels Traefik para routing a `ph.berguecio.cl`
- SSL manejado por Traefik

## Development Commands

### Starting the Application

**Local development:**
```bash
docker compose up -d
docker compose logs -f

# Ver logs específicos
docker compose logs -f backend
docker compose logs -f telegram_bot
```

Access at:
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs
- Database: localhost:5432

**Production (requires Traefik):**
```bash
docker network create webapp  # Primera vez
docker compose up -d
```

### Database Migrations

**Creating a new migration:**
```bash
docker compose exec backend alembic revision --autogenerate -m "description"
```

**Applying migrations:**
```bash
docker compose exec backend alembic upgrade head
# or
docker compose exec backend bash migrate.sh
```

**Viewing history:**
```bash
docker compose exec backend alembic history
docker compose exec backend alembic current
```

**Rollback:**
```bash
docker compose exec backend alembic downgrade -1
```

### Rebuilding

```bash
# Rebuild after Dockerfile/dependencies change
docker compose up -d --build

# Restart single service
docker compose restart backend

# Stop everything
docker compose down

# Delete volumes (includes database!)
docker compose down -v
```

### Database Access

```bash
# psql inside container
docker compose exec postgres_db psql -U postgres -d postgres

# From host (if psql installed)
PGPASSWORD=postgres psql -h localhost -U postgres -d postgres
```

### Running CLI Scripts

```bash
# Búsqueda semántica
docker compose exec backend python scripts/cli_search.py search "beach photos"
docker compose exec backend python scripts/cli_search.py search "sunset" --event-id 1

# Ver estadísticas de embeddings
docker compose exec backend python scripts/cli_search.py stats

# Backfill embeddings (generar embeddings faltantes)
docker compose exec backend python scripts/cli_search.py backfill
docker compose exec backend python scripts/cli_search.py backfill --event-id 1 --dry-run

# Listar memorias
docker compose exec backend python scripts/cli_search.py list --with-embeddings
```

## Key Patterns

### Adding a New Tool

1. Create tool in `backend/agent/tools/implementations/`:
```python
from ..base_tool import BaseTool, ExecutionContext

class MyNewTool(BaseTool):
    @property
    def name(self) -> str:
        return "my_new_tool"

    @property
    def description(self) -> str:
        return "What this tool does"

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "param": {"type": "string", "description": "Description"}
            },
            "required": ["param"]
        }

    async def execute(self, input: dict, ctx: ExecutionContext) -> dict:
        # Access dependencies from ctx:
        # ctx.db, ctx.user, ctx.s3_service, ctx.telegram_service
        # ctx.metadata (has_photo, photo_file_id, etc.)

        result = do_something(input["param"])
        return {"success": True, "data": result}
```

2. Import in `backend/agent/tools/implementations/__init__.py`:
```python
from .my_new_tool import MyNewTool
```

Tool auto-registers on import!

3. Update system prompt in `AnthropicAgent` to mention the new tool

### Adding a New Database Model

1. Add model to `backend/models.py`:
```python
class MyModel(Base):
    __tablename__ = "my_table"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    # ...
```

2. Import in `backend/alembic/env.py` for autogeneration
3. Create migration: `docker compose exec backend alembic revision --autogenerate -m "add my_model"`
4. Review migration file, apply: `docker compose exec backend alembic upgrade head`
5. Add service methods in `DatabaseService` if needed
6. Create tool to interact with new model if needed

### Working with Images

**Upload flow:**
```python
# In a tool's execute method
if ctx.metadata.get("has_photo"):
    file_id = ctx.metadata["photo_file_id"]

    # Download from Telegram
    image_bytes = await ctx.telegram_service.download_file(file_id)

    # Optional: Generate description with Claude Vision
    description = await image_service.describe_image(image_bytes)

    # Upload to S3
    image_url = ctx.s3_service.upload_image(
        image_bytes,
        filename=f"{ctx.user.id}_{event_id}_{timestamp}.jpg"
    )

    # Save to database
    memory = DatabaseService.add_memory(
        db=ctx.db,
        event_id=event_id,
        user_id=ctx.user.id,
        text=description,  # or user's caption
        image_url=image_url
    )
```

**Retrieve with presigned URLs:**
```python
memories = DatabaseService.list_event_memories(db, event_id)
for memory in memories:
    if memory.image_url:
        # Generate temporary URL (1 hour expiration)
        presigned_url = s3_service.generate_presigned_url(memory.image_url)
        # Include in response to user
```

### Working with Embeddings

**Manual backfill** (via CLI):
```bash
docker compose exec backend python scripts/cli_search.py backfill
```

**Search:**
```python
from services.search import SearchService
from services.embedding import EmbeddingService

# Create query embedding
query_embedding = embedding_service.embed_text(
    "beach sunset photos",
    input_type="query"
)

# Search
results = SearchService.search_memories(
    db=db,
    query_embedding=query_embedding,
    event_id=1,  # optional
    top_k=10,
    threshold=0.7  # cosine similarity threshold
)
```

## Environment Variables

### Required

```bash
# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-...

# Voyage AI Embeddings
VOYAGE_API_KEY=pa-...

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...

# Database
DATABASE_URL=postgresql://postgres:postgres@postgres_db:5432/postgres
```

### Optional

```bash
# AWS S3 (if not set, uses mock mode with placeholder URLs)
AWS_S3_BUCKET=my-bucket-name
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1

# Bot API URL (for telegram-bot service)
API_URL=http://backend:8000/webhook

# Docker Compose
COMPOSE_FILE=docker-compose.local.yml
```

## Current Tools Available

El agente tiene acceso a estas tools:

1. **create_event** - Crea un evento y agrega al creador automáticamente
2. **join_event** - Une a un usuario a un evento existente
3. **add_memory** - Agrega memoria (texto/foto) a un evento
   - Maneja descarga de foto, upload a S3, guardado en BD
   - **Valida que el usuario esté en el evento**
4. **list_events** - Lista eventos del usuario
5. **list_memories** - Lista memorias de un evento
   - Genera URLs presigned para fotos (válidas 1 hora)
6. **get_faq** - Retorna ayuda contextual por tópico

## Important Notes

### Agent Architecture
- **No hay endpoints REST CRUD tradicionales**
- Todo funciona via conversación natural con el agente
- El agente decide qué tools usar basándose en el contexto
- System prompt incluye contexto dinámico (usuario, si hay foto, etc.)

### Database
- PostgreSQL con extensión **pgvector** (requerida para embeddings)
- Embeddings son Vector(1024) para Voyage AI
- Índice HNSW creado automáticamente en migrations para búsqueda rápida

### Images
- S3 en modo mock si AWS_S3_BUCKET no está configurado
- URLs presigned expiran en 1 hora
- Claude Vision describe fotos automáticamente (en backfill)

### Embeddings
- **No se generan automáticamente** al crear memories
- Usar `cli_search.py backfill` para generar embeddings faltantes
- Backfill descarga imágenes, las describe con Claude Vision, y genera embeddings

### Bot
- Usa polling en lugar de webhooks (más simple para desarrollo)
- Timeout de 30s para llamadas al backend
- Maneja tanto texto como fotos

### Migrations
- Alembic debe poder importar todos los modelos
- Asegurar que nuevos models estén en `alembic/env.py`
- Revisar migrations autogeneradas antes de aplicar

### Testing
- No hay tests automatizados actualmente
- Testing manual via Telegram bot
- CLI tools útiles para testing de búsqueda semántica

### Security
- CORS completamente abierto (`allow_origins=["*"]`)
- No hay autenticación/autorización
- Para producción: restringir CORS, agregar auth

## TODOs / Limitaciones Conocidas

- [ ] Embeddings no se generan automáticamente (requiere backfill manual)
- [ ] Sin autenticación/autorización
- [ ] Sin tests automatizados
- [ ] Sin paginación en list operations
- [ ] Sin cache (Redis)
- [ ] Bot usa polling (considerar webhooks para producción)
- [ ] Búsqueda semántica tiene infraestructura completa pero no está expuesta como tool del agente

## Future Features (del roadmap)

- Semantic search integration en tools del agente
- WhatsApp integration
- Web frontend
- Face recognition en fotos
- Automatic event suggestions basado en contexto/fecha
- Memory highlights/summaries automáticos
