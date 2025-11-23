"use client"

import { useEffect, useState } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function VerifyPage() {
    const searchParams = useSearchParams()
    const router = useRouter()
    const token = searchParams.get("token")

    const [status, setStatus] = useState<"verifying" | "success" | "error">("verifying")
    const [error, setError] = useState("")

    useEffect(() => {
        if (!token) {
            setStatus("error")
            setError("No token provided")
            return
        }

        const verifyToken = async () => {
            try {
                // TODO: RM must use the actual backend URL
                const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
                const res = await fetch(`${API_URL}/auth/verify`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ token }),
                })

                const data = await res.json()

                if (!res.ok) {
                    throw new Error(data.error || "Verification failed")
                }

                // Store user info (simple implementation)
                localStorage.setItem("user", JSON.stringify(data.user))
                localStorage.setItem("token", data.token)

                setStatus("success")

                // Redirect after short delay
                setTimeout(() => {
                    router.push("/")
                }, 1500)

            } catch (err: any) {
                setStatus("error")
                setError(err.message)
            }
        }

        verifyToken()
    }, [token, router])

    return (
        <div className="min-h-screen flex items-center justify-center bg-black text-white p-4">
            <Card className="w-full max-w-md bg-zinc-900 border-zinc-800 text-white">
                <CardHeader>
                    <CardTitle className="text-2xl text-center">Verifying Login...</CardTitle>
                </CardHeader>
                <CardContent className="flex flex-col items-center justify-center p-6">
                    {status === "verifying" && (
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white"></div>
                    )}

                    {status === "success" && (
                        <div className="text-center space-y-2">
                            <div className="text-green-500 text-4xl mb-2">✓</div>
                            <p className="text-lg font-medium">Login Successful!</p>
                            <p className="text-zinc-400 text-sm">Redirecting you to the diary...</p>
                        </div>
                    )}

                    {status === "error" && (
                        <div className="text-center space-y-2">
                            <div className="text-red-500 text-4xl mb-2">✕</div>
                            <p className="text-lg font-medium">Login Failed</p>
                            <p className="text-red-400 text-sm">{error}</p>
                            <button
                                onClick={() => router.push("/login")}
                                className="mt-4 text-sm underline text-zinc-400 hover:text-white"
                            >
                                Back to Login
                            </button>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    )
}
