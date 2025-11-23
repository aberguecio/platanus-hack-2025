import os
from dotenv import load_dotenv

# Load environment variables from the root .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

from typing import List, Dict, Any
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from agent import AnthropicAgent
from agent.services import MessagingService
from agent.tools import get_registry, ExecutionContext
from services import DatabaseService, TelegramService, S3Service
from services.embedding import EmbeddingService
from services.image import ImageService
from services.search import SearchService
from services.speech import SpeechService
from schemas import TelegramUpdate
# Import models to ensure SQLAlchemy recognizes them
from models import User, Event, Memory, Message, LoginRequest
from enums import MediaTypeEnum
from database import engine, Base

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Memories Bot API", version="1.0.0")

# Initialize services
agent = AnthropicAgent()
s3_service = S3Service()

# Initialize SpeechService if OpenAI API key is available
speech_service = None
try:
    speech_service = SpeechService()
    print("[MAIN] SpeechService initialized - voice messages will be transcribed")
except ValueError as e:
    print(f"[MAIN] SpeechService not initialized: {e}")
    print("[MAIN] Voice messages will not be transcribed")

telegram_service = TelegramService(
    bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
    speech_service=speech_service
)

image_service = ImageService(
    telegram_service=telegram_service,
    s3_service=s3_service
)

# Get tool registry (tools are auto-registered on import)
tool_registry = get_registry()

# Initialize Messaging service (coordinates agent, telegram, and database)
messaging_service = MessagingService(
    agent=agent,
    telegram_service=telegram_service,
    database_service=DatabaseService,
    s3_service=s3_service,
    image_service=image_service
)


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "memories-bot"}


@app.post("/webhook")
async def telegram_webhook(update: TelegramUpdate, db: Session = Depends(get_db)):
    """
    Main webhook endpoint that receives raw Telegram updates and processes them.

    Receives a Telegram Update object, processes it with the AI agent via MessagingService,
    and returns a Telegram Bot API response.

    La lógica de procesamiento está ahora encapsulada en MessagingService.
    """
    return await messaging_service.process_response(update, db)


# ============================================================================
# API Endpoints for Frontend
# ============================================================================

