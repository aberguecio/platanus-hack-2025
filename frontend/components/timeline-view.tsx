"use client"

import { format } from "date-fns"
import { Calendar, Image as ImageIcon } from "lucide-react"

interface TimelineMemory {
    id: number
    text?: string
    s3_url?: string
    media_type?: string
    created_at: string
    user_id: number
}

interface TimelineItem {
    date: string
    memories: TimelineMemory[]
}

interface TimelineViewProps {
    timeline: TimelineItem[]
}

export function TimelineView({ timeline }: TimelineViewProps) {
    if (!timeline || timeline.length === 0) {
        return (
            <div className="text-center text-gray-500 py-12">
                <Calendar className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No timeline available</p>
            </div>
        )
    }

    return (
        <div className="relative">
            {/* Vertical line */}
            <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gradient-to-b from-blue-500 via-purple-500 to-pink-500 opacity-30"></div>

            <div className="space-y-12">
                {timeline.map((item, index) => (
                    <div key={item.date} className="relative pl-20">
                        {/* Date marker */}
                        <div className="absolute left-0 top-0">
                            <div className="flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg">
                                <div className="text-center text-white">
                                    <div className="text-sm font-bold">
                                        {format(new Date(item.date), "MMM")}
                                    </div>
                                    <div className="text-xl font-bold">
                                        {format(new Date(item.date), "d")}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Memories for this date */}
                        <div className="space-y-4">
                            <h3 className="text-xl font-semibold text-white mb-4">
                                {format(new Date(item.date), "EEEE, MMMM d, yyyy")}
                            </h3>

                            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                                {item.memories.map((memory) => (
                                    <div
                                        key={memory.id}
                                        className="group relative aspect-square rounded-lg overflow-hidden bg-gray-800 shadow-md hover:shadow-xl transition-all duration-300"
                                    >
                                        {memory.s3_url ? (
                                            <>
                                                <img
                                                    src={memory.s3_url}
                                                    alt={memory.text || "Memory"}
                                                    className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                                                />
                                                {memory.text && (
                                                    <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                                                        <div className="absolute bottom-0 left-0 right-0 p-3">
                                                            <p className="text-white text-xs line-clamp-2">
                                                                {memory.text}
                                                            </p>
                                                        </div>
                                                    </div>
                                                )}
                                            </>
                                        ) : (
                                            <div className="flex flex-col items-center justify-center w-full h-full p-4 text-center">
                                                <ImageIcon className="w-8 h-8 text-gray-600 mb-2" />
                                                {memory.text && (
                                                    <p className="text-gray-400 text-xs line-clamp-3">
                                                        {memory.text}
                                                    </p>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}
