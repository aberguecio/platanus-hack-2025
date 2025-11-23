import json
from typing import Dict, List, Any
from arq import ArqRedis
import asyncio

class MessageBatcher:
    """Agrupa mensajes por usuario con ventana de tiempo"""

    def __init__(self, redis_pool: ArqRedis, delay_seconds: float = 5):
        self.redis = redis_pool
        self.delay = delay_seconds
        self.pending_jobs = {}  # {user_id: job_id}

    async def add_message(self, user_id: str, chat_id: int, update: Dict[str, Any]):
        """
        Agrega mensaje al batch. Cancela job anterior y programa nuevo
        con delay resetado (ventana de agrupación).
        """
        batch_key = f"batch:{user_id}"

        # Obtener batch actual
        batch_data = await self.redis.get(batch_key)
        if batch_data:
            if isinstance(batch_data, bytes):
                batch_data = batch_data.decode('utf-8')
            updates = json.loads(batch_data)
        else:
            updates = []

        updates.append(update)

        # Guardar batch actualizado con TTL
        await self.redis.setex(
            batch_key,
            int(self.delay * 3),  # TTL mayor que delay
            json.dumps(updates)
        )

        # Cancelar job anterior si existe
        if user_id in self.pending_jobs:
            old_job_id = self.pending_jobs[user_id]
            try:
                # ARQ permite cancelar jobs antes de ejecutarse
                await self.redis.delete(f"arq:job:{old_job_id}")
            except Exception as e:
                print(f"[BATCHER] Could not cancel old job: {e}")

        # Encolar nuevo job con delay (defer_by)
        job = await self.redis.enqueue_job(
            "process_message_batch",
            user_id,
            chat_id,
            updates,
            _defer_by=self.delay
        )

        self.pending_jobs[user_id] = job.job_id

        print(f"[BATCHER] User {user_id}: {len(updates)} msgs, job {job.job_id[:8] if len(job.job_id) >= 8 else job.job_id}")
        return job.job_id

    async def clear_batch(self, user_id: str):
        """Limpia batch después de procesamiento"""
        await self.redis.delete(f"batch:{user_id}")
        self.pending_jobs.pop(user_id, None)

