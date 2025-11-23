#!/bin/bash
# Script para monitorear la cola de ARQ desde la terminal

echo "🔍 Monitoreando cola de ARQ/Redis..."
echo ""

# Ejecutar redis-cli dentro del contenedor
docker compose exec redis redis-cli << 'EOF'

-- Ver todas las keys relacionadas con ARQ
KEYS arq:*

-- Ver jobs en cola (pending)
KEYS arq:queue:*

-- Ver jobs en progreso
KEYS arq:result:*

-- Ver info general de Redis
INFO stats

-- Monitorear comandos en tiempo real (Ctrl+C para salir)
MONITOR
EOF

