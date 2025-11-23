# MemoryBot - Bot de Memorias Conversacional

## Descripción del Proyecto

MemoryBot es un bot de Telegram inteligente que revoluciona la forma en que guardamos y organizamos nuestros recuerdos. A través de conversación natural con un agente AI, los usuarios pueden almacenar fotos y textos organizados en eventos, sin necesidad de interfaces complejas o comandos específicos.

## Características Principales

### Conversación Natural con IA
- **Agente AI con Claude**: El bot utiliza Anthropic Claude como cerebro, permitiendo interacciones naturales sin comandos rígidos
- **Tool Calling Inteligente**: El agente decide automáticamente qué acciones ejecutar basándose en el contexto de la conversación
- **Contexto Dinámico**: Cada interacción considera el historial del usuario y el estado actual

### Organización de Memorias en Eventos
- **Creación de Eventos**: Crea eventos para organizar recuerdos (viajes, fiestas, proyectos, etc.)
- **Memorias Multimedia**: Almacena tanto texto como imágenes
- **Compartir Eventos**: Invita a otros usuarios a eventos colaborativos
- **Gestión Intuitiva**: Lista y consulta tus eventos y memorias fácilmente

### Búsqueda Semántica Avanzada
- **Embeddings con Voyage AI**: Cada memoria se convierte en un vector de 1024 dimensiones
- **Búsqueda por Significado**: Encuentra memorias por concepto, no solo por palabras exactas
- **PostgreSQL con pgvector**: Base de datos optimizada con índices HNSW para búsquedas rápidas

### Análisis Inteligente de Imágenes
- **Visión por Computadora**: Claude Haiku describe automáticamente el contenido de las fotos
- **Almacenamiento en S3**: Las imágenes se guardan de forma segura y eficiente
- **URLs Presignadas**: Acceso temporal y seguro a las imágenes

## Stack Tecnológico

### Backend
- **FastAPI**: Framework web moderno y de alto rendimiento
- **PostgreSQL + pgvector**: Base de datos relacional con soporte para vectores
- **Anthropic Claude**: Modelo de lenguaje avanzado para el agente AI
- **Voyage AI**: Generación de embeddings de alta calidad

### Bot
- **python-telegram-bot**: Integración robusta con Telegram
- **Modo Polling**: Simplicidad y confiabilidad en el procesamiento de mensajes

### Storage & Vision
- **AWS S3**: Almacenamiento escalable para imágenes
- **Claude Vision**: Análisis y descripción automática de imágenes

### Infrastructure
- **Docker & Docker Compose**: Containerización y orquestación
- **Traefik**: Reverse proxy con SSL automático
- **Alembic**: Migraciones de base de datos controladas

## Arquitectura Destacable

### Sistema de Agente AI
El proyecto implementa un sistema de agente AI modular con:
- **Tool Registry Pattern**: Registro dinámico de herramientas disponibles
- **Execution Context**: Inyección de dependencias para cada tool
- **Async Tool Execution**: Ejecución eficiente de múltiples tools
- **Loop de Reasoning**: El agente puede usar múltiples tools en secuencia para tareas complejas

### Sin Endpoints REST Tradicionales
Todo el sistema funciona mediante conversación natural. No hay endpoints CRUD tradicionales; el agente AI orquesta todas las operaciones a través de tool calling.

## Casos de Uso

1. **Viajes**: Guarda fotos y notas de tus viajes, comparte el evento con compañeros de viaje
2. **Eventos Familiares**: Crea un espacio colaborativo para reuniones familiares donde todos pueden subir fotos
3. **Proyectos**: Documenta el progreso de proyectos con imágenes y notas contextuales
4. **Diario Personal**: Mantén un diario multimedia organizado por temas/eventos
5. **Búsqueda Semántica**: Encuentra ese "atardecer en la playa" aunque no recuerdes cuándo lo subiste

## Innovación Técnica

- **Agente AI Conversacional**: Interfaz completamente natural sin comandos predefinidos
- **Búsqueda Semántica Real**: No solo keywords, sino búsqueda por significado usando embeddings
- **Visión por Computadora Integrada**: Descripción automática de imágenes para mejor searchability
- **Arquitectura Modular**: Sistema de tools extensible y mantenible

## Demo

Puedes probar el bot en Telegram buscando [@MemoryBot] o visitando nuestra interfaz web en [https://ph.berguecio.cl](https://ph.berguecio.cl)

## Equipo

Desarrollado durante el Platanus Hack 2025 por un equipo apasionado por la IA y las experiencias de usuario intuitivas.

---

**Tech Stack**: FastAPI, PostgreSQL, pgvector, Anthropic Claude, Voyage AI, python-telegram-bot, AWS S3, Docker, Traefik
