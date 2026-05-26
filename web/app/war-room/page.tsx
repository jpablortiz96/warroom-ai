"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { toast } from "sonner"
import { ArrowLeft, CheckCircle, XCircle, Loader2, AlertTriangle } from "lucide-react"
import { Logo } from "@/components/shared/logo"
import { apiGet } from "@/lib/api"

type HelloResponse = {
  status: "ok" | "config_needed" | "error"
  bright_data_reachable?: boolean
  sample_titles?: string[]
  message?: string
  error?: string
  next_steps?: string[]
}

export default function WarRoomPage() {
  const [data, setData] = useState<HelloResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiGet<HelloResponse>("/missions/hello")
      .then(setData)
      .catch((err: Error) => {
        toast.error("Backend unreachable", {
          description: err.message ?? "Is FastAPI running on http://localhost:8000?",
        })
        setData({ status: "error", error: err.message })
      })
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* ── Navigation ──────────────────────────────────────────────────── */}
      <nav className="border-b border-zinc-800/60 px-6">
        <div className="max-w-4xl mx-auto h-14 flex items-center justify-between">
          <Logo />
          <Link
            href="/"
            className="flex items-center gap-1.5 font-mono text-xs text-zinc-600 hover:text-zinc-300 transition-colors"
          >
            <ArrowLeft className="h-3 w-3" />
            Back
          </Link>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-6 pt-16 pb-24">
        {/* ── Page header ───────────────────────────────────────────────── */}
        <div className="mb-10">
          <p className="font-mono text-[10px] text-zinc-600 tracking-widest mb-2">
            SYSTEM CHECK · DAY 1
          </p>
          <h1 className="text-3xl font-bold tracking-tight text-zinc-100">
            War Room
          </h1>
          <p className="text-sm text-zinc-500 mt-1">
            Backend health · Bright Data connectivity · End-to-end handshake
          </p>
        </div>

        {/* ── Health card ───────────────────────────────────────────────── */}
        <div className="border border-zinc-800 bg-zinc-900/20">
          {/* Card header */}
          <div className="border-b border-zinc-800 px-6 py-3 flex items-center justify-between">
            <span className="font-mono text-xs text-zinc-500 tracking-wider">
              BACKEND HEALTH CHECK
            </span>
            <StatusBadge loading={loading} data={data} />
          </div>

          {/* Card body */}
          <div className="p-6">
            {loading && (
              <div className="flex items-center gap-2 text-zinc-600">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="font-mono text-xs">
                  Connecting to warroom-ai-api on :8000…
                </span>
              </div>
            )}

            {!loading && data && (
              <div className="space-y-6">
                {/* Key-value table */}
                <div className="font-mono text-xs space-y-2">
                  <DataRow label="status" value={data.status} />
                  {data.bright_data_reachable !== undefined && (
                    <DataRow
                      label="bright_data"
                      value={data.bright_data_reachable ? "reachable" : "unreachable"}
                      valueClass={
                        data.bright_data_reachable ? "text-green-400" : "text-red-400"
                      }
                    />
                  )}
                  {data.message && (
                    <DataRow label="message" value={data.message} />
                  )}
                  {data.error && (
                    <DataRow
                      label="error"
                      value={data.error}
                      valueClass="text-red-400"
                    />
                  )}
                </div>

                {/* SERP results */}
                {data.sample_titles && data.sample_titles.length > 0 && (
                  <div>
                    <SectionDivider label='SERP SAMPLE — "war room AI hackathon"' />
                    <ol className="space-y-2.5">
                      {data.sample_titles.map((title, i) => (
                        <li key={i} className="flex items-start gap-3">
                          <span className="font-mono text-[10px] text-zinc-700 w-5 shrink-0 pt-[3px]">
                            {String(i + 1).padStart(2, "0")}
                          </span>
                          <span className="text-sm text-zinc-300 leading-snug">
                            {title}
                          </span>
                        </li>
                      ))}
                    </ol>
                  </div>
                )}

                {/* Config steps */}
                {data.next_steps && data.next_steps.length > 0 && (
                  <div>
                    <SectionDivider label="NEXT STEPS" />
                    <ol className="space-y-2">
                      {data.next_steps.map((step, i) => (
                        <li key={i} className="flex items-start gap-3">
                          <span className="font-mono text-[10px] text-zinc-700 w-4 shrink-0 pt-[3px]">
                            {i + 1}.
                          </span>
                          <span className="font-mono text-xs text-zinc-500">
                            {step}
                          </span>
                        </li>
                      ))}
                    </ol>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* ── Day marker ────────────────────────────────────────────────── */}
        <div className="mt-10 flex items-center gap-4">
          <div className="flex-1 h-px bg-zinc-900" />
          <span className="font-mono text-[10px] text-zinc-800 text-center">
            DAY 1 OF 5 · FOUNDATION COMPLETE · DAY 2: MULTI-AGENT ENGINE
          </span>
          <div className="flex-1 h-px bg-zinc-900" />
        </div>
      </div>
    </div>
  )
}

/* ── Sub-components ────────────────────────────────────────────────────────── */

function StatusBadge({
  loading,
  data,
}: {
  loading: boolean
  data: HelloResponse | null
}) {
  if (loading) {
    return (
      <span className="font-mono text-[10px] text-zinc-600 tracking-widest">
        CHECKING…
      </span>
    )
  }
  if (!data || data.status === "error") {
    return (
      <span className="flex items-center gap-1 font-mono text-[10px] text-red-500 tracking-widest">
        <XCircle className="h-3 w-3" />
        ERROR
      </span>
    )
  }
  if (data.status === "config_needed") {
    return (
      <span className="flex items-center gap-1 font-mono text-[10px] text-amber-500 tracking-widest">
        <AlertTriangle className="h-3 w-3" />
        CONFIG NEEDED
      </span>
    )
  }
  return (
    <span className="flex items-center gap-1 font-mono text-[10px] text-green-500 tracking-widest">
      <CheckCircle className="h-3 w-3" />
      OK
    </span>
  )
}

function DataRow({
  label,
  value,
  valueClass = "text-zinc-300",
}: {
  label: string
  value: string
  valueClass?: string
}) {
  return (
    <div className="flex items-baseline gap-6">
      <span className="text-zinc-600 w-28 shrink-0">{label}</span>
      <span className={valueClass}>{value}</span>
    </div>
  )
}

function SectionDivider({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-4 my-4">
      <div className="flex-1 h-px bg-zinc-800" />
      <span className="font-mono text-[10px] text-zinc-700 tracking-widest whitespace-nowrap">
        {label}
      </span>
      <div className="flex-1 h-px bg-zinc-800" />
    </div>
  )
}
