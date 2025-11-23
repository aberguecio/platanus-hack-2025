"use client"

import { ChevronDown } from "lucide-react"
import { format } from "date-fns"

interface EventHeroProps {
    eventName: string
    eventDate?: string
    heroImage?: string
}

export function EventHero({ eventName, eventDate, heroImage }: EventHeroProps) {
    return (
        <section className="relative h-screen flex items-center justify-center overflow-hidden">
            {/* Background Image with Parallax */}
            {heroImage && (
                <div
                    className="absolute inset-0 bg-cover bg-center bg-fixed"
                    style={{
                        backgroundImage: `url(${heroImage})`,
                        transform: 'translateZ(0)' // Hardware acceleration
                    }}
                />
            )}

            {/* Dark Gradient Overlay */}
            <div className="absolute inset-0 bg-gradient-to-b from-black/40 via-black/50 to-black/90" />

            {/* Content */}
            <div className="relative z-10 text-center px-4 max-w-6xl mx-auto">
                <h1 className="text-6xl md:text-8xl lg:text-9xl font-bold mb-6 bg-gradient-to-r from-white via-gray-100 to-gray-300 bg-clip-text text-transparent leading-tight">
                    {eventName}
                </h1>

                {eventDate && (
                    <div className="inline-flex items-center gap-2 px-6 py-3 bg-white/10 backdrop-blur-md rounded-full border border-white/20 text-white text-lg">
                        {format(new Date(eventDate), "MMMM d, yyyy")}
                    </div>
                )}
            </div>

            {/* Scroll Indicator */}
            <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
                <ChevronDown className="w-8 h-8 text-white/60" />
            </div>
        </section>
    )
}
