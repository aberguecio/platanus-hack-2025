"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"

export default function CapsuleRedirect({ params }: { params: { id: string } }) {
    const router = useRouter()

    useEffect(() => {
        // Redirect to the main event page (capsule is now integrated there)
        router.replace(`/events/${params.id}`)
    }, [params.id, router])

    return (
        <div className="min-h-screen bg-black flex items-center justify-center">
            <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
                <p className="text-gray-400">Redirecting...</p>
            </div>
        </div>
    )
}
