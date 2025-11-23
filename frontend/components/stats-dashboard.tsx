"use client"

import { Camera, Users, Calendar, Image as ImageIcon } from "lucide-react"

interface EventStats {
    total_memories: number
    by_type: Record<string, number>
    by_user: Array<{
        user_id: number
        count: number
        first_name: string
        last_name: string
    }>
    date_range?: {
        start: string
        end: string
    }
    unique_contributors: number
}

interface StatsDashboardProps {
    stats: EventStats
}

export function StatsDashboard({ stats }: StatsDashboardProps) {
    const getMediaTypeLabel = (type: string) => {
        const labels: Record<string, string> = {
            image: "Fotos",
            video: "Videos",
            audio: "Audio",
            text: "Texto",
            document: "Documentos"
        }
        return labels[type] || type
    }

    return (
        <div className="space-y-8">
            {/* Top stats cards - Clean dark theme */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Total Memories */}
                <div className="bg-gray-900/50 backdrop-blur border border-gray-800 rounded-xl p-6 hover:border-gray-700 transition-colors">
                    <div className="flex items-start justify-between mb-3">
                        <Camera className="w-5 h-5 text-blue-400" />
                    </div>
                    <p className="text-3xl font-bold text-white mb-1">{stats.total_memories}</p>
                    <p className="text-sm text-gray-400">Recuerdos</p>
                </div>

                {/* Contributors */}
                <div className="bg-gray-900/50 backdrop-blur border border-gray-800 rounded-xl p-6 hover:border-gray-700 transition-colors">
                    <div className="flex items-start justify-between mb-3">
                        <Users className="w-5 h-5 text-blue-400" />
                    </div>
                    <p className="text-3xl font-bold text-white mb-1">{stats.unique_contributors}</p>
                    <p className="text-sm text-gray-400">Colaboradores</p>
                </div>

                {/* Photos */}
                <div className="bg-gray-900/50 backdrop-blur border border-gray-800 rounded-xl p-6 hover:border-gray-700 transition-colors">
                    <div className="flex items-start justify-between mb-3">
                        <ImageIcon className="w-5 h-5 text-blue-400" />
                    </div>
                    <p className="text-3xl font-bold text-white mb-1">{stats.by_type.image || 0}</p>
                    <p className="text-sm text-gray-400">Fotos</p>
                </div>

                {/* Duration */}
                <div className="bg-gray-900/50 backdrop-blur border border-gray-800 rounded-xl p-6 hover:border-gray-700 transition-colors">
                    <div className="flex items-start justify-between mb-3">
                        <Calendar className="w-5 h-5 text-blue-400" />
                    </div>
                    <div className="text-lg font-semibold text-white mb-1">
                        {stats.date_range
                            ? `${new Date(stats.date_range.start).toLocaleDateString("es-ES", { month: "short", day: "numeric" })} - ${new Date(stats.date_range.end).toLocaleDateString("es-ES", { month: "short", day: "numeric" })}`
                            : "N/A"}
                    </div>
                    <p className="text-sm text-gray-400">Duración</p>
                </div>
            </div>

            {/* Two column layout for breakdowns */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Media types breakdown */}
                <div className="bg-gray-900/50 backdrop-blur border border-gray-800 rounded-xl p-6">
                    <h3 className="text-lg font-semibold text-white mb-6">Tipos de Medios</h3>
                    <div className="space-y-4">
                        {Object.entries(stats.by_type).map(([type, count]) => (
                            <div key={type} className="space-y-2">
                                <div className="flex items-center justify-between text-sm">
                                    <span className="text-gray-300">{getMediaTypeLabel(type)}</span>
                                    <span className="text-gray-400">{count}</span>
                                </div>
                                <div className="w-full bg-gray-800 rounded-full h-1.5 overflow-hidden">
                                    <div
                                        className="h-full bg-blue-500 rounded-full transition-all duration-500"
                                        style={{
                                            width: `${(count / stats.total_memories) * 100}%`
                                        }}
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Top contributors */}
                <div className="bg-gray-900/50 backdrop-blur border border-gray-800 rounded-xl p-6">
                    <h3 className="text-lg font-semibold text-white mb-6">Principales Colaboradores</h3>
                    <div className="space-y-4">
                        {stats.by_user.slice(0, 5).map((user, index) => (
                            <div key={user.user_id} className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded-full bg-gray-800 border border-gray-700 flex items-center justify-center text-xs font-semibold text-gray-400">
                                    {index + 1}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm text-gray-200 truncate">
                                        {user.first_name} {user.last_name}
                                    </p>
                                    <div className="w-full bg-gray-800 rounded-full h-1.5 overflow-hidden mt-1.5">
                                        <div
                                            className="h-full bg-blue-500 rounded-full transition-all duration-500"
                                            style={{
                                                width: `${(user.count / stats.total_memories) * 100}%`
                                            }}
                                        />
                                    </div>
                                </div>
                                <span className="text-sm font-medium text-gray-400 ml-2">
                                    {user.count}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    )
}
