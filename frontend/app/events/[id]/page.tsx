"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft, Image as ImageIcon, Clock, Quote as QuoteIcon, BarChart3 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { EventHero } from "@/components/event-hero"
import { ArticleNarrative } from "@/components/article-narrative"
import { GalleryCarousel } from "@/components/gallery-carousel"
import { TimelineView } from "@/components/timeline-view"
import { QuoteCard } from "@/components/quote-card"
import { StatsDashboard } from "@/components/stats-dashboard"
import { RelatedEvents } from "@/components/related-events"
import { AftermovieSection } from "@/components/aftermovie-section"

interface EventData {
    event: any
    heroImage: any
    narrative: any
    bestPhotos: any[]
    timeline: any[]
    quotes: any[]
    stats: any
    relatedEvents: any[]
}

export default function EventPage({ params }: { params: { id: string } }) {
    const router = useRouter()
    const [data, setData] = useState<EventData | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [generatedVideoUrl, setGeneratedVideoUrl] = useState<string | undefined>(undefined)

    useEffect(() => {
        if (data?.event?.memories) {
            const videoMemory = data.event.memories.find((m: any) =>
                m?.media_type === 'video' &&
                (m?.text?.includes("Video resumen") || m?.text?.includes("generated automatically"))
            )
            if (videoMemory) {
                setGeneratedVideoUrl(videoMemory.s3_url)
            }
        }
    }, [data])

    useEffect(() => {
        async function fetchEventData() {
            try {
                setLoading(true)
                const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

                // Fetch all data in parallel
                const [eventRes, heroRes, photosRes, timelineRes, quotesRes, statsRes, relatedRes] = await Promise.all([
                    fetch(`${API_URL}/events/${params.id}`),
                    fetch(`${API_URL}/events/${params.id}/hero-image`),
                    fetch(`${API_URL}/events/${params.id}/best-photos?limit=12`),
                    fetch(`${API_URL}/events/${params.id}/timeline`),
                    fetch(`${API_URL}/events/${params.id}/best-quotes?limit=6`),
                    fetch(`${API_URL}/events/${params.id}/stats`),
                    fetch(`${API_URL}/events/${params.id}/related-events?limit=5`)
                ])

                if (!eventRes.ok) throw new Error("Failed to fetch event")

                // Log photos response status before parsing
                console.log("[EventPage] Photos response status:", photosRes.status, photosRes.statusText)
                console.log("[EventPage] Photos response ok:", photosRes.ok)

                const [event, heroImage, bestPhotos, timeline, quotes, stats, relatedEvents] = await Promise.all([
                    eventRes.json(),
                    heroRes.json(),
                    photosRes.json(),
                    timelineRes.json(),
                    quotesRes.json(),
                    statsRes.json(),
                    relatedRes.json()
                ])

                // Check if event has cached narrative, otherwise generate it
                let narrative = event.generated_narrative || null
                // let narrative = null
                if (!narrative) {
                    console.log("[EventPage] No cached narrative, generating new one...")
                    const narrativeRes = await fetch(`${API_URL}/events/${params.id}/generate-narrative-v2`, { method: 'POST' })
                    const narrativeData = await narrativeRes.json()
                    narrative = narrativeData.narrative
                } else {
                    console.log("[EventPage] Using cached narrative from database")
                }

                // Check for aftermovie video in memories and trigger generation if missing
                const hasVideo = event.memories?.some((m: any) =>
                    m?.media_type === 'video' &&
                    (m?.text?.includes("Video resumen") || m?.text?.includes("generated automatically"))
                )

                if (!hasVideo) {
                    console.log("[EventPage] No aftermovie found, triggering background generation...")
                    // Fire and forget - don't await this to avoid blocking page load
                    fetch(`${API_URL}/events/${params.id}/generate-video`, { method: 'POST' })
                        .then(res => res.json())
                        .then(data => {
                            console.log("[EventPage] Video generation completed:", data)
                            if (data.video_url) {
                                // Update state to show video immediately without refresh
                                console.log("Video generated at:", data.video_url)
                                setGeneratedVideoUrl(data.video_url)
                            }
                        })
                        .catch(err => console.error("[EventPage] Video generation failed:", err))
                } else {
                    console.log("[EventPage] Aftermovie already exists")
                }

                // Handle error responses and ensure arrays
                console.log("[EventPage] Raw bestPhotos before processing:", bestPhotos)
                console.log("[EventPage] bestPhotos type:", typeof bestPhotos)
                console.log("[EventPage] bestPhotos isArray:", Array.isArray(bestPhotos))
                console.log("[EventPage] bestPhotos has error:", bestPhotos && typeof bestPhotos === 'object' && 'error' in bestPhotos)

                const safeBestPhotos = Array.isArray(bestPhotos) && !('error' in bestPhotos) ? bestPhotos : []
                const safeHeroImage = heroImage && typeof heroImage === 'object' && !('error' in heroImage) ? heroImage : null

                // If bestPhotos is empty but we have images in event memories, try to extract them
                let finalBestPhotos = safeBestPhotos
                if (safeBestPhotos.length === 0 && event?.memories) {
                    console.log("[EventPage] bestPhotos is empty, checking event.memories for images")
                    const imageMemories = event.memories.filter((m: any) =>
                        m?.media_type === 'image' &&
                        m?.s3_url &&
                        (m.s3_url.startsWith('http://') || m.s3_url.startsWith('https://'))
                    )
                    console.log("[EventPage] Found", imageMemories.length, "images in event.memories")
                    if (imageMemories.length > 0) {
                        // Use images from event memories as fallback
                        finalBestPhotos = imageMemories.slice(0, 5).map((m: any) => ({
                            id: m.id,
                            s3_url: m.s3_url,
                            text: m.text,
                            created_at: m.created_at,
                            user_id: m.user_id,
                            relevance_score: 0.0
                        }))
                        console.log("[EventPage] Using fallback photos from event.memories:", finalBestPhotos)
                    }
                }

                // Debug logging - Photos information
                console.log("[EventPage] ========== PHOTOS DEBUG INFO ==========")
                console.log("[EventPage] Raw bestPhotos response:", bestPhotos)
                console.log("[EventPage] Safe bestPhotos (filtered):", safeBestPhotos)
                console.log("[EventPage] Final bestPhotos (with fallback):", finalBestPhotos)
                console.log("[EventPage] Best photos count:", finalBestPhotos.length)
                console.log("[EventPage] Best photos details:", finalBestPhotos.map((p: any, i: number) => ({
                    index: i,
                    id: p?.id,
                    s3_url: p?.s3_url,
                    url_length: p?.s3_url?.length || 0,
                    url_starts_with_http: p?.s3_url?.startsWith('http://') || p?.s3_url?.startsWith('https://'),
                    has_text: !!p?.text,
                    text_preview: p?.text?.substring(0, 50) || null,
                    media_type: p?.media_type,
                    created_at: p?.created_at,
                    relevance_score: p?.relevance_score
                })))
                console.log("[EventPage] Photos to pass to ArticleNarrative (first 5):", finalBestPhotos.slice(0, 5))
                console.log("[EventPage] Hero image response:", safeHeroImage)
                console.log("[EventPage] Hero image URL:", safeHeroImage?.s3_url)
                console.log("[EventPage] Event memories count:", event?.memories?.length || 0)
                console.log("[EventPage] Event memories with images:", event?.memories?.filter((m: any) => m?.media_type === 'image')?.length || 0)
                console.log("[EventPage] =========================================")

                setData({
                    event,
                    heroImage: safeHeroImage,
                    narrative: narrative || event.summary,
                    bestPhotos: finalBestPhotos,
                    timeline: Array.isArray(timeline) ? timeline : [],
                    quotes: Array.isArray(quotes) ? quotes : [],
                    stats,
                    relatedEvents: Array.isArray(relatedEvents) ? relatedEvents : []
                })
            } catch (err) {
                console.error("Error fetching event data:", err)
                setError(err instanceof Error ? err.message : "Failed to load event")
            } finally {
                setLoading(false)
            }
        }

        fetchEventData()
    }, [params.id])

    if (loading) {
        return (
            <div className="min-h-screen bg-black flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-white mx-auto mb-6"></div>
                    <p className="text-gray-400 text-lg">Crafting your event story...</p>
                </div>
            </div>
        )
    }

    if (error || !data) {
        return (
            <div className="min-h-screen bg-black flex items-center justify-center">
                <div className="text-white">
                    <p className="text-red-500 mb-6 text-xl">{error || "Failed to load event"}</p>
                    <Button onClick={() => router.push("/")} size="lg">
                        <ArrowLeft className="w-4 h-4 mr-2" />
                        Back to Events
                    </Button>
                </div>
            </div>
        )
    }

    const { event, heroImage, narrative, bestPhotos, timeline, quotes, stats, relatedEvents } = data

    // Use hero image if available, otherwise fallback to first best photo, or first memory image
    let displayHeroImage = heroImage?.s3_url || null

    if (!displayHeroImage && bestPhotos.length > 0) {
        // Find first photo with valid s3_url
        const validPhoto = bestPhotos.find((p: any) => p?.s3_url && typeof p.s3_url === 'string')
        displayHeroImage = validPhoto?.s3_url || null
    }

    // Final fallback: check event memories directly
    if (!displayHeroImage && event?.memories) {
        const memoryWithImage = event.memories.find((m: any) =>
            m?.media_type === 'image' && m?.s3_url && typeof m.s3_url === 'string'
        )
        displayHeroImage = memoryWithImage?.s3_url || null
    }

    console.log("Display hero image:", displayHeroImage)



    // Find aftermovie video (initial check)
    let aftermovieUrl = generatedVideoUrl
    if (!aftermovieUrl && event?.memories) {
        // Look for the auto-generated video memory
        const videoMemory = event.memories.find((m: any) =>
            m?.media_type === 'video' &&
            (m?.text?.includes("Video resumen") || m?.text?.includes("generated automatically"))
        )

        if (videoMemory) {
            aftermovieUrl = videoMemory.s3_url
        }
    }

    return (
        <main className="min-h-screen bg-black text-white">
            {/* Fixed Back Button */}
            <div className="fixed top-6 left-6 z-50">
                <Button
                    onClick={() => router.push("/")}
                    variant="ghost"
                    className="bg-black/50 backdrop-blur-md border border-white/20 text-white hover:bg-white hover:text-black hover:border-black transition-all duration-200"
                >
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Back
                </Button>
            </div>

            {/* Hero Section */}
            <EventHero
                eventName={event.name}
                eventDate={event.event_date}
                heroImage={displayHeroImage}
            />

            {/* Article Narrative Section - The Key Differentiator */}
            <ArticleNarrative
                narrative={narrative}
                eventName={event.name}
                eventDate={event.event_date}
                participantCount={stats?.unique_contributors || event.memories?.length || 0}
                photos={bestPhotos.slice(0, 5)}
                quotes={quotes.slice(0, 2).map((q: any) => ({
                    text: q.text,
                    author: q.first_name || "A participant"
                }))}
            />

            {/* Featured Collaborator Quote */}
            <section className="py-16 px-4 bg-gradient-to-b from-black to-gray-950">
                <div className="max-w-4xl md:max-w-5xl lg:max-w-6xl xl:max-w-7xl mx-auto">
                    <div className="relative">
                        <div className="absolute -left-4 top-0 text-8xl text-blue-400/20 font-serif">"</div>
                        <div className="absolute -right-4 top-0 text-8xl text-blue-400/20 font-serif rotate-180">"</div>
                        <div className="pl-8 md:pl-16 pr-8 md:pr-16">
                            <blockquote className="text-2xl md:text-3xl lg:text-4xl font-light text-gray-200 italic mb-8 leading-relaxed">
                                {quotes[0]?.text || "Una experiencia inolvidable que nos unió como equipo y nos recordó por qué hacemos lo que hacemos."}
                            </blockquote>
                            <div className="flex items-center gap-4">
                                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                                    <span className="text-white font-bold text-lg">
                                        {quotes[0]?.first_name?.charAt(0) || "M"}
                                    </span>
                                </div>
                                <div>
                                    <p className="text-gray-300 font-medium">
                                        {quotes[0]?.first_name || "María López"}
                                    </p>
                                    <p className="text-sm text-gray-500">
                                        Participante del evento
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Aftermovie Section */}
            <AftermovieSection
                eventName={event.name}
                videoUrl={aftermovieUrl}
            />


            {/* Featured Moments Gallery */}
            {/* {bestPhotos.length > 0 && (
                <section className="py-24 px-4 bg-gradient-to-b from-black to-gray-950">
                    <div className="max-w-7xl mx-auto">
                        <div className="flex items-center gap-3 mb-12">
                            <ImageIcon className="w-6 h-6 text-blue-400" />
                            <h2 className="text-3xl md:text-4xl font-bold text-white">
                                Featured Moments
                            </h2>
                        </div>
                        <GalleryCarousel photos={bestPhotos} />
                    </div>
                </section>
            )} */}

            {/* Timeline */}
            {timeline.length > 0 && (
                <section className="py-24 px-4">
                    <div className="max-w-7xl mx-auto">
                        <div className="flex items-center justify-between mb-12">
                            <div className="flex items-center gap-3">
                                <Clock className="w-6 h-6 text-purple-400" />
                                <h2 className="text-3xl md:text-4xl font-bold text-white">
                                    Timeline
                                </h2>
                            </div>
                            <Button
                                onClick={() => {
                                    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
                                    window.open(`${API_URL}/events/${params.id}/download-images`, '_blank')
                                }}
                                variant="outline"
                                className="border-gray-800 bg-gray-900/50 text-white hover:bg-white hover:text-black hover:border-black transition-all duration-200"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-2">
                                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                                    <polyline points="7 10 12 15 17 10"></polyline>
                                    <line x1="12" y1="15" x2="12" y2="3"></line>
                                </svg>
                                Descargar Imágenes
                            </Button>
                        </div>
                        <TimelineView timeline={timeline} />
                    </div>
                </section>
            )}

            {/* Related Events */}
            <RelatedEvents events={relatedEvents} />

            {/* Memorable Quotes */}
            {quotes.length > 0 && (
                <section className="py-24 px-4">
                    <div className="max-w-7xl mx-auto">
                        <div className="flex items-center gap-3 mb-12">
                            <QuoteIcon className="w-6 h-6 text-pink-400" />
                            <h2 className="text-3xl md:text-4xl font-bold text-white">
                                Memorable Quotes
                            </h2>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {quotes.map((quote: any) => (
                                <QuoteCard
                                    key={quote.id}
                                    text={quote.text}
                                    author={`${quote.first_name || "Anonymous"}`}
                                    date={quote.created_at}
                                />
                            ))}
                        </div>
                    </div>
                </section>
            )}

            {/* Event Insights */}
            {stats && stats.total_memories > 0 && (
                <section className="py-24 px-4 bg-gradient-to-b from-black to-gray-950">
                    <div className="max-w-7xl mx-auto">
                        <div className="flex items-center gap-3 mb-12">
                            <BarChart3 className="w-6 h-6 text-indigo-400" />
                            <h2 className="text-3xl md:text-4xl font-bold text-white">
                                Event Insights
                            </h2>
                        </div>
                        <StatsDashboard stats={stats} />
                    </div>
                </section>
            )}

            {/* Footer */}
            <footer className="border-t border-gray-800 py-12 px-4 text-center text-gray-500">
                <p className="mb-4">Created with Memor.ia</p>
                <div className="flex justify-center">
                    <Button
                        onClick={() => router.push("/")}
                        variant="outline"
                        className="border-gray-800 bg-gray-900/50 text-white hover:bg-white hover:text-black hover:border-black transition-all duration-200"
                    >
                        <ArrowLeft className="w-4 h-4 mr-2" />
                        Back to Events
                    </Button>
                </div>
            </footer>
        </main>
    )
}
