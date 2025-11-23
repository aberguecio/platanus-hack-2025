// Shared TypeScript interfaces for the application

export interface Memory {
    id: number
    event_id: number
    user_id: number
    message_id?: number
    text?: string
    s3_url?: string
    media_type?: string
    memory_metadata?: Record<string, any>
    created_at: string
}

export interface Event {
    id: number
    name: string
    description?: string
    event_date?: string
    summary?: string
    ai_context?: string
    created_at: string
}

export interface EventWithMemories extends Event {
    memories: Memory[]
}
