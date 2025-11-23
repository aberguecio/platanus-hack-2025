"use client"

import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { EventWithMemories } from "@/lib/types"
import { format } from "date-fns"
import { Calendar, Image as ImageIcon } from "lucide-react"
import Link from "next/link"

interface EventCardProps {
    event: EventWithMemories
}

export function EventCard({ event }: EventCardProps) {
    const memoryCount = event.memories.length
    // Get the first image memory as hero
    const heroMemory = event.memories.find(m => m.s3_url)
    // Show remaining memories
    const displayMemories = event.memories.filter(m => m.s3_url).slice(1, 5)

    return (
        <Link href={`/events/${event.id}`}>
            <Card className="w-full overflow-hidden border-0 shadow-xl bg-gradient-to-br from-gray-900 to-black text-white rounded-2xl hover:shadow-2xl hover:scale-[1.02] transition-all duration-300 cursor-pointer group">
                {/* Hero Image Banner */}
                {heroMemory?.s3_url ? (
                    <div className="relative h-96 overflow-hidden">
                        <img
                            src={heroMemory.s3_url}
                            alt={event.name}
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                        />
                        {/* Gradient Overlay */}
                        <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent" />

                        {/* Event Title on Hero */}
                        <div className="absolute bottom-0 left-0 right-0 p-8">
                            <h3 className="text-4xl font-bold tracking-tight mb-3 group-hover:text-blue-400 transition-colors drop-shadow-lg">
                                {event.name}
                            </h3>
                            {event.description && (
                                <p className="text-base text-gray-200 line-clamp-2 mb-4 drop-shadow-md max-w-3xl">
                                    {event.description}
                                </p>
                            )}
                        </div>
                    </div>
                ) : (
                    // Fallback if no hero image
                    <div className="relative h-96 bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center">
                        <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent" />
                        <div className="absolute bottom-0 left-0 right-0 p-8">
                            <h3 className="text-4xl font-bold tracking-tight mb-3 group-hover:text-blue-400 transition-colors">
                                {event.name}
                            </h3>
                            {event.description && (
                                <p className="text-base text-gray-200 line-clamp-2 mb-4 max-w-3xl">
                                    {event.description}
                                </p>
                            )}
                        </div>
                    </div>
                )}

                <CardContent className="p-8">
                    {/* Stats */}
                    <div className="flex items-center gap-6 text-sm text-gray-400 mb-6">
                        {event.event_date && (
                            <div className="flex items-center gap-2">
                                <Calendar className="w-4 h-4" />
                                <span>{format(new Date(event.event_date), "MMM d, yyyy")}</span>
                            </div>
                        )}
                        <div className="flex items-center gap-2">
                            <ImageIcon className="w-4 h-4" />
                            <span>{memoryCount} {memoryCount === 1 ? 'memory' : 'memories'}</span>
                        </div>
                    </div>

                    {/* Additional Memory Thumbnails */}
                    {displayMemories.length > 0 && (
                        <div className="grid grid-cols-4 gap-3">
                            {displayMemories.map((memory) => (
                                <div
                                    key={memory.id}
                                    className="relative aspect-square rounded-lg overflow-hidden bg-gray-800 shadow-md"
                                >
                                    <img
                                        src={memory.s3_url}
                                        alt="Memory preview"
                                        className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                                    />
                                </div>
                            ))}
                        </div>
                    )}

                    {memoryCount === 0 && (
                        <div className="text-center text-gray-500 py-8 text-sm">
                            No memories yet
                        </div>
                    )}
                </CardContent>
            </Card>
        </Link>
    )
}
