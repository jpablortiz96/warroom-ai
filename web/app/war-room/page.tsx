"use client"

import { type RefObject, useCallback, useEffect, useRef, useState } from "react"
import Link from "next/link"
import { toast } from "sonner"
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  Loader2,
  ChevronRight,
  RefreshCw,
} from "lucide-react"
import { Logo } from "@/components/shared/logo"
import { apiPost } from "@/lib/api"

// ── Types ──────────────────────────────────────────────────────────────────

type MissionType = "account_pulse" | "supplier_watch" | "threat_surface"
type Phase = "setup" | "running" | "complete" | "failed"
type AgentStatus = "idle" | "running" | "complete" | "failed"

type AgentState = { status: AgentStatus; message: string }
type BDCounts = Record<string, number>

type Brief = {
  market_move_score: number
  recommended_move: string
  confidence_score: number
  executive_summary: string
  action_pack: {
    headline?: string
    situation?: string
    actions?: { immediate?: string[]; this_week?: string[]; watch?: string[] }
    commander_rationale?: string
  }
}

// ── Static data ────────────────────────────────────────────────────────────

const MISSIONS: {
  type: MissionType
  track: string
  name: string
  description: string
  tools: string[]
}[] = [
  {
    type: "account_pulse",
    track: "TRACK 1 · GTM",
    name: "Account Pulse",
    description: "Competitor moves, funding events, exec changes, product launches",
    tools: ["SERP API", "MCP Server", "Web Unlocker"],
  },
  {
    type: "supplier_watch",
    track: "TRACK 2 · FINANCE",
    name: "Supplier Watch",
    description: "Financial health, risk signals, market position, contract exposure",
    tools: ["SERP API", "Web Scraper API", "Scraping Browser"],
  },
  {
    type: "threat_surface",
    track: "TRACK 3 · SECURITY",
    name: "Threat Surface",
    description: "Breach history, CVEs, dark web exposure, domain reputation",
    tools: ["SERP API", "Web Unlocker", "MCP Server"],
  },
]

const AGENTS = ["planner", "researcher", "skeptic", "verifier", "commander"] as const
type AgentName = (typeof AGENTS)[number]

const BD_PRODUCTS = [
  { key: "serp_api", label: "SERP API" },
  { key: "mcp_server", label: "MCP Server" },
  { key: "web_unlocker", label: "Web Unlocker" },
  { key: "web_scraper_api", label: "Scraper API" },
  { key: "scraping_browser", label: "Browser" },
]

const MOVE_STYLES: Record<string, string> = {
  ATTACK: "text-red-400 border-red-500/40 bg-red-500/5",
  DEFEND: "text-amber-400 border-amber-500/40 bg-amber-500/5",
  ESCALATE: "text-red-300 border-red-400/40 bg-red-400/5",
  WAIT: "text-zinc-400 border-zinc-600 bg-zinc-800/40",
  MONITOR: "text-sky-400 border-sky-500/40 bg-sky-500/5",
}

const INITIAL_AGENTS = (): Record<AgentName, AgentState> =>
  Object.fromEntries(
    AGENTS.map((a) => [a, { status: "idle" as AgentStatus, message: "" }])
  ) as Record<AgentName, AgentState>

// ── Page ───────────────────────────────────────────────────────────────────

