"use client"

import { Sparkles } from "lucide-react"

interface EventNarrativeProps {
    narrative: string
    description?: string
}

export function EventNarrative({ narrative, description }: EventNarrativeProps) {
    if (!narrative && !description) return null

    return (
        <section className="py-24 px-4">
            <div className="max-w-3xl mx-auto">
                {/* Section Header */}
                <div className="flex items-center gap-3 mb-12">
                    <Sparkles className="w-6 h-6 text-blue-400" />
                    <h2 className="text-3xl md:text-4xl font-bold text-white">
                        The Story
                    </h2>
                </div>

                {/* Narrative Content */}
                <article className="prose prose-lg prose-invert max-w-none">
                    {/* Description (if provided) */}
                    {description && (
                        <p className="text-xl text-gray-300 leading-relaxed mb-8 font-light italic border-l-4 border-blue-500 pl-6">
                            {description}
                        </p>
                    )}

                    {/* AI-Generated Narrative */}
                    {narrative && (
                        <div className="space-y-6 text-gray-200 leading-relaxed" style={{ fontFamily: 'Georgia, serif' }}>
                            {narrative.split('\n\n').map((paragraph, index) => (
                                <p
                                    key={index}
                                    className={`text-lg ${index === 0 ? 'first-letter:text-7xl first-letter:font-bold first-letter:text-blue-400 first-letter:mr-2 first-letter:float-left' : ''}`}
                                >
                                    {paragraph}
                                </p>
                            ))}
                        </div>
                    )}
                </article>
            </div>
        </section>
    )
}
