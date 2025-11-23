"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Feed } from "@/components/feed"

export default function Home() {
  const router = useRouter()
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if user is logged in
    const user = localStorage.getItem("user")
    const token = localStorage.getItem("token")

    if (!user || !token) {
      // Not authenticated, redirect to login
      router.push("/login")
    } else {
      setIsAuthenticated(true)
      setLoading(false)
    }
  }, [router])

  if (loading || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
      </div>
    )
  }

  return (
    <main className="min-h-screen bg-black text-white">
      <header className="sticky top-0 z-10 bg-black/80 backdrop-blur-md border-b border-gray-800 p-4">
        <div className="max-w-md mx-auto flex justify-between items-center">
          <h1 className="text-xl font-bold tracking-tight">Collective Diary</h1>
          <div className="text-xs font-medium px-2 py-1 bg-white text-black rounded-full">
            Trip 2025
          </div>
        </div>
      </header>

      <div className="max-w-md mx-auto p-4">
        <Feed />
      </div>
    </main>
  )
}
