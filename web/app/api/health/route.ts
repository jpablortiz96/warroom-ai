import { NextResponse } from "next/server"

export const dynamic = "force-dynamic"

export async function GET() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

  try {
    const res = await fetch(`${apiUrl}/health`, {
      cache: "no-store",
      signal: AbortSignal.timeout(5000),
    })
    const backend = await res.json()
    return NextResponse.json({ frontend: "ok", backend })
  } catch {
    return NextResponse.json(
      { frontend: "ok", backend: "unreachable" },
      { status: 200 },
    )
  }
}
