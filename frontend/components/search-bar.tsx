"use client"

import { Search } from "lucide-react"
import { useState, useEffect } from "react"

interface SearchBarProps {
    onSearch: (query: string) => void
    placeholder?: string
}

const motivationalPhrases = [
    "Busca recuerdos por ubicación o tiempo...",
    "Recuerda esa increíble puesta de sol en la playa...",
    "Encuentra recuerdos del verano pasado...",
    "Revive tus momentos favoritos...",
    "Descubre recuerdos de París...",
    "Busca ese concierto que amaste...",
    "Encuentra recuerdos con amigos...",
    "Recuerda ese cumpleaños especial...",
    "Explora recuerdos del 2023...",
    "Busca momentos que te hicieron sonreír..."
]

export function SearchBar({ onSearch, placeholder }: SearchBarProps) {
    const [query, setQuery] = useState("")
    const [currentPlaceholder, setCurrentPlaceholder] = useState(placeholder || motivationalPhrases[0])
    const [placeholderIndex, setPlaceholderIndex] = useState(0)
    const [isTransitioning, setIsTransitioning] = useState(false)

    // Rotate placeholder every 3 seconds
    useEffect(() => {
        if (placeholder) return // Don't rotate if custom placeholder is provided

        const interval = setInterval(() => {
            setIsTransitioning(true)
            setTimeout(() => {
                setPlaceholderIndex((prev) => (prev + 1) % motivationalPhrases.length)
                setCurrentPlaceholder(motivationalPhrases[(placeholderIndex + 1) % motivationalPhrases.length])
                setIsTransitioning(false)
            }, 300) // Half of transition duration
        }, 3000)

        return () => clearInterval(interval)
    }, [placeholder, placeholderIndex])

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        if (query.trim()) {
            onSearch(query)
        }
    }

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value
        setQuery(value)

        // Optional: Real-time search as user types (debounced)
        if (value.trim() === "") {
            onSearch("") // Clear search when input is empty
        }
    }

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === "Enter") {
            handleSubmit(e)
        }
    }

    return null; // TODO: Remove this

    return (
        <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto">
            <div className="relative group">
                {/* Constant gold glow effect */}
                <div className="absolute -inset-0.5 bg-gradient-to-r from-yellow-400 via-amber-500 to-yellow-600 rounded-xl opacity-25 group-hover:opacity-35 group-focus-within:opacity-40 blur transition-opacity duration-300"></div>
                
                <div className="relative bg-gray-900/80 backdrop-blur-sm border border-gray-700/50 rounded-xl shadow-lg">
                    <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                        <Search className="h-5 w-5 text-yellow-400/70 group-focus-within:text-yellow-400 transition-colors duration-200" />
                    </div>
                    <input
                        type="text"
                        value={query}
                        onChange={handleChange}
                        onKeyDown={handleKeyDown}
                        placeholder={currentPlaceholder}
                        className={`w-full bg-transparent text-white placeholder-gray-400 rounded-xl pl-12 pr-4 py-4 focus:outline-none focus:ring-2 focus:ring-yellow-500/50 transition-all duration-300 border-2 border-yellow-400/40 focus:border-yellow-400 shadow-[0_0_12px_2px_rgba(234,179,8,0.4)] focus:shadow-[0_0_12px_2px_rgba(234,179,8,0.6)] ${
                            isTransitioning ? 'opacity-50' : 'opacity-100'
                        }`}
                        style={{
                            transition: 'opacity 0.3s ease-in-out'
                        }}
                    />
                </div>
            </div>
        </form>
    )
}
