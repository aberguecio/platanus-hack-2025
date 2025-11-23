#!/bin/bash
# Script para monitorear la cola en tiempo real (cada 2 segundos)

echo "🔄 Monitoreando cola ARQ en tiempo real (Ctrl+C para salir)"
echo "============================================================="
echo ""

watch -n 2 "
echo '📦 Batches por usuario:'
docker compose exec -T redis redis-cli KEYS 'batch:*' 2>/dev/null | head -n 5

echo ''
echo '⏳ Jobs pendientes:'
docker compose exec -T redis redis-cli KEYS 'arq:queue:*' 2>/dev/null | wc -l | xargs echo 'Total:'

echo ''
echo '✅ Jobs completados (últimos):'
docker compose exec -T redis redis-cli KEYS 'arq:result:*' 2>/dev/null | head -n 3

echo ''
echo '📊 Redis Stats:'
docker compose exec -T redis redis-cli INFO stats 2>/dev/null | grep -E 'total_commands_processed|instantaneous_ops_per_sec'

echo ''
echo '💾 Memoria:'
docker compose exec -T redis redis-cli INFO memory 2>/dev/null | grep 'used_memory_human'

echo ''
echo '🔥 Última actualización:' \$(date '+%H:%M:%S')
"