export default function WarRoomPage() {
  const [phase, setPhase] = useState<Phase>("setup")
  const [selected, setSelected] = useState<MissionType>("account_pulse")
  const [target, setTarget] = useState("")
  const [missionId, setMissionId] = useState<string | null>(null)
  const [agents, setAgents] = useState<Record<AgentName, AgentState>>(INITIAL_AGENTS)
  const [bdCounts, setBdCounts] = useState<BDCounts>({})
  const [brief, setBrief] = useState<Brief | null>(null)
  const [log, setLog] = useState<string[]>([])
  const logRef = useRef<HTMLDivElement>(null)
  const esRef = useRef<EventSource | null>(null)

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight
  }, [log])

  const pushLog = useCallback((line: string) => {
    setLog((prev) => [...prev.slice(-100), line])
  }, [])

  const handleDeploy = async () => {
    if (!target.trim()) {
      toast.error("Target required", { description: "Enter a company name or domain." })
      return
    }
    try {
      const res = await apiPost<{ mission_id: string }>("/missions/", {
        mission_type: selected,
        target: target.trim(),
        context: null,
      })
      setMissionId(res.mission_id)
      setPhase("running")
      pushLog(`DEPLOYED  mission=${res.mission_id.slice(0, 8)}`)
      startSSE(res.mission_id)
    } catch (err) {
      toast.error("Deploy failed", {
        description: err instanceof Error ? err.message : String(err),
      })
    }
  }

  const startSSE = (id: string) => {
    const es = new EventSource(`http://localhost:8000/missions/${id}/stream`)
    esRef.current = es

    es.addEventListener("agent_event", (e: MessageEvent) => {
      try {
        const d = JSON.parse(e.data as string)
        const { agent, event_type, message, bright_data_product } = d as {
          agent: string
          event_type: string
          message: string
          bright_data_product: string | null
        }

        setAgents((prev) => {
          const next = { ...prev }
          const a = agent as AgentName
          if (!AGENTS.includes(a)) return prev
          if (["started", "thinking", "tool_call", "tool_result"].includes(event_type)) {
            next[a] = { status: "running", message }
          } else if (event_type === "completed") {
            next[a] = { status: "complete", message }
          } else if (event_type === "failed") {
            next[a] = { status: "failed", message }
          }
          return next
        })

        if (bright_data_product && event_type === "tool_call") {
          setBdCounts((prev) => ({
            ...prev,
            [bright_data_product]: (prev[bright_data_product] ?? 0) + 1,
          }))
        }

        const tag = agent.toUpperCase().padEnd(10)
        pushLog(`${tag}  ${event_type.padEnd(12)}  ${message}`)
      } catch {
        // ignore malformed events
      }
    })

    es.addEventListener("done", async () => {
      es.close()
      esRef.current = null
      pushLog("─────────────  MISSION COMPLETE  ─────────────")
      try {
        const r = await fetch(`http://localhost:8000/missions/${id}`)
        const data = (await r.json()) as { mission: unknown; brief: Brief | null }
        if (data.brief) setBrief(data.brief)
      } catch {
        // best-effort
      }
      setPhase("complete")
    })

    es.onerror = () => {
      pushLog("SSE ERROR: connection dropped")
    }
  }

  const handleReset = () => {
    esRef.current?.close()
    setPhase("setup")
    setMissionId(null)
    setBrief(null)
    setLog([])
    setBdCounts({})
    setAgents(INITIAL_AGENTS())
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <nav className="border-b border-zinc-800/60 px-6">
        <div className="max-w-5xl mx-auto h-14 flex items-center justify-between">
          <Logo />
          <div className="flex items-center gap-5">
            {missionId && (
              <span className="font-mono text-[10px] text-zinc-700 tracking-widest">
                MISSION {missionId.slice(0, 8).toUpperCase()}
              </span>
            )}
            {phase !== "setup" && (
              <button
                onClick={handleReset}
                className="flex items-center gap-1.5 font-mono text-[10px] text-zinc-600 hover:text-zinc-300 transition-colors"
              >
                <RefreshCw className="h-3 w-3" />
                NEW MISSION
              </button>
            )}
            <Link
              href="/"
              className="flex items-center gap-1.5 font-mono text-xs text-zinc-600 hover:text-zinc-300 transition-colors"
            >
              <ArrowLeft className="h-3 w-3" />
              Back
            </Link>
          </div>
        </div>
      </nav>

      <div className="max-w-5xl mx-auto px-6 pt-10 pb-24">
        {phase === "setup" ? (
          <SetupPanel
            selected={selected}
            onSelect={setSelected}
            target={target}
            onTargetChange={setTarget}
            onDeploy={handleDeploy}
          />
        ) : (
          <ActivePanel
            phase={phase}
            missionType={selected}
            target={target}
            agents={agents}
            bdCounts={bdCounts}
            brief={brief}
            log={log}
            logRef={logRef}
          />
        )}
      </div>
    </div>
  )
}

