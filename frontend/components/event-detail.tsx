"use client"

import { EventWithMemories } from "@/lib/types"
import { MemoryCard } from "@/components/memory-card"
import { formatDistanceToNow, format } from "date-fns"
import { Calendar, ArrowLeft, Sparkles } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"

interface EventDetailProps {
    event: EventWithMemories
}

export function EventDetail({ event }: EventDetailProps) {
    return (
        <div className="min-h-screen bg-black text-white">
            {/* Header */}
            <header className="sticky top-0 z-10 bg-black/90 backdrop-blur-md border-b border-gray-800">
                <div className="max-w-md mx-auto p-4">
                    <Link
                        href="/"
                        className="inline-flex items-center gap-2 text-gray-400 hover:text-white transition-colors mb-3"
                    >
                        <ArrowLeft className="w-4 h-4" />
                        <span className="text-sm font-medium">Back to Events</span>
                    </Link>

                    <div>
                        <h1 className="text-2xl font-bold tracking-tight mb-2">
                            {event.name}
                        </h1>

                        {event.description && (
                            <p className="text-gray-400 text-sm mb-3">
                                {event.description}
                            </p>
                        )}

                        <div className="flex items-center gap-4 text-xs text-gray-500">
                            {event.event_date && (
                                <div className="flex items-center gap-1.5">
                                    <Calendar className="w-3.5 h-3.5" />
                                    <span>{format(new Date(event.event_date), "MMMM d, yyyy")}</span>
                                </div>
                            )}
                            <div>
                                {event.memories.length} {event.memories.length === 1 ? 'memory' : 'memories'}
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            {/* Memories Grid */}
            <div className="max-w-md mx-auto p-4">
                {/* Event Capsule Button */}
                <Link href={`/events/${event.id}/capsule`}>
                    <Button className="w-full mb-6 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 hover:from-blue-600 hover:via-purple-600 hover:to-pink-600 text-white font-semibold py-6 rounded-xl shadow-lg hover:shadow-xl transition-all">
                        <Sparkles className="w-5 h-5 mr-2" />
                        View Event Capsule
                    </Button>
                </Link>

                {event.summary && (
                    <div className="mb-6 p-4 bg-gradient-to-br from-gray-900 to-gray-800 rounded-xl border border-gray-700">
                        <h2 className="text-sm font-semibold text-gray-400 mb-2">Event Summary</h2>
                        <p className="text-sm text-gray-300">{event.summary}</p>
                    </div>
                )}

                <div className="flex flex-col gap-8 pb-20">
                    {event.memories.length > 0 ? (
                        event.memories.map((memory) => (
                            <MemoryCard key={memory.id} memory={memory} />
                        ))
                    ) : (
                        <div className="text-center text-gray-500 py-20">
                            <p className="text-lg mb-2">No memories yet</p>
                            <p className="text-sm">Share moments via Telegram to get started</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