from fastapi.middleware.cors import CORSMiddleware
from typing import List
from schemas import Memory as MemorySchema, EventWithMemories, Event as EventSchema

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/memories", response_model=List[MemorySchema])
def get_memories(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get a list of memories (photos/videos) for the frontend feed.
    """
    memories = db.query(Memory).order_by(Memory.created_at.desc()).offset(skip).limit(limit).all()
    return memories


@app.get("/events", response_model=List[EventWithMemories])
def get_events(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all events with their related memories for the frontend.
    Events are ordered by event_date (or created_at if event_date is null).
    """
    events = db.query(Event).order_by(
        Event.event_date.desc().nullslast(),
        Event.created_at.desc()
    ).offset(skip).limit(limit).all()

    # Convert S3 URIs to presigned URLs for all memories
    for event in events:
        for memory in event.memories:
            if memory.s3_url and memory.s3_url.startswith("s3://"):
                memory.s3_url = s3_service.generate_presigned_url(memory.s3_url)

    return events


@app.get("/events/{event_id}", response_model=EventWithMemories)
def get_event(event_id: int, db: Session = Depends(get_db)):
    """
    Get a specific event with its memories.
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Event not found")

    # Convert S3 URIs to presigned URLs for all memories
    for memory in event.memories:
        if memory.s3_url and memory.s3_url.startswith("s3://"):
            memory.s3_url = s3_service.generate_presigned_url(memory.s3_url)

    return event


@app.get("/search/memories")
def search_memories(
    q: str,
    limit: int = 50,
    threshold: float = 0.0,
    event_id: int = None,
    db: Session = Depends(get_db)
):
    """
    Search memories using AI semantic search.

    Args:
        q: Search query (natural language)
        limit: Maximum number of results
        threshold: Minimum similarity score (0-1)
        event_id: Optional filter by event ID
    """
    try:
        results = SearchService.search_memories(
            db=db,
            query=q,
            top_k=limit,
            threshold=threshold,
            event_id=event_id
        )

        # Convert SearchResult objects to dict format
        return [
            {
                "id": r.memory.id,
                "event_id": r.memory.event_id,
                "user_id": r.memory.user_id,
                "text": r.memory.text,
                "s3_url": r.memory.s3_url,
                "media_type": r.memory.media_type,
                "memory_metadata": r.memory.memory_metadata,
                "created_at": r.memory.created_at,
                "similarity_score": round(r.similarity_score, 4),
            }
            for r in results
        ]
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# Event Capsule Endpoints
# ============================================================================

from collections import defaultdict
from datetime import datetime as dt

@app.get("/events/{event_id}/best-photos")
def get_best_photos(
    event_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get the best photos from an event using semantic search.
    Falls back to direct database query if semantic search returns no results.
    """
    try:
        print(f"[get_best_photos] Fetching best photos for event_id={event_id}, limit={limit}")
        results = SearchService.search_memories(
            db=db,
            query="beautiful high quality memorable amazing photos moments",
            event_id=event_id,
            top_k=limit * 2,  # Get more to filter
            threshold=0.3  # Lowered threshold from 0.5 to get more results
        )

        print(f"[get_best_photos] Search returned {len(results)} results")

        # Filter only images and convert S3 URIs to presigned URLs
        photos = []
        for r in results:
            if r.memory.media_type == "image" and r.memory.s3_url:
                original_url = r.memory.s3_url
                # Generate presigned URL
                if r.memory.s3_url.startswith("s3://"):
                    r.memory.s3_url = s3_service.generate_presigned_url(r.memory.s3_url)
                    print(f"[get_best_photos] Converted S3 URL: {original_url} -> {r.memory.s3_url[:50]}...")

                photo_data = {
                    "id": r.memory.id,
                    "s3_url": r.memory.s3_url,
                    "text": r.memory.text,
                    "created_at": r.memory.created_at,
                    "user_id": r.memory.user_id,
                    "relevance_score": round(r.similarity_score, 4)
                }
                photos.append(photo_data)
                print(f"[get_best_photos] Added photo: id={photo_data['id']}, url={photo_data['s3_url'][:80]}..., has_text={bool(photo_data['text'])}")

                if len(photos) >= limit:
                    break

        # Fallback: If semantic search returned no photos, query database directly
        if len(photos) == 0:
            print(f"[get_best_photos] No photos from semantic search, falling back to direct database query")
            memories = db.query(Memory).filter(
                Memory.event_id == event_id,
                Memory.media_type == MediaTypeEnum.IMAGE,
                Memory.s3_url.isnot(None)
            ).order_by(Memory.created_at.desc()).limit(limit).all()
            
            print(f"[get_best_photos] Direct query found {len(memories)} images")
            
            for memory in memories:
                original_url = memory.s3_url
                # Generate presigned URL
                if memory.s3_url and memory.s3_url.startswith("s3://"):
                    memory.s3_url = s3_service.generate_presigned_url(memory.s3_url)
                    print(f"[get_best_photos] Converted S3 URL: {original_url} -> {memory.s3_url[:50]}...")

                photo_data = {
                    "id": memory.id,
                    "s3_url": memory.s3_url,
                    "text": memory.text,
                    "created_at": memory.created_at,
                    "user_id": memory.user_id,
                    "relevance_score": 0.0  # No relevance score for direct query
                }
                photos.append(photo_data)
                print(f"[get_best_photos] Added photo (fallback): id={photo_data['id']}, url={photo_data['s3_url'][:80]}..., has_text={bool(photo_data['text'])}")

        print(f"[get_best_photos] Returning {len(photos)} photos")
        print(f"[get_best_photos] Photo URLs: {[p['s3_url'][:50] + '...' if len(p['s3_url']) > 50 else p['s3_url'] for p in photos]}")
        return photos
    except Exception as e:
        print(f"[get_best_photos] Error: {str(e)}")
        import traceback
        print(f"[get_best_photos] Traceback: {traceback.format_exc()}")
        return {"error": str(e)}


@app.get("/events/{event_id}/timeline")
def get_event_timeline(event_id: int, db: Session = Depends(get_db)):
    """
    Get memories grouped by date for timeline view.
    """
    print(f"[get_event_timeline] Fetching timeline for event_id={event_id}")
    memories = db.query(Memory).filter(
        Memory.event_id == event_id,
        Memory.s3_url.isnot(None)
    ).order_by(Memory.created_at.asc()).all()

    print(f"[get_event_timeline] Found {len(memories)} memories with s3_url")

    # Convert S3 URIs to presigned URLs
    image_count = 0
    for memory in memories:
        if memory.s3_url and memory.s3_url.startswith("s3://"):
            original_url = memory.s3_url
            memory.s3_url = s3_service.generate_presigned_url(memory.s3_url)
            print(f"[get_event_timeline] Converted S3 URL: {original_url} -> {memory.s3_url[:50]}...")
        if memory.media_type == "image":
            image_count += 1

    print(f"[get_event_timeline] Found {image_count} images out of {len(memories)} memories")

    # Group by date
    timeline = defaultdict(list)
    for memory in memories:
        date_key = memory.created_at.date().isoformat()
        memory_data = {
            "id": memory.id,
            "text": memory.text,
            "s3_url": memory.s3_url,
            "media_type": memory.media_type,
            "created_at": memory.created_at.isoformat(),
            "user_id": memory.user_id
        }
        timeline[date_key].append(memory_data)
        if memory.media_type == "image":
            print(f"[get_event_timeline] Added image to timeline: date={date_key}, id={memory.id}, url={memory.s3_url[:50] if memory.s3_url else 'None'}...")

    # Convert to sorted list
    result = [
        {"date": date, "memories": items}
        for date, items in sorted(timeline.items())
    ]
    print(f"[get_event_timeline] Returning timeline with {len(result)} date groups")
    return result


@app.get("/events/{event_id}/download-images")
def download_event_images(event_id: int, db: Session = Depends(get_db)):
    """
    Download all images from an event as a ZIP file.
    """
    import tempfile
    import zipfile
    import requests
    from pathlib import Path
    
    try:
        print(f"[download_event_images] Fetching images for event_id={event_id}")
        
        # Get event
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Get all image memories
        memories = db.query(Memory).filter(
            Memory.event_id == event_id,
            Memory.media_type == MediaTypeEnum.IMAGE,
            Memory.s3_url.isnot(None)
        ).all()
        
        if not memories:
            raise HTTPException(status_code=404, detail="No images found for this event")
        
        print(f"[download_event_images] Found {len(memories)} images")
        
        # Create temporary directory and ZIP file
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, f"{event.name.replace(' ', '_')}_images.zip")
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for idx, memory in enumerate(memories, 1):
                    try:
                        # Generate presigned URL if needed
                        if memory.s3_url.startswith("s3://"):
                            image_url = s3_service.generate_presigned_url(memory.s3_url)
                        else:
                            image_url = memory.s3_url
                        
                        print(f"[download_event_images] Downloading image {idx}/{len(memories)}: {image_url[:80]}...")
                        
                        # Download image
                        response = requests.get(image_url, timeout=30)
                        response.raise_for_status()
                        
                        # Determine file extension from content type or URL
                        content_type = response.headers.get('content-type', '')
                        if 'jpeg' in content_type or 'jpg' in content_type:
                            ext = 'jpg'
                        elif 'png' in content_type:
                            ext = 'png'
                        elif 'webp' in content_type:
                            ext = 'webp'
                        else:
                            ext = 'jpg'  # default
                        
                        # Create filename
                        filename = f"image_{idx:03d}_{memory.id}.{ext}"
                        
                        # Add to ZIP
                        zipf.writestr(filename, response.content)
                        print(f"[download_event_images] Added {filename} to ZIP")
                        
                    except Exception as e:
                        print(f"[download_event_images] Error downloading image {memory.id}: {e}")
                        continue
            
            print(f"[download_event_images] ZIP file created at {zip_path}")
            
            # Read ZIP file contents into memory BEFORE the temp directory is cleaned up
            with open(zip_path, "rb") as f:
                zip_content = f.read()
        
        # Now temp directory is cleaned up, but we have the content in memory
        from io import BytesIO
        
        return StreamingResponse(
            BytesIO(zip_content),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={event.name.replace(' ', '_')}_images.zip"
            }
        )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"[download_event_images] Error: {str(e)}")
        import traceback
        print(f"[download_event_images] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/events/{event_id}/best-quotes")
