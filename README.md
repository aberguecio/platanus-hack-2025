# Full Stack Application

Stack completo con Next.js (frontend), FastAPI (backend) y SQLite (base de datos) usando Docker Compose.

## Stack Tecnológico

- **Frontend**: Next.js 14 con TypeScript
- **Backend**: FastAPI con Python
- **Base de datos**: SQLite
- **Migraciones**: Alembic
- **Containerización**: Docker & Docker Compose

## Estructura del Proyecto

```
ph2/
├── backend/
│   ├── alembic/              # Migraciones de base de datos
│   │   ├── versions/         # Archivos de migración
│   │   ├── env.py           # Configuración de Alembic
│   │   └── script.py.mako   # Template para migraciones
│   ├── main.py              # Aplicación FastAPI
│   ├── models.py            # Modelos SQLAlchemy
│   ├── schemas.py           # Schemas Pydantic
│   ├── database.py          # Configuración de base de datos
│   ├── requirements.txt     # Dependencias Python
│   ├── Dockerfile
│   ├── alembic.ini          # Configuración Alembic
│   └── migrate.sh           # Script de migración
├── frontend/
│   ├── app/
│   │   ├── layout.tsx       # Layout principal
│   │   └── page.tsx         # Página principal
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.js
│   └── Dockerfile
└── docker-compose.yml
```

## Requisitos Previos

- Docker
- Docker Compose

## Instalación y Ejecución

Hay dos configuraciones disponibles:

### Desarrollo Local

Para desarrollo local con puertos expuestos:

```bash
# Levantar los servicios
docker compose -f docker-compose.local.yml up -d

# Ver logs
docker compose -f docker-compose.local.yml logs -f

# Detener
docker compose -f docker-compose.local.yml down
```

**Acceso:**

- **Frontend**: <http://localhost:3000>
- **Backend API**: <http://localhost:8000>
- **API Docs (Swagger)**: <http://localhost:8000/docs>
- **API Redoc**: <http://localhost:8000/redoc>

### Producción con Traefik

Para producción usando Traefik como reverse proxy:

```bash
# Asegurarse de que la red webapp existe
docker network create webapp

# Levantar los servicios
docker compose up -d

# Ver logs
docker compose logs -f

# Detener
docker compose down
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

## Migraciones de Base de Datos

### Crear una nueva migración

Cuando modifiques los modelos en [backend/models.py](backend/models.py), necesitas crear una migración:

```bash
# Entrar al contenedor del backend
docker-compose exec backend bash

# Crear una migración automática
alembic revision --autogenerate -m "Descripción del cambio"

# Salir del contenedor
exit
```

### Aplicar migraciones

```bash
# Entrar al contenedor del backend
docker-compose exec backend bash

# Aplicar todas las migraciones pendientes
alembic upgrade head

# O usar el script incluido
bash migrate.sh

# Salir del contenedor
exit
```

### Ver historial de migraciones

```bash
docker-compose exec backend alembic history
```

### Revertir migración

```bash
docker-compose exec backend alembic downgrade -1
```

## Ejemplo: Agregar un nuevo campo

1. Editar [backend/models.py](backend/models.py):

```python
class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    completed = Column(Boolean, default=False)
    priority = Column(String, default="medium")  # NUEVO CAMPO
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

2. Crear la migración:

```bash
docker-compose exec backend alembic revision --autogenerate -m "add priority field"
```

3. Aplicar la migración:

```bash
docker-compose exec backend alembic upgrade head
```

## Comandos Útiles

### Ver logs

```bash
# Todos los servicios
docker-compose logs -f

# Solo backend
docker-compose logs -f backend

# Solo frontend
docker-compose logs -f frontend

```

### Reiniciar servicios

```bash
# Reiniciar todos los servicios
docker-compose restart

# Reiniciar solo el backend
docker-compose restart backend
```

### Detener servicios

```bash
docker-compose down
```

### Detener y eliminar volúmenes (borra la base de datos)

```bash
docker-compose down -v
```

### Reconstruir imágenes

```bash
docker-compose up -d --build
```

## API Endpoints

### Items

- `GET /` - Mensaje de bienvenida
- `GET /health` - Health check
- `GET /items/` - Listar todos los items
- `GET /items/{item_id}` - Obtener un item específico
- `POST /items/` - Crear un nuevo item
- `PUT /items/{item_id}` - Actualizar un item
- `DELETE /items/{item_id}` - Eliminar un item

### Ejemplo de Request Body (POST/PUT)

```json
{
  "title": "Mi tarea",
  "description": "Descripción de la tarea",
  "completed": false
}
```

## Acceso a la Base de Datos

La base de datos SQLite se guarda en el archivo [backend/app.db](backend/app.db). Puedes acceder a ella usando:

### Desde el contenedor del backend

```bash
docker-compose exec backend sqlite3 app.db
```

### Desde tu máquina local

Si tienes SQLite instalado:

```bash
sqlite3 backend/app.db
```

El archivo de base de datos se persiste en el volumen montado, por lo que los datos se mantienen entre reinicios del contenedor.

## Desarrollo

### Modificar el backend

Los cambios en los archivos Python se recargan automáticamente gracias a `--reload` en uvicorn.

### Modificar el frontend

Los cambios en los archivos de Next.js se recargan automáticamente en modo desarrollo.

## Troubleshooting

### Puerto ya en uso

Si algún puerto está en uso, puedes modificar los puertos en [docker-compose.yml](docker-compose.yml):

```yaml
ports:
  - "PUERTO_HOST:PUERTO_CONTENEDOR"
```

### Reconstruir todo desde cero

```bash
docker-compose down -v
docker-compose up -d --build
```

### Ver errores de migración

```bash
docker-compose exec backend alembic current
docker-compose logs backend
```

## Próximos Pasos

- Agregar autenticación (JWT)
- Implementar tests
- Agregar validación de datos
- Implementar paginación
- Agregar filtros y búsqueda
- Implementar cache con Redis
- Implementar CSS framework (Tailwind CSS con Shadcn UI?)
- LLM integration (Claude, OpenAI, etc.)
