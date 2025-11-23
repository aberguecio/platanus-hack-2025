#!/bin/bash
# Script para ver estadísticas de la cola ARQ

echo "📊 Estadísticas de Cola ARQ"
echo "=============================="
echo ""

echo "🔢 Total de keys ARQ:"
docker compose exec -T redis redis-cli KEYS "arq:*" | wc -l

echo ""
echo "📦 Batches pendientes por usuario:"
docker compose exec -T redis redis-cli KEYS "batch:*"

echo ""
echo "⏳ Jobs en cola (pending):"
docker compose exec -T redis redis-cli KEYS "arq:queue:*"

echo ""
echo "✅ Resultados de jobs (últimos 10 min):"
docker compose exec -T redis redis-cli KEYS "arq:result:*" | head -n 10

echo ""
echo "📈 Info de Redis:"
docker compose exec -T redis redis-cli INFO stats | grep -E "total_commands_processed|instantaneous_ops_per_sec|connected_clients"

echo ""
echo "💾 Uso de memoria:"
docker compose exec -T redis redis-cli INFO memory | grep -E "used_memory_human|used_memory_peak_human"

