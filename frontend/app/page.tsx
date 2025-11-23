import { Feed } from "@/components/feed"

export default function Home() {
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
