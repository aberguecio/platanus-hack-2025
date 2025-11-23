"use client"

import { Newspaper, Clock, Users, Twitter, Facebook, Link2, Quote } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useState } from "react"

interface ArticleNarrativeProps {
    narrative: string
    eventName: string
    eventDate?: string
    participantCount?: number
    photos?: Array<{ s3_url: string; text?: string }>
    quotes?: Array<{ text: string; author: string }>
}

export function ArticleNarrative({
    narrative,
    eventName,
    eventDate,
    participantCount = 0,
    photos = [],
    quotes = []
}: ArticleNarrativeProps) {
    const [copied, setCopied] = useState(false)

    // Handle null/undefined narrative
    if (!narrative || typeof narrative !== 'string') {
        return (
            <div className="py-20 px-4 bg-gradient-to-b from-gray-950 to-black">
                <div className="max-w-4xl mx-auto text-center">
                    <p className="text-gray-500">Generating your collective story...</p>
                    <p className="text-sm text-gray-600 mt-2">This may take a moment as we weave together your memories.</p>
                </div>
            </div>
        )
    }

    const wordCount = narrative.split(/\s+/).length
    const readingTime = Math.ceil(wordCount / 200)

    const handleShare = (platform: string) => {
        const url = window.location.href
        const text = `Check out this story: ${eventName}`

        switch (platform) {
            case 'twitter':
                window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`, '_blank')
                break
            case 'facebook':
                window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`, '_blank')
                break
            case 'copy':
                navigator.clipboard.writeText(url)
                setCopied(true)
                setTimeout(() => setCopied(false), 2000)
                break
        }
    }

    const formattedDate = eventDate
        ? new Date(eventDate).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        })
        : 'Recently'

    // Split narrative into sections
    const sections = narrative.split('\n\n').filter(p => p.trim())

    // Filter valid photos
    const validPhotos = photos.filter(p =>
        p &&
        p.s3_url &&
        typeof p.s3_url === 'string' &&
        (p.s3_url.startsWith('http://') || p.s3_url.startsWith('https://'))
    )

    // Debug logging
    console.log('ArticleNarrative - Photos received:', photos)
    console.log('ArticleNarrative - Valid photos:', validPhotos)
    console.log('ArticleNarrative - Sections count:', sections.length)

    const displayQuotes = quotes.length > 0 ? quotes : []

    return (
        <article className="py-16 px-4 bg-gradient-to-b from-gray-950 to-black">
            {/* Responsive width: grows wider on larger screens */}
            <div className="max-w-4xl md:max-w-5xl lg:max-w-6xl xl:max-w-7xl mx-auto">
                {/* Header */}
                <header className="mb-12 pb-6 border-b border-gray-800">
                    <div className="flex items-center gap-2 text-blue-400 mb-3">
                        <Newspaper className="w-4 h-4" />
                        <span className="text-xs font-medium uppercase tracking-wider">Collective Chronicle</span>
                    </div>

                    <h1 className="text-3xl md:text-4xl font-bold text-white mb-4 leading-tight">
                        {eventName}
                    </h1>

                    <div className="flex flex-wrap items-center gap-4 text-gray-400 text-sm mb-4">
                        <div className="flex items-center gap-1.5">
                            <Users className="w-3.5 h-3.5" />
                            <span>{participantCount} {participantCount === 1 ? 'contributor' : 'contributors'}</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                            <Clock className="w-3.5 h-3.5" />
                            <span>{readingTime} min read</span>
                        </div>
                        <time className="text-gray-500">{formattedDate}</time>
                    </div>

                    <div className="flex items-center gap-2">
                        <Button onClick={() => handleShare('twitter')} variant="outline" size="sm" className="h-8 border-gray-700 text-gray-400 hover:border-blue-400 hover:text-blue-400">
                            <Twitter className="w-3.5 h-3.5" />
                        </Button>
                        <Button onClick={() => handleShare('facebook')} variant="outline" size="sm" className="h-8 border-gray-700 text-gray-400 hover:border-blue-500 hover:text-blue-500">
                            <Facebook className="w-3.5 h-3.5" />
                        </Button>
                        <Button onClick={() => handleShare('copy')} variant="outline" size="sm" className="h-8 border-gray-700 text-gray-400 hover:border-green-400 hover:text-green-400">
                            <Link2 className="w-3.5 h-3.5" />
                            {copied && <span className="ml-2 text-xs">Copied!</span>}
                        </Button>
                    </div>
                </header>

                {/* Article Body - Alternating Layout */}
                <div className="space-y-12">
                    {sections.map((section, index) => {
                        // Fix: Adjust photo index since index 0 doesn't use a photo
                        // Pattern: Index 0 (no photo), Index 1 (photo 0), Index 2 (photo 1), Index 3 (photo 2), etc.
                        const photoIndex = index > 0 ? Math.floor((index - 1) / 2) : -1
                        const hasPhoto = photoIndex >= 0 && photoIndex < validPhotos.length && validPhotos[photoIndex]
                        const isEven = index % 2 === 0

                        // Debug logging for photo display
                        console.log(`[ArticleNarrative] Section ${index}:`, {
                            sectionIndex: index,
                            calculatedPhotoIndex: photoIndex,
                            validPhotosLength: validPhotos.length,
                            hasPhoto: hasPhoto,
                            photoExists: photoIndex >= 0 ? validPhotos[photoIndex] : null,
                            photoUrl: photoIndex >= 0 && validPhotos[photoIndex] ? validPhotos[photoIndex].s3_url : null,
                            validPhotosArray: validPhotos.map((p, i) => ({ index: i, url: p.s3_url, hasUrl: !!p.s3_url }))
                        })

                        // Check if section is a markdown heading (starts with #)
                        const isHeading = section.trim().startsWith('#')
                        if (isHeading) {
                            // Extract heading text (remove # and any extra spaces)
                            const headingText = section.trim().replace(/^#+\s*/, '')
                            return (
                                <h2 key={index} className="text-xl md:text-2xl lg:text-3xl xl:text-4xl font-bold text-white mb-6 leading-tight">
                                    <span className="text-blue-400">#</span> {headingText}
                                </h2>
                            )
                        }

                        // Pattern: Paragraph alone, then Picture+Paragraph, then Paragraph alone, then Paragraph+Picture
                        if (index === 0) {
                            // First paragraph - with drop cap, no picture
                            return (
                                <div key={index} className="prose prose-lg prose-invert max-w-none">
                                    <p className="text-gray-200 leading-relaxed text-xl">
                                        <span className="float-left text-5xl font-bold leading-[0.85] mr-2 text-blue-400">
                                            {section.charAt(0)}
                                        </span>
                                        {section.slice(1)}
                                    </p>
                                </div>
                            )
                        }

                        // Odd indices (1, 3, 5...) - Picture + Paragraph (or just paragraph if no photo)
                        if (index % 2 === 1) {
                            if (hasPhoto && validPhotos[photoIndex]) {
                                const photo = validPhotos[photoIndex]
                                console.log(`[ArticleNarrative] Rendering photo for section ${index}:`, {
                                    photoIndex,
                                    photoUrl: photo.s3_url,
                                    photoText: photo.text
                                })
                                return (
                                    <div key={index} className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
                                        <div className="relative aspect-[4/3] rounded-xl overflow-hidden bg-gray-900 border border-gray-800">
                                            <img
                                                src={photo.s3_url}
                                                alt={photo.text || `Moment from ${eventName}`}
                                                className="w-full h-full object-cover"
                                                onError={(e) => {
                                                    console.error('Image failed to load:', photo.s3_url)
                                                    e.currentTarget.style.display = 'none'
                                                }}
                                                onLoad={() => console.log('Image loaded successfully:', photo.s3_url)}
                                            />
                                        </div>
                                        <div className="prose prose-lg prose-invert max-w-none">
                                            <p className="text-gray-200 leading-relaxed text-lg">{section}</p>
                                        </div>
                                    </div>
                                )
                            } else {
                                // No photo available, just show paragraph
                                console.log(`[ArticleNarrative] No photo for section ${index} (odd index):`, {
                                    photoIndex,
                                    hasPhoto,
                                    validPhotosLength: validPhotos.length,
                                    reason: photoIndex < 0 ? 'Index 0 (no photo slot)' :
                                        photoIndex >= validPhotos.length ? 'Photo index out of bounds' :
                                            !validPhotos[photoIndex] ? 'Photo at index is null/undefined' : 'Unknown'
                                })
                                return (
                                    <div key={index} className="prose prose-lg prose-invert max-w-none">
                                        <p className="text-gray-200 leading-relaxed text-lg">{section}</p>
                                    </div>
                                )
                            }
                        }

                        // Even indices (2, 4, 6...) - Paragraph + Picture (or just paragraph if no photo)
                        if (index % 2 === 0 && index > 0) {
                            if (hasPhoto && validPhotos[photoIndex]) {
                                const photo = validPhotos[photoIndex]
                                console.log(`[ArticleNarrative] Rendering photo for section ${index}:`, {
                                    photoIndex,
                                    photoUrl: photo.s3_url,
                                    photoText: photo.text
                                })
                                return (
                                    <div key={index} className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
                                        <div className="prose prose-lg prose-invert max-w-none">
                                            <p className="text-gray-200 leading-relaxed text-lg">{section}</p>
                                        </div>
                                        <div className="relative aspect-[4/3] rounded-xl overflow-hidden bg-gray-900 border border-gray-800">
                                            <img
                                                src={photo.s3_url}
                                                alt={photo.text || `Moment from ${eventName}`}
                                                className="w-full h-full object-cover"
                                                onError={(e) => {
                                                    console.error('Image failed to load:', photo.s3_url)
                                                    e.currentTarget.style.display = 'none'
                                                }}
                                                onLoad={() => console.log('Image loaded successfully:', photo.s3_url)}
                                            />
                                        </div>
                                    </div>
                                )
                            } else {
                                console.log(`[ArticleNarrative] No photo for section ${index} (even index):`, {
                                    photoIndex,
                                    hasPhoto,
                                    validPhotosLength: validPhotos.length,
                                    reason: photoIndex < 0 ? 'Index 0 (no photo slot)' :
                                        photoIndex >= validPhotos.length ? 'Photo index out of bounds' :
                                            !validPhotos[photoIndex] ? 'Photo at index is null/undefined' : 'Unknown'
                                })
                                return (
                                    <div key={index} className="prose prose-lg prose-invert max-w-none">
                                        <p className="text-gray-200 leading-relaxed text-lg">{section}</p>
                                    </div>
                                )
                            }
                        }

                        // Fallback - just paragraph
                        console.log(`[ArticleNarrative] Fallback for section ${index} (unhandled case)`)
                        return (
                            <div key={index} className="prose prose-lg prose-invert max-w-none">
                                <p className="text-gray-200 leading-relaxed text-lg">{section}</p>
                            </div>
                        )
                    })}

                    {/* Quote Card */}
                    {displayQuotes[0] && (
                        <div className="my-12 py-8 px-6 bg-gradient-to-br from-blue-950/30 to-purple-950/30 rounded-2xl border border-blue-900/30">
                            <Quote className="w-8 h-8 text-blue-400 mb-4 opacity-50" />
                            <blockquote className="text-xl md:text-2xl text-gray-200 font-light italic mb-4 leading-relaxed">
                                "{displayQuotes[0].text}"
                            </blockquote>
                            <p className="text-gray-400 text-sm">— {displayQuotes[0].author}</p>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <footer className="mt-16 pt-8 border-t border-gray-800">
                    <p className="text-lg text-gray-500 italic text-center">
                        "Transformamos recuerdos dispersos en historias que vuelven a emocionar" ✨
                    </p>
                </footer>
            </div>
        </article>
    )
}
