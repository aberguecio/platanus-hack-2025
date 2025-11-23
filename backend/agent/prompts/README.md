# Sistema de Prompts v2 - Arquitectura Híbrida

## Resumen

Sistema de prompts rediseñado siguiendo los principios de **Effective Context Engineering** de Anthropic:
- ✅ Formato híbrido (JSON + texto plano)
- ✅ Compaction strategy para conversaciones largas
- ✅ Context management inteligente
- ✅ Few-shot examples estructurados
- ✅ **Flujo conversacional de enriquecimiento de recuerdos**

## Estructura de Archivos

```
prompts/
├── manifest.json                    # Orquestación y configuración
├── core/
│   ├── identity.txt                 # Personalidad del bot (prosa)
│   └── instructions.xml             # Instrucciones estructuradas (XML)
├── examples/
│   ├── event_creation.json          # Few-shot: crear eventos
│   ├── photo_upload.json            # Few-shot: subir fotos
│   ├── context_inference.json       # Few-shot: inferencia de contexto
│   ├── ambiguity_handling.json      # Few-shot: resolver ambigüedades
│   ├── error_recovery.json          # Few-shot: manejo de errores
│   ├── memory_enrichment.json       # Few-shot: enriquecimiento conversacional con fotos
│   └── text_memory_capture.json     # ⭐ NUEVO: guardar historias en texto
├── context/
│   ├── conversation.py              # Gestión de historial con compaction
│   └── images.py                    # Gestión de contexto de imágenes
└── prompt_builder_v2.py             # Orchestrator principal

ARCHIVOS OBSOLETOS (se pueden eliminar):
- base_system.txt
- photo_handling.txt
- tools_description.txt
- prompt_builder.py (versión vieja)
```

## Características Principales

### 1. Manifest-Based Configuration

**`manifest.json`** controla toda la orquestación:
- Rutas a componentes core
- Lista de examples a cargar
- Estrategia de compaction
- Configuración de modelo (Sonnet 4.5)
- Comportamiento del agente

### 2. Hybrid Format

**Prosa en .txt:**
- Fácil de editar
- Git-friendly
- Syntax highlighting

**Datos estructurados en .json:**
- Examples validables
- Fácil de parsear
- Consistencia garantizada

### 3. Smart Context Management

**ConversationContext:**
- Sliding window con priorización
- Messages con fotos = mayor prioridad
- Messages con eventos = mayor prioridad
- Compaction automático después de 50 mensajes

**ImageContext:**
- Modo actual: `descriptions_only`
- Usa descripciones de Claude Vision en lugar de imágenes completas
- Ahorro de ~400-800 tokens por imagen en historial

### 4. Flujo de Enriquecimiento de Recuerdos

**FASE 1: Guardar**
- Foto → Guardar en evento → Confirmar

**FASE 2: Enriquecer**
- Claude Vision analiza la imagen
- Hace pregunta MUY específica basada en lo que ve
- Máximo 2 preguntas por foto
- Guarda contexto enriquecido

**Ejemplo:**
```
Usuario: [envía foto de restaurante]
Bot: "Listo, guardada en 'Cumpleaños' ✨ Veo que estaban en un
      restaurante con harta comida, ¿qué estaban celebrando?"
Usuario: "El cumpleaños de mi hermana"
Bot: "¿Qué tal estuvo la comida?"
Usuario: "Increíble, pedimos sushi"
Bot: "Qué rico! Queda todo guardado 📸"
```

### 5. ⭐ NUEVO: Captura de Memories en Texto (Sin Fotos)

El agente ahora identifica y guarda automáticamente historias, descripciones y sentimientos que el usuario comparte **solo en texto**, sin necesidad de fotos.

**Señales de que es un recuerdo:**
- Descripciones detalladas de experiencias pasadas
- Emociones y sentimientos sobre momentos específicos
- Detalles de personas, lugares, o situaciones
- Respuestas a preguntas de enriquecimiento (después de subir fotos)

**Cuándo guarda:**
- Si mencionan un evento específico Y cuentan una historia → Guardar en ese evento
- Si están en contexto de evento reciente (últimos 10 mensajes) → Guardar ahí
- Si NO hay contexto claro → Pregunta a qué evento va

**Ejemplo 1 - Después de crear evento:**
```
Usuario: "crea evento hackaton"
Bot: "Listo! Evento 'hackaton' creado 🎉"
Usuario: "Fue una noche intensa. Nuestro equipo trabajó hasta las 5am
         construyendo una app de memorias con IA. Ganamos el premio a
         mejor UX y nos dieron pizza gratis toda la noche"
Bot: "Genial! Guardado en 'hackaton' 🏆"
```

