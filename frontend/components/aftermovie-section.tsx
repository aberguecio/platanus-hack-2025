"use client"

import { Film, Play, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"

interface AftermovieSectionProps {
    eventName: string
    videoUrl?: string
}

export function AftermovieSection({ eventName, videoUrl }: AftermovieSectionProps) {
    return (
        <section className="py-24 px-4 bg-gradient-to-b from-black to-gray-950">
            <div className="max-w-4xl md:max-w-5xl lg:max-w-6xl xl:max-w-7xl mx-auto">
                <div className="mb-12">
                    <div className="flex items-center gap-3 mb-4">
                        <Film className="w-6 h-6 text-purple-400" />
                        <h2 className="text-3xl md:text-4xl font-bold text-white">
                            Aftermovie
                        </h2>
                    </div>
                    <p className="text-lg md:text-xl text-gray-300 font-light leading-relaxed max-w-3xl ml-0 md:ml-9">
                        Revive los mejores momentos de <span className="text-purple-400 font-medium">{eventName}</span> en este video resumen creado automáticamente.
                    </p>
                </div>

                {videoUrl ? (
                    // Video player
                    <div className="relative aspect-video rounded-2xl overflow-hidden bg-gray-900 border border-gray-800">
                        <video
                            src={videoUrl}
                            controls
                            className="w-full h-full object-cover"
                            poster="/video-placeholder.jpg"
                        >
                            Tu navegador no soporta el elemento de video.
                        </video>
                    </div>
                ) : (
                    // Placeholder state
                    <div className="relative aspect-video rounded-2xl overflow-hidden bg-gradient-to-br from-gray-900 to-gray-950 border border-gray-800">
                        <div className="absolute inset-0 flex flex-col items-center justify-center p-8 text-center">
                            <div className="mb-6 relative">
                                <div className="w-20 h-20 rounded-full bg-purple-500/20 flex items-center justify-center">
                                    <Play className="w-10 h-10 text-purple-400" />
                                </div>
                                <Sparkles className="w-6 h-6 text-purple-300 absolute -top-2 -right-2 animate-pulse" />
                            </div>

                            <h3 className="text-2xl font-bold text-white mb-3">
                                Aftermovie en Producción
                            </h3>

                            <p className="text-gray-400 mb-6 max-w-md">
                                Estamos creando un video especial con los mejores momentos de este evento. ¡Vuelve pronto!
                            </p>

                            <div className="flex items-center gap-2 text-sm text-gray-500">
                                <div className="w-2 h-2 rounded-full bg-purple-500 animate-pulse" />
                                <span>Generando automáticamente...</span>
                            </div>
                        </div>

                        {/* Decorative gradient overlay */}
                        <div className="absolute inset-0 bg-gradient-to-t from-purple-950/20 via-transparent to-transparent pointer-events-none" />
                    </div>
                )}

                {/* Video stats (optional - can be shown later) */}
                {videoUrl && (
                    <div className="mt-6 flex items-center gap-6 text-sm text-gray-400">
                        <div className="flex items-center gap-2">
                            <Film className="w-4 h-4" />
                            <span>Generado automáticamente</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <Sparkles className="w-4 h-4" />
                            <span>Con IA</span>
                        </div>
                    </div>
                )}
            </div>
        </section>
    )
}
