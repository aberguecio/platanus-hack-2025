"use client"

import Link from "next/link"
import { Compass, ArrowRight } from "lucide-react"
import { format } from "date-fns"

interface RelatedEvent {
    id: number
    name: string
    description?: string
    event_date?: string
    preview_image?: string
    similarity_score: number
}

interface RelatedEventsProps {
    events: RelatedEvent[]
}

export function RelatedEvents({ events }: RelatedEventsProps) {
    if (!events || events.length === 0) return null

    return (
        <section className="py-24 px-4 bg-gradient-to-b from-black to-gray-950">
            <div className="max-w-7xl mx-auto">
                {/* Section Header */}
                <div className="flex items-center gap-3 mb-12">
                    <Compass className="w-6 h-6 text-purple-400" />
                    <h2 className="text-3xl md:text-4xl font-bold text-white">
                        More Like This
                    </h2>
                </div>

                {/* Horizontal Scroll Container */}
                <div className="overflow-x-auto pb-4 -mx-4 px-4 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
                    <div className="flex gap-6 min-w-max">
                        {events.map((event) => (
                            <Link
                                key={event.id}
                                href={`/events/${event.id}`}
                                className="group relative w-80 flex-shrink-0"
                            >
                                <div className="relative h-64 rounded-2xl overflow-hidden bg-gray-900 shadow-lg group-hover:shadow-2xl transition-all duration-300">
                                    {/* Preview Image */}
                                    {event.preview_image ? (
                                        <>
                                            <img
                                                src={event.preview_image}
                                                alt={event.name}
                                                className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                                            />
                                            <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent" />
                                        </>
                                    ) : (
                                        <div className="absolute inset-0 bg-gradient-to-br from-gray-800 to-gray-900" />
                                    )}

                                    {/* Content */}
                                    <div className="absolute inset-x-0 bottom-0 p-6">
                                        <h3 className="text-xl font-bold text-white mb-2 line-clamp-2">
                                            {event.name}
                                        </h3>

                                        {event.event_date && (
                                            <p className="text-sm text-gray-300 mb-3">
                                                {format(new Date(event.event_date), "MMM d, yyyy")}
                                            </p>
                                        )}

                                        {event.description && (
                                            <p className="text-sm text-gray-400 line-clamp-2 mb-3">
                                                {event.description}
                                            </p>
                                        )}

                                        {/* Similarity Badge */}
                                        <div className="flex items-center gap-2">
                                            <span className="text-xs text-gray-500">
                                                {Math.round(event.similarity_score * 100)}% similar
                                            </span>
                                            <ArrowRight className="w-4 h-4 text-blue-400 group-hover:translate-x-1 transition-transform" />
                                        </div>
                                    </div>
                                </div>
                            </Link>
                        ))}
                    </div>
                </div>
            </div>
        </section>
    )
}