**Ejemplo 2 - Respuesta a pregunta de enriquecimiento:**
```
Usuario: [foto de playa]
Bot: "Listo, guardada en 'Vacaciones' ✨ ¿Cómo estuvo ese día?"
Usuario: "Increíble! El agua estaba cristalina, vimos peces de colores.
         Los niños construyeron castillos de arena enormes"
Bot: "Qué lindo! ¿Con quién estabas?"
Usuario: "Con mi familia: mi esposa y mis 3 hijos"
Bot: "Hermoso momento! Todo guardado en 'Vacaciones' 🏖️"
[Cada respuesta del usuario se guarda como memory separada]
```

**Ejemplo 3 - Historia sin contexto previo:**
```
Usuario: "Ayer fuimos a un restaurante increíble, la comida estuvo
         espectacular. Pedimos pasta carbonara y tiramisú de postre"
Bot: "¿A qué evento va este recuerdo?"
Usuario: "A viaje a italia"
Bot: "Listo, guardado en 'viaje a italia' ✨"
```

**NO guarda conversación casual:**
- "hola", "gracias", "ok", "bien"
- Preguntas sobre cómo funciona el bot
- Comandos simples

## Datos Guardados

### Message Model (actualizado)

```python
class Message:
    content: str                    # Texto del usuario
    photo_s3_url: str               # URL de la foto en S3
    image_description: str          # Claude Vision description
    embedding: Vector(1024)         # Voyage AI embedding
```

El campo `image_description` permite:
- Contexto visual en el historial sin incluir imágenes completas
- Búsqueda semántica sobre contenido visual
- Preguntas específicas del agente basadas en lo que "vio"

## Configuración

### Model Selection

Configurado en `manifest.json`:
```json
{
  "settings": {
    "model": "claude-sonnet-4-5-20250929",
    "max_tokens": 1024
  }
}
```

### Context Strategy

```json
{
  "context_strategy": {
    "max_history_messages": 10,
    "compaction": {
      "enabled": true,
      "trigger_threshold": 50,
      "strategy": "sliding_window_with_summary"
    },
    "event_context_window": 10,
    "images": {
      "mode": "descriptions_only"
    }
  }
}
```

### Behavior

```json
{
  "behavior": {
    "response_style": "concise",
    "error_tone": "transparent",
    "proactive_event_inference": true,
    "ambiguity_resolution": "ask_with_suggestion"
  }
}
```

## Usage

### En AnthropicAgent

```python
from .prompts.prompt_builder_v2 import get_prompt_builder

builder = get_prompt_builder()

# Build system prompt
system_prompt = builder.build_system_prompt(
    telegram_id=ctx.telegram_id,
    username=ctx.username,
    first_name=ctx.first_name,
    has_photo=ctx.has_photo,
    conversation_history=ctx.conversation_history,
    include_examples=True  # Siempre incluir para comportamiento consistente
)

# Format conversation history
formatted_history = builder.format_conversation_history(
    messages=ctx.conversation_history,
    total_message_count=len(ctx.conversation_history)
)
```

## Principios de Diseño

Basado en [Anthropic's Context Engineering Guide](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents):

1. **Smallest possible set of high-signal tokens**
   - Descriptions en lugar de imágenes completas en historial
   - Compaction de conversaciones largas
   - Examples relevantes, no exhaustivos

2. **Right altitude**
   - Ni muy prescriptivo (evita lógica frágil)
   - Ni muy vago (clara dirección al agente)
   - XML structure para organización clara

3. **Progressive disclosure**
   - Context se carga dinámicamente
   - Examples se formatean on-demand
   - Historial procesado con priorización

4. **Just-in-time retrieval**
   - Imágenes no se cargan hasta que se necesitan
   - Examples se cargan del filesystem al construir prompt
   - Manifiest singleton para performance

## Token Budget Estimation

**Sin nuevo sistema:**
- System prompt: ~2000 tokens
- Historial (10 msgs con imágenes): ~5000-8000 tokens
- **Total: ~7000-10000 tokens**

**Con nuevo sistema:**
- System prompt: ~1500 tokens (optimizado)
- Historial (10 msgs con descripciones): ~2000-3000 tokens
- Examples: ~1500 tokens
- **Total: ~5000-6000 tokens** ✅

**Ahorro: ~30-40% en tokens de contexto**

## Próximos Pasos

- [ ] Eliminar archivos obsoletos (base_system.txt, etc.)
- [ ] Implementar summarization para compaction
- [ ] Agregar métricas de token usage
- [ ] A/B test: descriptions vs últimas 2 imágenes completas
- [ ] Implementar tools para editar/eliminar memories
- [ ] Agregar búsqueda semántica como tool del agente

## Testing

Para probar el nuevo sistema:

1. Enviar foto al bot
2. Verificar que guarde correctamente
3. Verificar que haga pregunta específica basada en Claude Vision
4. Responder y verificar seguimiento (máx 2 preguntas)
5. Enviar otra foto y verificar que use contexto de evento activo

**Logs a revisar:**
```bash
docker compose logs -f backend | grep AGENT
docker compose logs -f backend | grep DATABASE_SERVICE
```
