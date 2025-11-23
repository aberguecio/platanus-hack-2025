"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export default function LoginPage() {
    const [phone, setPhone] = useState("")
    const [loading, setLoading] = useState(false)
    const [message, setMessage] = useState("")
    const [error, setError] = useState("")

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setMessage("")
        setError("")

        try {
            // TODO: RM must use the actual backend URL
            const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
            const res = await fetch(`${API_URL}/auth/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ phone_number: phone }),
            })

            const data = await res.json()

            if (!res.ok) {
                throw new Error(data.error || "Failed to send login link")
            }

            setMessage(data.message || "Check your Telegram for the login link!")
        } catch (err: any) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-black text-white p-4">
            <Card className="w-full max-w-md bg-zinc-900 border-zinc-800 text-white">
                <CardHeader>
                    <CardTitle className="text-2xl text-center">Collective Diary</CardTitle>
                    <CardDescription className="text-center text-zinc-400">
                        Enter your phone number to log in
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="space-y-2">
                            <Input
                                type="tel"
                                placeholder="+1234567890"
                                value={phone}
                                onChange={(e) => setPhone(e.target.value)}
                                className="bg-zinc-800 border-zinc-700 text-white placeholder:text-zinc-500"
                                required
                            />
                        </div>
                        <Button
                            type="submit"
                            className="w-full bg-white text-black hover:bg-zinc-200"
                            disabled={loading}
                        >
                            {loading ? "Sending..." : "Send Login Link"}
                        </Button>

                        {message && (
                            <div className="p-3 bg-green-900/50 border border-green-900 rounded text-green-200 text-sm text-center">
                                {message}
                            </div>
                        )}

                        {error && (
                            <div className="p-3 bg-red-900/50 border border-red-900 rounded text-red-200 text-sm text-center">
                                {error}
                            </div>
                        )}
                    </form>
                </CardContent>
            </Card>
        </div>
    )
}