// ── Setup panel ────────────────────────────────────────────────────────────

function SetupPanel({
  selected,
  onSelect,
  target,
  onTargetChange,
  onDeploy,
}: {
  selected: MissionType
  onSelect: (t: MissionType) => void
  target: string
  onTargetChange: (v: string) => void
  onDeploy: () => void
}) {
  return (
    <div className="space-y-10">
      <div>
        <p className="font-mono text-[10px] text-zinc-600 tracking-widest mb-2">
          COMMAND CONSOLE · DEPLOY MISSION
        </p>
        <h1 className="text-3xl font-bold tracking-tight text-zinc-100">War Room</h1>
        <p className="text-sm text-zinc-500 mt-1">
          Select a mission type, enter a target, and deploy the 5-agent pipeline.
        </p>
      </div>

      {/* Mission type cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {MISSIONS.map((m) => (
          <button
            key={m.type}
            onClick={() => onSelect(m.type)}
            className={`text-left border p-5 transition-colors ${
              selected === m.type
                ? "border-zinc-400 bg-zinc-900/60"
                : "border-zinc-800 bg-zinc-900/20 hover:border-zinc-700"
            }`}
          >
            <p className="font-mono text-[9px] text-zinc-600 tracking-widest mb-2">
              {m.track}
            </p>
            <p className="font-semibold text-zinc-100 text-sm mb-1.5">{m.name}</p>
            <p className="text-xs text-zinc-500 leading-relaxed mb-4">{m.description}</p>
            <div className="flex flex-wrap gap-1">
              {m.tools.map((t) => (
                <span
                  key={t}
                  className="font-mono text-[9px] px-1.5 py-0.5 border border-zinc-800 text-zinc-600 bg-zinc-900"
                >
                  {t}
                </span>
              ))}
            </div>
          </button>
        ))}
      </div>

      {/* Target input */}
      <div className="border border-zinc-800 bg-zinc-900/20">
        <div className="border-b border-zinc-800 px-5 py-2.5">
          <span className="font-mono text-[10px] text-zinc-600 tracking-widest">
            INTELLIGENCE TARGET
          </span>
        </div>
        <div className="p-5 flex gap-3">
          <input
            type="text"
            value={target}
            onChange={(e) => onTargetChange(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && onDeploy()}
            placeholder="Company name, domain, or ticker — e.g. Wix.com"
            className="flex-1 bg-zinc-950 border border-zinc-800 px-4 py-2.5 font-mono text-sm text-zinc-200 placeholder-zinc-700 outline-none focus:border-zinc-600 transition-colors"
          />
          <button
            onClick={onDeploy}
            className="flex items-center gap-2 px-6 py-2.5 bg-zinc-100 text-zinc-900 font-mono text-xs font-semibold tracking-widest hover:bg-white transition-colors"
          >
            DEPLOY
            <ChevronRight className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Active panel (running / complete) ─────────────────────────────────────

function ActivePanel({
  phase,
  missionType,
  target,
  agents,
  bdCounts,
  brief,
  log,
  logRef,
}: {
  phase: Phase
  missionType: MissionType
  target: string
  agents: Record<AgentName, AgentState>
  bdCounts: BDCounts
  brief: Brief | null
  log: string[]
  logRef: RefObject<HTMLDivElement>
}) {
  const missionDef = MISSIONS.find((m) => m.type === missionType)!
  const totalBDCalls = Object.values(bdCounts).reduce((a, b) => a + b, 0)

  return (
    <div className="space-y-6">
      {/* Mission header */}
      <div className="flex items-baseline justify-between">
        <div>
          <p className="font-mono text-[10px] text-zinc-600 tracking-widest mb-1">
            {missionDef.track} · {missionType.toUpperCase().replace("_", " ")}
          </p>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-100">{target}</h1>
        </div>
        <span
          className={`font-mono text-[10px] tracking-widest px-2 py-1 border ${
            phase === "running"
              ? "border-amber-600/40 text-amber-400 bg-amber-500/5"
              : phase === "complete"
              ? "border-green-600/40 text-green-400 bg-green-500/5"
              : "border-red-600/40 text-red-400 bg-red-500/5"
          }`}
        >
          {phase === "running" ? "● RUNNING" : phase === "complete" ? "✓ COMPLETE" : "✗ FAILED"}
        </span>
      </div>

      {/* Agent pipeline */}
      <div className="border border-zinc-800 bg-zinc-900/20">
        <div className="border-b border-zinc-800 px-5 py-2.5">
          <span className="font-mono text-[10px] text-zinc-600 tracking-widest">
            AGENT PIPELINE
          </span>
        </div>
        <div className="p-4 flex flex-col gap-2">
          {AGENTS.map((name) => (
            <AgentRow key={name} name={name} state={agents[name]} />
          ))}
        </div>
      </div>

      {/* Two-column: live log + BD counter */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Live log */}
        <div className="border border-zinc-800 bg-zinc-900/20 flex flex-col">
          <div className="border-b border-zinc-800 px-5 py-2.5 flex items-center justify-between">
            <span className="font-mono text-[10px] text-zinc-600 tracking-widest">
              LIVE FEED
            </span>
            {phase === "running" && (
              <Loader2 className="h-3 w-3 text-zinc-600 animate-spin" />
            )}
          </div>
          <div
            ref={logRef}
            className="flex-1 overflow-y-auto p-4 font-mono text-[10px] text-zinc-500 space-y-0.5 max-h-72"
          >
            {log.length === 0 ? (
              <span className="text-zinc-800">Waiting for events…</span>
            ) : (
              log.map((line, i) => (
                <div key={i} className="leading-5 whitespace-pre-wrap break-all">
                  {line}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Bright Data counter */}
        <div className="border border-zinc-800 bg-zinc-900/20">
          <div className="border-b border-zinc-800 px-5 py-2.5 flex items-center justify-between">
            <span className="font-mono text-[10px] text-zinc-600 tracking-widest">
              BRIGHT DATA COVERAGE
            </span>
            <span className="font-mono text-[10px] text-zinc-600">
              {totalBDCalls} CALLS
            </span>
          </div>
          <div className="p-4 space-y-2">
            {BD_PRODUCTS.map(({ key, label }) => {
              const count = bdCounts[key] ?? 0
              return (
                <div key={key} className="flex items-center gap-3">
                  <span className="font-mono text-[10px] text-zinc-600 w-28 shrink-0">
                    {label}
                  </span>
                  <div className="flex-1 h-1 bg-zinc-900 rounded-none overflow-hidden">
                    <div
                      className="h-full bg-zinc-400 transition-all duration-500"
                      style={{ width: count > 0 ? `${Math.min(count * 20, 100)}%` : "0%" }}
                    />
                  </div>
                  <span
                    className={`font-mono text-[10px] w-5 text-right ${
                      count > 0 ? "text-zinc-300" : "text-zinc-800"
                    }`}
                  >
                    {count}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Battle Brief (appears when complete) */}
      {phase === "complete" && brief && <BattleBriefPanel brief={brief} />}
    </div>
  )
}

// ── Agent row ──────────────────────────────────────────────────────────────

function AgentRow({ name, state }: { name: AgentName; state: AgentState }) {
  const { status, message } = state
  return (
    <div className="flex items-center gap-4 px-1 py-1.5">
      {/* Status icon */}
      <div className="w-4 shrink-0 flex justify-center">
        {status === "idle" && (
          <span className="w-1.5 h-1.5 rounded-full bg-zinc-800 block" />
        )}
        {status === "running" && (
          <Loader2 className="h-3.5 w-3.5 text-amber-400 animate-spin" />
        )}
        {status === "complete" && (
          <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
        )}
        {status === "failed" && (
          <XCircle className="h-3.5 w-3.5 text-red-500" />
        )}
      </div>

      {/* Agent name */}
      <span
        className={`font-mono text-xs w-24 shrink-0 font-semibold ${
          status === "idle"
            ? "text-zinc-700"
            : status === "running"
            ? "text-amber-300"
            : status === "complete"
            ? "text-green-400"
            : "text-red-400"
        }`}
      >
        {name.toUpperCase()}
      </span>

      {/* Latest message */}
      <span className="font-mono text-[11px] text-zinc-600 truncate">
        {status === "idle" ? "—" : message}
      </span>
    </div>
  )
}

// ── Battle Brief panel ─────────────────────────────────────────────────────

function BattleBriefPanel({ brief }: { brief: Brief }) {
  const { market_move_score, confidence_score, action_pack } = brief
  // DB stores lowercase; display always uppercase for tactical readability.
  const recommended_move = (brief.recommended_move ?? "monitor").toUpperCase()
  const moveStyle = MOVE_STYLES[recommended_move] ?? "text-zinc-400 border-zinc-600 bg-zinc-800/40"
  const scoreColor =
    market_move_score >= 80
      ? "text-red-400"
      : market_move_score >= 60
      ? "text-amber-400"
      : market_move_score >= 40
      ? "text-zinc-300"
      : "text-zinc-500"
  const actions = action_pack.actions ?? {}

  return (
    <div className="border border-zinc-700 bg-zinc-900/40">
      {/* Header */}
      <div className="border-b border-zinc-700 px-5 py-3 flex items-center justify-between">
        <span className="font-mono text-[10px] text-zinc-400 tracking-widest">
          EXECUTIVE BATTLE BRIEF
        </span>
        <span className="font-mono text-[10px] text-zinc-600">
          CONFIDENCE {confidence_score}/100
        </span>
      </div>

      <div className="p-6 space-y-6">
        {/* Score + Move */}
        <div className="flex items-start gap-8">
          <div className="text-center">
            <div className={`font-mono text-5xl font-bold ${scoreColor}`}>
              {market_move_score}
            </div>
            <div className="font-mono text-[9px] text-zinc-700 tracking-widest mt-1">
              MARKET MOVE SCORE
            </div>
          </div>
          <div>
            <div
              className={`inline-block font-mono text-sm font-bold tracking-widest px-4 py-2 border ${moveStyle}`}
            >
              {recommended_move}
            </div>
            <div className="font-mono text-[9px] text-zinc-700 tracking-widest mt-1">
              RECOMMENDED MOVE
            </div>
          </div>
        </div>

        {/* Headline + Situation */}
        {action_pack.headline && (
          <div>
            <p className="font-mono text-[9px] text-zinc-600 tracking-widest mb-2">
              SITUATION
            </p>
            <p className="text-sm text-zinc-200 font-semibold leading-relaxed">
              {action_pack.headline}
            </p>
            {action_pack.situation && (
              <p className="text-sm text-zinc-400 mt-2 leading-relaxed">
                {action_pack.situation}
              </p>
            )}
          </div>
        )}

        {/* Action Pack */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <ActionColumn
            label="IMMEDIATE"
            items={actions.immediate ?? []}
            accentClass="text-red-400"
          />
          <ActionColumn
            label="THIS WEEK"
            items={actions.this_week ?? []}
            accentClass="text-amber-400"
          />
          <ActionColumn
            label="WATCH"
            items={actions.watch ?? []}
            accentClass="text-sky-400"
          />
        </div>

        {/* Rationale */}
        {action_pack.commander_rationale && (
          <div className="border-t border-zinc-800 pt-4">
            <p className="font-mono text-[9px] text-zinc-600 tracking-widest mb-2">
              COMMANDER RATIONALE
            </p>
            <p className="text-xs text-zinc-500 leading-relaxed">
              {action_pack.commander_rationale}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

function ActionColumn({
  label,
  items,
  accentClass,
}: {
  label: string
  items: string[]
  accentClass: string
}) {
  return (
    <div>
      <p className={`font-mono text-[9px] tracking-widest mb-2 ${accentClass}`}>{label}</p>
      {items.length === 0 ? (
        <p className="font-mono text-[10px] text-zinc-800">—</p>
      ) : (
        <ul className="space-y-1.5">
          {items.map((item, i) => (
            <li key={i} className="flex items-start gap-2">
              <span className={`font-mono text-[10px] mt-0.5 shrink-0 ${accentClass}`}>
                →
              </span>
              <span className="text-xs text-zinc-400 leading-relaxed">{item}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
