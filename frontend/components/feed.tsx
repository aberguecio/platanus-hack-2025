"use client"

import { useEffect, useState } from "react"
import { MemoryCard } from "@/components/memory-card"

interface Memory {
    id: number
    text?: string
    s3_url?: string
    created_at: string
    user_id: number
}

export function Feed() {
    const [memories, setMemories] = useState<Memory[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        async function fetchMemories() {
            try {
                const response = await fetch("http://localhost:8000/memories")
                if (!response.ok) {
                    throw new Error("Failed to fetch memories")
                }
                const data = await response.json()
                setMemories(data)
            } catch (error) {
                console.error("Error fetching memories:", error)
            } finally {
                setLoading(false)
            }
        }

        fetchMemories()
    }, [])

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[50vh]">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
            </div>
        )
    }

    return (
        <div className="flex flex-col gap-8 pb-20">
            {memories.map((memory) => (
                <MemoryCard key={memory.id} memory={memory} />
            ))}
            {memories.length === 0 && (
                <div className="text-center text-gray-500 py-10">
                    No memories yet. Be the first to share!
                </div>
            )}
        </div>
    )
}
