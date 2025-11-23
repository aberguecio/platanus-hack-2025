import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import Image from "next/image"
import { formatDistanceToNow } from "date-fns"

interface Memory {
    id: number
    text?: string
    s3_url?: string
    created_at: string
    user_id: number
    // We might need to fetch user details separately or include them in the API response
    // For now, we'll assume basic user info or placeholders
}

interface MemoryCardProps {
    memory: Memory
}

export function MemoryCard({ memory }: MemoryCardProps) {
    return (
        <Card className="w-full max-w-md mx-auto overflow-hidden border-0 shadow-lg bg-black text-white rounded-xl">
            <CardHeader className="flex flex-row items-center gap-3 p-4">
                <div className="relative w-10 h-10 rounded-full overflow-hidden bg-gray-700 border border-gray-600">
                    {/* Placeholder for user avatar */}
                    <div className="flex items-center justify-center w-full h-full text-sm font-bold">
                        U{memory.user_id}
                    </div>
                </div>
                <div className="flex flex-col">
                    <span className="font-bold text-sm">User {memory.user_id}</span>
                    <span className="text-xs text-gray-400">
                        {formatDistanceToNow(new Date(memory.created_at), { addSuffix: true })}
                    </span>
                </div>
            </CardHeader>
            <CardContent className="p-0 relative aspect-[3/4] bg-gray-900">
                {memory.s3_url ? (
                    <Image
                        src={memory.s3_url}
                        alt="Memory"
                        fill
                        className="object-cover"
                        sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                    />
                ) : (
                    <div className="flex items-center justify-center w-full h-full text-gray-500">
                        No Image
                    </div>
                )}
                {/* Overlay text if any */}
                {memory.text && (
                    <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/80 to-transparent">
                        <p className="text-white text-sm font-medium">{memory.text}</p>
                    </div>
                )}
            </CardContent>
            <CardFooter className="p-3 flex justify-between items-center bg-black">
                {/* Reactions or other metadata could go here */}
                <div className="text-xs text-gray-500">
                    Captured at {new Date(memory.created_at).toLocaleTimeString()}
                </div>
            </CardFooter>
        </Card>
    )
}