def get_best_quotes(
    event_id: int,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """
    Get the best quotes and meaningful moments using semantic search.
    """
    try:
        results = SearchService.search_memories(
            db=db,
            query="emotional meaningful heartfelt funny memorable quotes messages stories",
            event_id=event_id,
            top_k=limit * 3,
            threshold=0.6
        )

        # Filter memories with substantial text
        quotes = []
        for r in results:
            if r.memory.text and len(r.memory.text) > 20:
                # Get user details
                user = r.memory.user if hasattr(r.memory, 'user') and r.memory.user else None

                quotes.append({
                    "id": r.memory.id,
                    "text": r.memory.text,
                    "user_id": r.memory.user_id,
                    "first_name": user.first_name if user else "Anonymous",
                    "last_name": user.last_name if user else "",
                    "created_at": r.memory.created_at,
                    "relevance_score": round(r.similarity_score, 4)
                })

                if len(quotes) >= limit:
                    break

        return quotes
    except Exception as e:
        return {"error": str(e)}


@app.get("/events/{event_id}/stats")
def get_event_stats(event_id: int, db: Session = Depends(get_db)):
    """
    Get statistics and insights about an event.
    """
    from sqlalchemy import func

    memories = db.query(Memory).filter(Memory.event_id == event_id).all()

    if not memories:
        return {
            "total_memories": 0,
            "by_type": {},
            "by_user": [],
            "date_range": None
        }

    # Count by media type
    by_type = defaultdict(int)
    for m in memories:
        media_type = m.media_type or "text"
        by_type[media_type] += 1

    # Count by user
    by_user_dict = defaultdict(int)
    user_details = {}
    for m in memories:
        by_user_dict[m.user_id] += 1
        if m.user_id not in user_details and m.user:
            user_details[m.user_id] = {
                "first_name": m.user.first_name,
                "last_name": m.user.last_name
            }

    by_user = [
        {
            "user_id": user_id,
            "count": count,
            "first_name": user_details.get(user_id, {}).get("first_name", "Unknown"),
            "last_name": user_details.get(user_id, {}).get("last_name", "")
        }
        for user_id, count in sorted(by_user_dict.items(), key=lambda x: x[1], reverse=True)
    ]

    # Date range
    dates = [m.created_at for m in memories if m.created_at]
    date_range = None
    if dates:
        date_range = {
            "start": min(dates).isoformat(),
            "end": max(dates).isoformat()
        }

    return {
        "total_memories": len(memories),
        "by_type": dict(by_type),
        "by_user": by_user,
        "date_range": date_range,
        "unique_contributors": len(by_user_dict)
    }


@app.post("/events/{event_id}/generate-narrative")
async def generate_event_narrative(
    event_id: int, 
    force: bool = True,
    db: Session = Depends(get_db)
):
    """
    Generate an AI narrative blog post about the event.
    Uses Claude to synthesize memories, quotes, and context into a compelling story.
    
    Args:
        event_id: ID of the event to generate narrative for
        force: If True, regenerate narrative even if one already exists. 
               If False (default), returns existing narrative if available.
    """
    try:
        # Get event details
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            return {"error": "Event not found"}

        # Return existing narrative if available and not forcing regeneration
        if not force and event.generated_narrative and event.generated_narrative.strip():
            print(f"[generate_event_narrative] Returning existing narrative for event_id={event_id}")
            return {"narrative": event.generated_narrative}
        print(f"[generate_event_narrative] Regenerating narrative for event_id={event_id}")
        # Get top memories via semantic search
        important_memories = SearchService.search_memories(
            db=db,
            query="important memorable significant meaningful emotional moments experiences",
            event_id=event_id,
            top_k=15,
            threshold=0.5
        )

        # Get best quotes
        quotes_results = SearchService.search_memories(
            db=db,
            query="emotional heartfelt meaningful quotes messages",
            event_id=event_id,
            top_k=5,
            threshold=0.6
        )

        # Bad quotes
        bad_quotes_results = SearchService.search_memories(
            db=db,
            query="bad quotes messages, bad experiences, bad moments",
            event_id=event_id,
            top_k=5,
            threshold=0.6
        )

        # Build prompt for Claude
        memories_text = "\n".join([
            f"- {r.memory.text}" for r in important_memories
            if r.memory.text and len(r.memory.text) > 10
        ][:10])

        quotes_text = "\n".join([
            f'- "{r.memory.text}"' for r in quotes_results
            if r.memory.text and len(r.memory.text) > 20
        ][:5])

        bad_quotes_text = "\n".join([
            f'- "{r.memory.text}"' for r in bad_quotes_results
            if r.memory.text and len(r.memory.text) > 20
        ][:5])

        prompt = f"""Estás escribiendo un artículo visual y atractivo sobre "{event.name}".

Detalles del Evento:
- Nombre: {event.name}
- Fecha: {event.event_date if event.event_date else 'Recientemente'}
- Descripción: {event.description if event.description else 'Una reunión memorable'}

Recuerdos Clave de los Participantes:
{memories_text if memories_text else '(Sin recuerdos aún)'}

Citas Destacadas:
{quotes_text if quotes_text else '(Sin citas aún)'}

Bad quotes:
{bad_quotes_text if bad_quotes_text else '(Sin citas negativas)'}

Escribe una narrativa de 600 palabras en 2-3 SECCIONES CORTAS (separadas por doble salto de línea), cada una de aproximadamente 150-200 palabras. Esto se mostrará con fotos y citas entre secciones.

TÍTULO:
- El título debe ser atractivo y emocional, y debe ser corto y directo.

SECCIÓN 1 - LA APERTURA (150-200 palabras):
- Apertura vívida y sensorial que sumerge a los lectores en un momento clave
- Establece atmósfera y tono emocional
- Usa detalles específicos de los recuerdos

SECCIÓN 2 - EL CORAZÓN (150-200 palabras):
- Qué hizo esto especial y significativo
- Las conexiones, emociones y momentos mágicos
- Teje perspectivas de los participantes de forma natural

SECCIÓN 2.1 - OPCIONAL
- Citas negativas o malas experiencias
- Qué se aprendió de las experiencias negativas
- Qué se hizo para mejorar la próxima vez

SECCIÓN 3 - LA REFLEXIÓN (100-150 palabras - OPCIONAL, incluir solo si hay suficiente contenido):
- Qué se recordará
- Impacto duradero y significado
- Termina con calidez

ESTILO:
- Escribe en TIEMPO PASADO, cálido y auténtico
- Lenguaje literario rico pero CONCISO
- Muestra, no digas - momentos específicos sobre generalizaciones
- Integra citas naturalmente como diálogo cuando sea relevante
- Cada sección debe funcionar visualmente por sí sola

CRÍTICO: Mantén las secciones CORTAS (máximo 150-200 palabras cada una). El diseño alternará texto con fotos/citas para atractivo visual.

Separa las secciones con doble salto de línea (\\n\\n). Escribe SOLO la narrativa en prosa, sin etiquetas de sección ni encabezados.

IMPORTANTE: Escribe todo el contenido en ESPAÑOL."""

        # Use Claude to generate narrative
        response = await agent.send_message(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="Eres un escritor narrativo excepcional que crea historias de eventos emocionalmente poderosas y concisas, optimizadas para diseños visuales con fotos y citas. Escribes exclusivamente en español con un estilo literario cálido y auténtico."
        )

        narrative = response.get("content", [{}])[0].get("text", "")

        # Save narrative to database for caching
        if narrative:
            event.generated_narrative = narrative
            db.commit()
            print(f"[generate_narrative] Saved narrative to database for event_id={event_id}")

        return {"narrative": narrative}

    except Exception as e:
        print(f"Error generating narrative: {e}")
        return {"error": str(e)}

@app.post("/events/{event_id}/generate-narrative-v2")
async def generate_event_narrative_v2(
    event_id: int,
    force: bool = True,
    db: Session = Depends(get_db)
):
    """
    ENHANCED: Generate an intelligent AI narrative using temporal analysis,
    multi-theme discovery, image descriptions, and participant voices.

    Args:
        event_id: ID of the event to generate narrative for
        force: If True, regenerate narrative even if one already exists.
               If False (default), returns existing narrative if available.
    """
    try:
        # Get event details
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            return {"error": "Event not found"}

        # Return existing narrative if available and not forcing regeneration
        if not force and event.generated_narrative and event.generated_narrative.strip():
            print(f"[generate_event_narrative_v2] Returning existing narrative for event_id={event_id}")
            return {"narrative": event.generated_narrative}

        print(f"[generate_event_narrative_v2] 🧠 INTELLIGENT GENERATION for event_id={event_id}")

        # ========================================================================
        # PHASE 1: COMPREHENSIVE DATA COLLECTION
        # ========================================================================

        # Get ALL memories for temporal and thematic analysis
        all_memories = db.query(Memory).filter(
            Memory.event_id == event_id
        ).order_by(Memory.created_at.asc()).all()

        if not all_memories:
            return {"narrative": "No hay suficientes recuerdos para generar una narrativa."}

        print(f"[narrative_v2] 📊 Analyzing {len(all_memories)} total memories")

        # ========================================================================
        # PHASE 2: TEMPORAL ANALYSIS - Discover narrative arc
        # ========================================================================

        total = len(all_memories)
        early_idx = max(1, total // 4)
        late_idx = max(1, 3 * total // 4)

        early_memories = all_memories[:early_idx]
        middle_memories = all_memories[early_idx:late_idx]
        late_memories = all_memories[late_idx:]

        # Get date range - use event_date for start if available, otherwise event created_at
        start_date = event.event_date if event.event_date else event.created_at
        end_date = all_memories[-1].created_at if all_memories else start_date

        date_range = {
            "start": start_date.strftime("%d/%m/%Y") if start_date else "Desconocido",
            "end": end_date.strftime("%d/%m/%Y") if end_date else "Desconocido"
        }

        print(f"[narrative_v2] ⏱️  Temporal phases: Early={len(early_memories)}, Middle={len(middle_memories)}, Late={len(late_memories)}")

        # ========================================================================
        # PHASE 3: MULTI-THEME SEMANTIC SEARCH - Discover natural themes
        # ========================================================================

        themes_to_discover = {
            "emotional_highs": "joy celebration laughter happiness amazing wonderful best incredible moments",
            "connections": "friendship bonding together team collaboration support unity connection",
            "challenges": "difficult hard struggle overcome challenge problem issue",
            "surprises": "unexpected surprise amazing wow incredible unbelievable shocking",
            "learning": "learned realized understood meaningful important significant insight",
            "nostalgia": "remember nostalgia memory thinking back reflecting past"
        }

        theme_results = {}
        for theme_name, query in themes_to_discover.items():
            results = SearchService.search_memories(
                db=db,
                query=query,
                event_id=event_id,
                top_k=5,
                threshold=0.55
            )
            if results:
                theme_results[theme_name] = results
                print(f"[narrative_v2] 🎯 Theme '{theme_name}': {len(results)} matches")

        # ========================================================================
        # PHASE 4: VISUAL CONTEXT - Use image descriptions for storytelling
        # ========================================================================

        visual_moments = db.query(Memory).filter(
            Memory.event_id == event_id,
            Memory.media_type == "image",
            Memory.image_description.isnot(None)
        ).order_by(Memory.created_at.asc()).all()

        print(f"[narrative_v2] 📸 Visual moments with descriptions: {len(visual_moments)}")

        # Build visual narrative context
        visual_context_items = []
        for memory in visual_moments[:10]:  # Top 10 visual moments
            visual_context_items.append({
                "description": memory.image_description,
                "caption": memory.text if memory.text else "",
                "user": memory.user.first_name if memory.user else "Alguien",
                "time": memory.created_at.strftime("%H:%M")
            })

        # ========================================================================
        # PHASE 5: PARTICIPANT VOICE TRACKING - Multiple perspectives
        # ========================================================================

        participant_contributions = defaultdict(list)
        for memory in all_memories:
            if memory.user and memory.text and len(memory.text) > 15:
                participant_contributions[memory.user.first_name].append({
                    "text": memory.text,
                    "has_media": bool(memory.s3_url),
                    "time": memory.created_at
                })

        # Sort by contribution count
        top_voices = sorted(
            participant_contributions.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:5]

        print(f"[narrative_v2] 👥 Top {len(top_voices)} participant voices identified")

        # ========================================================================
        # PHASE 6: BUILD RICH, STRUCTURED PROMPT
        # ========================================================================

        def format_phase_memories(memories, phase_name):
            """Format memories from a temporal phase"""
            items = []
            for m in memories[:8]:  # Max 8 per phase
                if m.text and len(m.text) > 10:
                    prefix = f"[{m.user.first_name}]" if m.user else "[Anónimo]"
                    visual_note = " 📸" if m.s3_url else ""
                    items.append(f"  • {prefix} {m.text[:150]}{visual_note}")
            return "\n".join(items) if items else f"  (Pocos recuerdos en fase {phase_name})"

        def format_theme_findings(theme_name, results):
            """Format discovered theme with examples"""
            if not results:
                return ""
            examples = []
            for r in results[:3]:
                if r.memory.text and len(r.memory.text) > 15:
                    examples.append(f'    - "{r.memory.text[:100]}..." (similitud: {r.similarity_score:.2f})')
            return "\n".join(examples) if examples else ""

        def format_visual_moments(visual_items):
            """Format visual scene descriptions"""
            if not visual_items:
                return "  (No hay descripciones visuales disponibles)"
            scenes = []
            for idx, item in enumerate(visual_items[:6], 1):
                scene = f"  {idx}. [{item['time']}] {item['description']}"
                if item['caption']:
                    scene += f"\n     → {item['user']}: \"{item['caption'][:80]}...\""
                scenes.append(scene)
            return "\n".join(scenes)

        def format_participant_voices(top_contributors):
            """Format participant perspectives"""
            if not top_contributors:
                return "  (Voces de participantes no disponibles)"
            voices = []
            for name, contributions in top_contributors[:4]:
                sample_quote = contributions[0]['text'][:100] if contributions else ""
                voices.append(
                    f"  • {name} ({len(contributions)} contribuciones): \"{sample_quote}...\""
                )
            return "\n".join(voices)

        # Find dominant themes
        dominant_themes = sorted(
            [(name, len(results)) for name, results in theme_results.items()],
            key=lambda x: x[1],
            reverse=True
        )[:3]

        # Build comprehensive prompt
        prompt = f"""Estás escribiendo un artículo narrativo profundo y visualmente rico sobre "{event.name}".

## 📅 CONTEXTO DEL EVENTO
- Nombre: {event.name}
- Fecha del evento: {event.event_date.strftime("%d de %B, %Y") if event.event_date else 'Fecha no especificada'}
- Periodo de captura: {date_range['start']} hasta {date_range['end']}
- Total de momentos documentados: {len(all_memories)}
- Participantes activos: {len(participant_contributions)}

## ⏱️ ARCO TEMPORAL DETECTADO

### Fase Inicial - Los Comienzos ({len(early_memories)} momentos)
{format_phase_memories(early_memories, "inicial")}

### Fase Central - El Corazón del Evento ({len(middle_memories)} momentos)
{format_phase_memories(middle_memories, "central")}

### Fase Final - El Cierre ({len(late_memories)} momentos)
{format_phase_memories(late_memories, "final")}

## 🎯 TEMAS EMERGENTES (Descubiertos mediante análisis semántico)

{chr(10).join([f"**{name.upper().replace('_', ' ')}** ({count} menciones):{chr(10)}{format_theme_findings(name, theme_results.get(name, []))}" for name, count in dominant_themes if count > 0])}

## 📸 MOMENTOS VISUALES CLAVE (De descripciones generadas por IA)
{format_visual_moments(visual_context_items)}

## 👥 VOCES DE PARTICIPANTES
{format_participant_voices(top_voices)}

## 🎨 DETALLES ADICIONALES
- Descripción del evento: {event.description if event.description else 'Evento memorable'}
- Contexto AI: {event.ai_context[:200] if event.ai_context else 'N/A'}

---

## 📝 TU TAREA

Escribe una narrativa de **800-1000 palabras** en **3-4 SECCIONES** (separadas por doble salto de línea) que:

### TÍTULO:
- El título debe ser **enganchador, positivo y emocional**
- Debe ser corto y directo (máximo 8-10 palabras)
- Evita títulos genéricos, captura la esencia única del evento

### SECCIÓN 1: LA APERTURA (250-300 palabras)
- Comienza capturando la **esencia y atmósfera** del evento
- Enfócate en las **memorias, emociones y voces** de los participantes
- Usa detalles específicos de lo que dijeron y sintieron las personas
- Establece el contexto y por qué este evento fue especial
- Las descripciones visuales son **OPCIONALES y mínimas** - úsalas solo si aportan algo esencial, de forma muy sutil
- Prioriza: citas, anécdotas, sentimientos > descripciones de fotos

### SECCIÓN 2: EL DESARROLLO (300-350 palabras)
- Sigue el arco temporal natural (inicio → desarrollo → clímax)
- Teje los temas emergentes descubiertos en el análisis
- Integra múltiples voces de participantes de forma orgánica
- Incluye momentos visuales descritos
- Muestra la evolución emocional y temática

### SECCIÓN 3: LOS MOMENTOS CLAVE (200-250 palabras)
- Destaca los momentos de mayor intensidad emocional
- Incluye conexiones humanas y aprendizajes
- Usa citas directas de participantes cuando sea relevante

### SECCIÓN 4: LA REFLEXIÓN (150-200 palabras)
- Cierra con el significado duradero del evento
- Qué se llevaron los participantes
- Tono cálido y nostálgico

## 🎨 ESTILO REQUERIDO:
- **TIEMPO PASADO** exclusivamente
- **CENTRADO EN PERSONAS**: Prioriza voces, citas, emociones y experiencias de los participantes
- **ESPECÍFICO sobre GENERAL**: Usa nombres, momentos concretos, anécdotas reales
- **LITERARIO pero ACCESIBLE**: Prosa rica pero clara
- **MULTI-PERSPECTIVA**: Equilibra diferentes voces
- **VISUAL CON MODERACIÓN**: Usa descripciones visuales solo cuando sean esenciales, de forma muy sutil
- **AUTÉNTICO**: Basado en datos reales, no inventes
- **POSITIVO y ENGANCHADOR**: Tono optimista que celebra la experiencia compartida

## ⚠️ IMPORTANTE:
- Separa secciones con doble salto de línea (\\n\\n)
- NO incluyas títulos de sección ni encabezados
- Escribe SOLO la narrativa en prosa fluida
- Escribe TODO en ESPAÑOL
- Usa los datos proporcionados, no inventes información

Crea una historia que honre la experiencia colectiva y capture la esencia única de "{event.name}"."""

        print(f"[narrative_v2] 📄 Prompt built with {len(prompt)} characters")

        # ========================================================================
        # PHASE 7: GENERATE WITH CLAUDE
        # ========================================================================

        response = await agent.send_message(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="""Eres un escritor narrativo excepcional especializado en crear historias de eventos emocionalmente poderosas y ricas en detalles.

Tu estilo combina:
- Periodismo narrativo (detalles específicos, múltiples perspectivas)
- Literatura creativa (lenguaje sensorial, arcos emocionales)
- Storytelling visual (integración natural de escenas, sin que se note el análisis técnico)

IMPORTANTE sobre las descripciones visuales:
- USA MUY POCAS descripciones de imágenes, solo cuando sea absolutamente esencial
- En el opening, EVITA relatar descripciones de fotos - enfócate en las voces y emociones de las personas
- Prioriza siempre: citas directas > anécdotas > sentimientos > descripciones visuales
- Si usas algo visual, debe ser extremadamente sutil e integrado, nunca como análisis de fotos

TONO:
- Escribes exclusivamente en español con un tono **cálido, positivo, auténtico y enganchador**
- Celebras la experiencia compartida con optimismo
- Cada palabra cuenta una historia verdadera basada en los datos proporcionados
- Los títulos son memorables y capturan la esencia emocional del evento"""
        )

        narrative = response.get("content", [{}])[0].get("text", "")

        # Save narrative to database for caching
        if narrative:
            event.generated_narrative = narrative
            db.commit()
            print(f"[narrative_v2] ✅ Saved enhanced narrative ({len(narrative)} chars) to database")

        return {"narrative": narrative}

    except Exception as e:
        print(f"[narrative_v2] ❌ Error generating narrative: {e}")
        import traceback
        print(f"[narrative_v2] Traceback: {traceback.format_exc()}")
        return {"error": str(e)}


@app.get("/events/{event_id}/hero-image")
def get_hero_image(event_id: int, db: Session = Depends(get_db)):
    """
    Get the best hero image for the event background.
    """
    try:
        results = SearchService.search_memories(
            db=db,
            query="beautiful landscape wide panoramic scenic artistic high quality photo",
            event_id=event_id,
            top_k=5,
            threshold=0.4
        )

        # Filter only images
        photos = []
        for r in results:
            if r.memory.media_type == "image" and r.memory.s3_url:
                if r.memory.s3_url.startswith("s3://"):
                    r.memory.s3_url = s3_service.generate_presigned_url(r.memory.s3_url)

                photos.append({
                    "s3_url": r.memory.s3_url,
                    "text": r.memory.text,
                    "relevance_score": round(r.similarity_score, 4)
                })

        # Return best photo or first available
        if photos:
            return photos[0]

        # Fallback: get any photo from event
        fallback = db.query(Memory).filter(
            Memory.event_id == event_id,
            Memory.media_type == "image",
            Memory.s3_url.isnot(None)
        ).first()

        if fallback:
            s3_url = fallback.s3_url
            if s3_url.startswith("s3://"):
                s3_url = s3_service.generate_presigned_url(s3_url)
            return {"s3_url": s3_url, "text": fallback.text, "relevance_score": 0}

        return {"s3_url": None}

    except Exception as e:
        return {"error": str(e)}


@app.get("/events/{event_id}/related-events")
def get_related_events(
    event_id: int,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """
    Find events similar to this one using semantic search on memories.
    """
    try:
        # Get representative memories from current event
        current_memories = SearchService.search_memories(
            db=db,
            query="important memorable significant",
            event_id=event_id,
            top_k=8,
            threshold=0.5
        )

        if not current_memories:
            return []

        # Find similar memories in other events
        related_event_scores = defaultdict(list)

        for mem_result in current_memories[:5]:  # Use top 5 memories
            try:
                similar = SearchService.find_similar_memories(
                    db=db,
                    memory_id=mem_result.memory.id,
                    top_k=15,
                    threshold=0.6
                )

                for sim_result in similar:
                    if sim_result.memory.event_id != event_id:
                        related_event_scores[sim_result.memory.event_id].append(
                            sim_result.similarity_score
                        )
            except:
                continue

        # Aggregate scores per event
        event_rankings = []
        for related_event_id, scores in related_event_scores.items():
            if len(scores) >= 2:  # At least 2 connections
                event = db.query(Event).filter(Event.id == related_event_id).first()
                if event:
                    # Get a preview image
                    preview_memory = db.query(Memory).filter(
                        Memory.event_id == related_event_id,
                        Memory.media_type == "image",
                        Memory.s3_url.isnot(None)
                    ).first()

                    preview_url = None
                    if preview_memory and preview_memory.s3_url:
                        preview_url = preview_memory.s3_url
                        if preview_url.startswith("s3://"):
                            preview_url = s3_service.generate_presigned_url(preview_url)

                    event_rankings.append({
                        "id": event.id,
                        "name": event.name,
                        "description": event.description,
                        "event_date": event.event_date.isoformat() if event.event_date else None,
                        "preview_image": preview_url,
                        "similarity_score": round(sum(scores) / len(scores), 4),
                        "connection_count": len(scores)
                    })

        # Sort by similarity
        event_rankings.sort(key=lambda x: x['similarity_score'], reverse=True)

        return event_rankings[:limit]

    except Exception as e:
        print(f"Error finding related events: {e}")
        return {"error": str(e)}


# ============================================================================
# Authentication Endpoints
# ============================================================================

from pydantic import BaseModel
from models.auth import LoginRequest
import uuid
from datetime import datetime, timedelta

class LoginPayload(BaseModel):
    phone_number: str

class VerifyPayload(BaseModel):
    token: str

class AuthResponse(BaseModel):
    token: str
    user: dict

@app.post("/auth/login")
async def login(payload: LoginPayload, db: Session = Depends(get_db)):
    """
    Initiate login flow.
    1. Find user by phone number.
    2. Generate magic link token.
    3. Send link via Telegram.
    """
    # Normalize phone number (basic)
    phone = payload.phone_number.strip()
    
    # Find user
    user = db.query(User).filter(User.phone_number == phone).first()
    if not user:
        # For security, don't reveal if user exists, but here we might want to be helpful
        # If user doesn't exist, we can't send telegram message easily unless we use phone number contact sharing
        # For this hackathon, assume user exists
        return {"message": "If your phone number is registered, you will receive a login link on Telegram."}

    # Generate token
    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(minutes=15)
    
    login_request = LoginRequest(
        user_id=user.id,
        token=token,
        expires_at=expires_at
    )
    db.add(login_request)
    db.commit()
    
    # Send Telegram message
    # Link format: {FRONTEND_URL}/verify?token=...
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    magic_link = f"{frontend_url}/verify?token={token}"
    print(f"MAGIC LINK: {magic_link}")
    
    try:
        await telegram_service.send_message(
            chat_id=int(user.telegram_id),
            text=f"🔐 Log in to Memor.ia:\n\n{magic_link}\n\nThis link expires in 15 minutes."
        )
    except Exception as e:
        print(f"Failed to send telegram message: {e}")
        return {"error": "Failed to send login link"}
        
    return {"message": "Login link sent to Telegram"}

@app.post("/auth/verify")
def verify(payload: VerifyPayload, db: Session = Depends(get_db)):
    """
    Verify magic link token.
    """
    login_req = db.query(LoginRequest).filter(
        LoginRequest.token == payload.token,
        LoginRequest.is_used == False,
        LoginRequest.expires_at > datetime.utcnow()
    ).first()
    
    if not login_req:
        return {"error": "Invalid or expired token"}
        
    # Mark as used
    login_req.is_used = True
    db.commit()
    
    user = login_req.user
    
    return {
        "token": "session_token_placeholder", # In a real app, issue a JWT here
        "user": {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "telegram_id": user.telegram_id
        }
    }
@app.post("/webhook/batch")
async def webhook_batch(
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Batch webhook endpoint que recibe múltiples updates de Telegram agrupados.

    Este endpoint es llamado por el ARQ worker después de que expira la ventana
    de agrupación (12.5 segundos). Procesa todos los mensajes como un solo batch,
    lo cual es especialmente útil para múltiples fotos.

    Args:
        payload: Dict con 'updates' (lista de Telegram updates) y 'user_id'
        db: Database session

    Returns:
        Dict con método y respuesta de Telegram Bot API
    """
    updates = payload.get("updates", [])
    user_id = payload.get("user_id")

    if not updates:
        return {"error": "No updates provided"}

    print(f"[BATCH] Processing {len(updates)} messages for user {user_id}")

    # Procesar batch usando MessagingService
    response = await messaging_service.process_message_batch(
        updates=updates,
        db=db
    )

    print(f"[BATCH] Batch processed successfully")
    return response
