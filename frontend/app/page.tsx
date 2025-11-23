"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Feed } from "@/components/feed"
import { SearchBar } from "@/components/search-bar"
import { Camera, Plus } from "lucide-react"

export default function Home() {
  const router = useRouter()
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")

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

  const handleSearch = (query: string) => {
    setSearchQuery(query)
  }

  if (loading || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
      </div>
    )
  }

  return (
    <main className="min-h-screen bg-black text-white">
      {/* Header with Logo and Add Memory Button */}
      {/* <header className="sticky top-0 z-10 bg-black/80 backdrop-blur-md border-b border-gray-800 p-4">
        <div className="max-w-md mx-auto flex justify-between items-center">
          <h1 className="text-xl font-bold tracking-tight">Events</h1>
          <div className="text-xs font-medium px-2 py-1 bg-white text-black rounded-full">
            Trip 2025
          </div>
        </div>
      </header> */}

      {/* Hero Section */}
      <section className="relative min-h-[85vh] flex flex-col items-center justify-center px-4 py-8 md:py-12">
        {/* Gradient background overlay */}
        <div className="absolute inset-0 bg-gradient-to-b from-black via-gray-900/50 to-black pointer-events-none" />

        {/* Content */}
        <div className="relative z-10 max-w-5xl mx-auto text-center space-y-6 md:space-y-8">
          {/* Logo with glow effect */}
          <div className="flex justify-center mb-4 md:mb-6">
            <div className="relative group">
              <div className="absolute -inset-4 bg-gradient-to-r from-yellow-400/20 via-amber-500/20 to-yellow-600/20 rounded-full blur-2xl opacity-75 group-hover:opacity-100 transition-opacity duration-500" />
              <img
                src="cropped_circle_image.png"
                alt="Memor.IA Logo"
                className="relative w-32 h-32 md:w-40 md:h-40 lg:w-48 lg:h-48 transition-transform duration-500 hover:scale-105"
              />
            </div>
          </div>

          {/* Heading & Subtitle */}
          <div className="space-y-4 md:space-y-6">
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight">
              <span className="bg-gradient-to-r from-white via-gray-100 to-gray-200 bg-clip-text text-transparent">
                Memor.IA
              </span>
            </h1>

            <p className="text-lg md:text-xl lg:text-2xl text-gray-100 font-light leading-relaxed max-w-3xl mx-auto px-4">
              Transformamos recuerdos dispersos en historias que vuelven a emocionar.
              <span className="inline-block ml-2 text-3xl animate-pulse">✨</span>
            </p>
          </div>

          {/* Search Bar */}
          <div className="pt-4 md:pt-8 max-w-2xl mx-auto w-full">
            <SearchBar onSearch={handleSearch} />
          </div>
        </div>
      </section>

      {/* Feed */}
      <div className="max-w-7xl mx-auto px-4 md:px-6 lg:px-8 pb-20">
        <Feed searchQuery={searchQuery} />
      </div>
    </main>
  )
}
