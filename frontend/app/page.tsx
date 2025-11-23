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
      <section className="max-w-7xl mx-auto px-4 py-16 text-center">
        <h2 className="text-5xl md:text-6xl font-bold mb-6">
          Memor.ia
        </h2>
        <p className="text-2xl md:text-3xl text-gray-300 mb-12 max-w-3xl mx-auto">
          Transformamos recuerdos dispersos en historias que vuelven a emocionar. <span className="text-4xl leading-none">✨</span>
        </p>

        {/* Search Bar */}
        <div className="mb-16">
          <SearchBar onSearch={handleSearch} />
        </div>
      </section>

      {/* Feed */}
      <div className="max-w-7xl mx-auto px-4 md:px-6 lg:px-8 pb-20">
        <Feed searchQuery={searchQuery} />
      </div>
    </main>
  )
}
