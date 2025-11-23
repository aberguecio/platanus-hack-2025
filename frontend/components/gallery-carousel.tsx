"use client"

import { useState } from "react"
import { ChevronLeft, ChevronRight, Camera } from "lucide-react"
import { Button } from "@/components/ui/button"

interface Photo {
    id: number
    s3_url: string
    text?: string
    created_at: string
    relevance_score: number
}

interface GalleryCarouselProps {
    photos: Photo[]
}

export function GalleryCarousel({ photos }: GalleryCarouselProps) {
    const [currentIndex, setCurrentIndex] = useState(0)

    // Enhanced validation: check for array and filter valid photos
    if (!photos || !Array.isArray(photos) || photos.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center h-96 bg-gray-900 rounded-2xl">
                <Camera className="w-16 h-16 text-gray-700 mb-4" />
                <p className="text-gray-500">No photos available</p>
            </div>
        )
    }

    // Filter out invalid photos (missing s3_url or other required fields)
    const validPhotos = photos.filter(p => p && p.s3_url && typeof p.s3_url === 'string')

    if (validPhotos.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center h-96 bg-gray-900 rounded-2xl">
                <Camera className="w-16 h-16 text-gray-700 mb-4" />
                <p className="text-gray-500">No valid photos available</p>
            </div>
        )
    }

    const goToPrevious = () => {
        setCurrentIndex((prev) => (prev === 0 ? validPhotos.length - 1 : prev - 1))
    }

    const goToNext = () => {
        setCurrentIndex((prev) => (prev === validPhotos.length - 1 ? 0 : prev + 1))
    }

    const currentPhoto = validPhotos[currentIndex]

    return (
        <div className="relative w-full">
            {/* Main carousel */}
            <div className="relative w-full aspect-video bg-black rounded-2xl overflow-hidden shadow-2xl">
                <img
                    src={currentPhoto.s3_url}
                    alt={currentPhoto.text || `Photo ${currentIndex + 1}`}
                    className="w-full h-full object-contain"
                />

                {/* Caption overlay */}
                {currentPhoto.text && (
                    <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black via-black/80 to-transparent p-6">
                        <p className="text-white text-lg leading-relaxed">
                            {currentPhoto.text}
                        </p>
                    </div>
                )}

                {/* Navigation buttons */}
                {photos.length > 1 && (
                    <>
                        <Button
                            onClick={goToPrevious}
                            className="absolute left-4 top-1/2 -translate-y-1/2 rounded-full w-12 h-12 bg-black/50 hover:bg-black/70 border border-white/20 backdrop-blur-sm"
                            variant="ghost"
                        >
                            <ChevronLeft className="w-6 h-6 text-white" />
                        </Button>
                        <Button
                            onClick={goToNext}
                            className="absolute right-4 top-1/2 -translate-y-1/2 rounded-full w-12 h-12 bg-black/50 hover:bg-black/70 border border-white/20 backdrop-blur-sm"
                            variant="ghost"
                        >
                            <ChevronRight className="w-6 h-6 text-white" />
                        </Button>
                    </>
                )}

                {/* Counter */}
                <div className="absolute top-4 right-4 bg-black/50 backdrop-blur-sm px-4 py-2 rounded-full text-white text-sm border border-white/20">
                    {currentIndex + 1} / {validPhotos.length}
                </div>
            </div>

            {/* Thumbnail strip */}
            {validPhotos.length > 1 && (
                <div className="mt-4 flex gap-2 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-gray-900">
                    {validPhotos.map((photo, index) => (
                        <button
                            key={photo.id}
                            onClick={() => setCurrentIndex(index)}
                            className={`flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden transition-all duration-300 ${
                                index === currentIndex
                                    ? "ring-2 ring-blue-500 scale-110"
                                    : "opacity-60 hover:opacity-100"
                            }`}
                        >
                            <img
                                src={photo.s3_url}
                                alt={`Thumbnail ${index + 1}`}
                                className="w-full h-full object-cover"
                            />
                        </button>
                    ))}
                </div>
            )}
        </div>
    )
}
