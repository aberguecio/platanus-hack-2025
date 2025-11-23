"use client"

import { useEffect, useState } from "react"
import { EventCard } from "@/components/event-card"
import { EventWithMemories } from "@/lib/types"

export function Feed() {
    const [events, setEvents] = useState<EventWithMemories[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        async function fetchEvents() {
            try {
                const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
                const response = await fetch(`${API_URL}/events`)
                if (!response.ok) {
                    throw new Error("Failed to fetch events")
                }
                const data = await response.json()
                setEvents(data)
            } catch (error) {
                console.error("Error fetching events:", error)
            } finally {
                setLoading(false)
            }
        }

        fetchEvents()
    }, [])

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[50vh]">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
            </div>
        )
    }

    return (
        <div className="flex flex-col gap-8">
            {events.map((event) => (
                <EventCard key={event.id} event={event} />
            ))}
            {events.length === 0 && (
                <div className="text-center text-gray-500 py-20">
                    <p className="text-lg mb-2">No events yet</p>
                    <p className="text-sm">Create your first event via Telegram to get started</p>
                </div>
            )}
        </div>
    )
}
