"use client"

import { Card } from "@/components/ui/card"
import { Quote } from "lucide-react"

interface QuoteCardProps {
    text: string
    author?: string
    date?: string
}

export function QuoteCard({ text, author, date }: QuoteCardProps) {
    return (
        <Card className="relative p-8 bg-gradient-to-br from-gray-900 to-black text-white border-gray-800 hover:shadow-xl transition-all duration-300">
            <Quote className="absolute top-4 left-4 w-8 h-8 text-gray-700 opacity-50" />

            <div className="relative">
                <p className="text-lg md:text-xl leading-relaxed text-gray-100 italic mb-4 pl-4">
                    "{text}"
                </p>

                {(author || date) && (
                    <div className="flex items-center justify-between text-sm text-gray-400 pl-4 pt-2 border-t border-gray-800">
                        {author && (
                            <span className="font-medium">— {author}</span>
                        )}
                        {date && (
                            <span className="text-xs">{new Date(date).toLocaleDateString()}</span>
                        )}
                    </div>
                )}
            </div>
        </Card>
    )
}
