"use client"

import { type RefObject, useCallback, useEffect, useRef, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import Link from "next/link"
import { toast } from "sonner"
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  Loader2,
  ChevronRight,
  RefreshCw,
  Search,
  Globe,
  ShieldCheck,
  FileText,
  Monitor,
  Copy,
  Download,
  Link2,
  Send,
  X,
} from "lucide-react"
import { Logo } from "@/components/shared/logo"
import { apiGet, apiPost } from "@/lib/api"

// Backend base URL — set NEXT_PUBLIC_API_URL in Vercel to the Render backend URL.
// Strip any trailing slash so `${API_BASE}/missions` never becomes a double slash.
const API_BASE = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/+$/, "")

// ── Types ──────────────────────────────────────────────────────────────────

type MissionType = "account_pulse" | "supplier_watch" | "threat_surface"
type Phase = "setup" | "running" | "complete" | "failed"
type Tab = "deploy" | "schedules"

type MissionDiff = {
  has_prior: boolean
  prior_mission_id?: string
  prior_date?: string
  score_delta?: number
  confidence_delta?: number
  move_changed?: boolean
  prior_move?: string
  current_move?: string
  new_findings?: string[]
  resolved_findings?: string[]
  prior_summary?: string
}

type Schedule = {
  id: string
  target: string
  mission_type: string
  cron: string
  label: string | null
  active: boolean
  last_run_at: string | null
  last_mission_id: string | null
}
type AgentStatus = "idle" | "running" | "complete" | "failed"

type AgentState = { status: AgentStatus; message: string }

type BDProductDetail = {
  count: number
  totalLatencyMs: number
  lastGoal: string
  lastStatus: string  // "ok" | "empty" | "failed" | "timeout" | ""
}
type BDDetails = Record<string, BDProductDetail>

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

const PRESETS: {
  track: string
  title: string
  mission: MissionType
  target: string
  tagline: string
}[] = [
  {
    track: "TRACK 1 · GTM",
    title: "Anthropic",
    mission: "account_pulse",
    target: "anthropic.com",
    tagline: "$380B AI giant, dual-cloud distribution — match or fall behind.",
  },
  {
    track: "TRACK 2 · FINANCE",
    title: "Boeing",
    mission: "supplier_watch",
    target: "boeing.com",
    tagline: "Aerospace supplier under regulatory siege — de-risk now?",
  },
  {
    track: "TRACK 3 · SECURITY",
    title: "Change Healthcare",
    mission: "threat_surface",
    target: "change.unitedhealthgroup.com",
    tagline: "Healthcare's largest cyber crisis — what's the exposure?",
  },
]

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

const BD_PRODUCTS: {
  key: string
  label: string
  Icon: React.ElementType
}[] = [
  { key: "serp_api", label: "SERP API", Icon: Search },
  { key: "mcp_server", label: "MCP Server", Icon: Globe },
  { key: "web_unlocker", label: "Web Unlocker", Icon: ShieldCheck },
  { key: "web_scraper_api", label: "Scraper API", Icon: FileText },
  { key: "scraping_browser", label: "Browser", Icon: Monitor },
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

const EMPTY_BD_DETAILS = (): BDDetails => ({})

// ── Page ───────────────────────────────────────────────────────────────────

export default function WarRoomPage() {
  const [tab, setTab] = useState<Tab>("deploy")
  const [phase, setPhase] = useState<Phase>("setup")
  const [selected, setSelected] = useState<MissionType>("account_pulse")
  const [target, setTarget] = useState("")
  const [missionId, setMissionId] = useState<string | null>(null)
  const [schedules, setSchedules] = useState<Schedule[]>([])
  const [isDeploying, setIsDeploying] = useState(false)
  const [agents, setAgents] = useState<Record<AgentName, AgentState>>(INITIAL_AGENTS)
  const [bdDetails, setBdDetails] = useState<BDDetails>(EMPTY_BD_DETAILS)
  const [brief, setBrief] = useState<Brief | null>(null)
  const [log, setLog] = useState<string[]>([])
  const logRef = useRef<HTMLDivElement>(null)
  const esRef = useRef<EventSource | null>(null)

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight
  }, [log])

  const loadSchedules = useCallback(async () => {
    try {
      const data = await apiGet<Schedule[]>("/missions/schedules")
      setSchedules(data)
    } catch {
      // schedules table may not exist yet — show empty state
    }
  }, [])

  useEffect(() => {
    if (tab === "schedules") loadSchedules()
  }, [tab, loadSchedules])

  const pushLog = useCallback((line: string) => {
    setLog((prev) => [...prev.slice(-100), line])
  }, [])

  const deployMission = async (missionTarget: string, missionType: MissionType) => {
    if (isDeploying) return                // block every duplicate click

    setIsDeploying(true)

    // Tear down any existing stream before starting a new one.
    esRef.current?.close()
    esRef.current = null

    // Reset all mission state.
    setLog([])
    setBdDetails(EMPTY_BD_DETAILS())
    setAgents(INITIAL_AGENTS())
    setBrief(null)
    setMissionId(null)

    try {
      const res = await apiPost<{ mission_id: string }>("/missions/", {
        mission_type: missionType,
        target: missionTarget,
        context: null,
      })
      setMissionId(res.mission_id)
      setPhase("running")
      pushLog(`DEPLOYED  mission=${res.mission_id.slice(0, 8)}`)
      startSSE(res.mission_id)
    } catch (err) {
      setIsDeploying(false)
      toast.error("Deploy failed", {
        description: err instanceof Error ? err.message : String(err),
      })
    }
  }

  const handleDeploy = async () => {
    if (!target.trim()) {
      toast.error("Target required", { description: "Enter a company name or domain." })
      return
    }
    await deployMission(target.trim(), selected)
  }

  const handlePresetDeploy = async (presetTarget: string, missionType: MissionType) => {
    setSelected(missionType)
    setTarget(presetTarget)
    await deployMission(presetTarget, missionType)
  }

  const startSSE = (id: string) => {
    const es = new EventSource(`${API_BASE}/missions/${id}/stream`)
    esRef.current = es

    es.addEventListener("agent_event", (e: MessageEvent) => {
      try {
        const d = JSON.parse(e.data as string) as {
          agent: string
          event_type: string
          message: string
          bright_data_product: string | null
          payload?: Record<string, unknown>
        }
        const { agent, event_type, message, bright_data_product, payload } = d

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

        if (bright_data_product) {
          if (event_type === "tool_call") {
            // Capture call count + last goal (strip "Step N: " prefix).
            const goal = message.replace(/^Step \d+:\s*/, "")
            setBdDetails((prev) => {
              const ex = prev[bright_data_product] ?? { count: 0, totalLatencyMs: 0, lastGoal: "", lastStatus: "" }
              return { ...prev, [bright_data_product]: { ...ex, count: ex.count + 1, lastGoal: goal } }
            })
          } else if (event_type === "tool_result") {
            // Capture latency + status from payload.
            const latency = typeof payload?.latency_ms === "number" ? payload.latency_ms : 0
            const status = typeof payload?.status === "string" ? payload.status : ""
            setBdDetails((prev) => {
              const ex = prev[bright_data_product] ?? { count: 0, totalLatencyMs: 0, lastGoal: "", lastStatus: "" }
              return {
                ...prev,
                [bright_data_product]: { ...ex, totalLatencyMs: ex.totalLatencyMs + latency, lastStatus: status },
              }
            })
          }
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
        const r = await fetch(`${API_BASE}/missions/${id}`)
        const data = (await r.json()) as { mission: unknown; brief: Brief | null }
        if (data.brief) setBrief(data.brief)
      } catch {
        // best-effort
      }
      setIsDeploying(false)
      setPhase("complete")
    })

    es.onerror = () => {
      pushLog("SSE ERROR: connection dropped")
      setIsDeploying(false)
      setPhase("failed")
    }
  }

  const handleReset = () => {
    esRef.current?.close()
    esRef.current = null
    setIsDeploying(false)
    setPhase("setup")
    setMissionId(null)
    setBrief(null)
    setLog([])
    setBdDetails(EMPTY_BD_DETAILS())
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
              href="/pricing"
              className="font-mono text-xs text-zinc-600 hover:text-zinc-300 transition-colors"
            >
              Pricing
            </Link>
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

      {/* Tab bar */}
      {phase === "setup" && (
        <div className="border-b border-zinc-800/60 px-6">
          <div className="max-w-5xl mx-auto flex gap-0">
            {(["deploy", "schedules"] as Tab[]).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`font-mono text-[10px] tracking-widest px-5 py-3 border-b-2 transition-colors ${
                  tab === t
                    ? "border-zinc-300 text-zinc-200"
                    : "border-transparent text-zinc-600 hover:text-zinc-400"
                }`}
              >
                {t === "deploy" ? "DEPLOY MISSION" : "SCHEDULED MISSIONS"}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="max-w-5xl mx-auto px-6 pt-10 pb-16">
        {phase !== "setup" ? (
          <ActivePanel
            phase={phase}
            missionType={selected}
            target={target}
            missionId={missionId}
            agents={agents}
            bdDetails={bdDetails}
            brief={brief}
            log={log}
            logRef={logRef}
          />
        ) : tab === "deploy" ? (
          <SetupPanel
            selected={selected}
            onSelect={setSelected}
            target={target}
            onTargetChange={setTarget}
            onDeploy={handleDeploy}
            onPresetDeploy={handlePresetDeploy}
            isDeploying={isDeploying}
          />
        ) : (
          <SchedulesPanel
            schedules={schedules}
            onRefresh={loadSchedules}
            onRunNow={handlePresetDeploy}
          />
        )}
      </div>
      {/* Footer */}
      <footer className="border-t border-zinc-800/50 px-6 py-4 mt-8">
        <div className="max-w-5xl mx-auto flex flex-wrap items-center justify-between gap-3">
          <span className="font-mono text-[9px] text-zinc-800 tracking-widest">
            Built for Bright Data Web Data UNLOCKED · May 2026
          </span>
          <a
            href="https://github.com/jpablortiz96/warroom-ai"
            target="_blank"
            rel="noopener noreferrer"
            className="font-mono text-[9px] text-zinc-800 hover:text-zinc-600 transition-colors tracking-widest"
          >
            github.com/jpablortiz96/warroom-ai ↗
          </a>
        </div>
      </footer>
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
  onPresetDeploy,
  isDeploying,
}: {
  selected: MissionType
  onSelect: (t: MissionType) => void
  target: string
  onTargetChange: (v: string) => void
  onDeploy: () => void
  onPresetDeploy: (target: string, missionType: MissionType) => void
  isDeploying: boolean
}) {
  return (
    <div className="space-y-10">
      <div>
        <p className="font-mono text-[10px] text-zinc-600 tracking-widest mb-2">
          COMMAND CONSOLE · DEPLOY MISSION
        </p>
        <h1 className="text-3xl font-bold tracking-tight text-zinc-100">War Room</h1>
        <p className="text-sm text-zinc-500 mt-1">
          Select a preset mission or configure a custom target below.
        </p>
      </div>

      {/* ── Preset mission cards (locked golden paths) ── */}
      <div className="space-y-3">
        <p className="font-mono text-[10px] text-zinc-600 tracking-widest">
          LOCKED GOLDEN PATHS — ONE-TAP DEMO
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {PRESETS.map((p, i) => (
            <motion.button
              key={p.target}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: i * 0.07 }}
              onClick={() => !isDeploying && onPresetDeploy(p.target, p.mission)}
              disabled={isDeploying}
              className={`group text-left border border-zinc-700 bg-zinc-900/40 p-5 transition-all ${
                isDeploying
                  ? "opacity-50 cursor-not-allowed"
                  : "hover:border-zinc-500 hover:bg-zinc-900/70 cursor-pointer"
              }`}
            >
              <p className="font-mono text-[9px] text-zinc-500 tracking-widest mb-3">
                {p.track}
              </p>
              <p className="font-bold text-zinc-100 text-base mb-0.5">{p.title}</p>
              <p className="font-mono text-[9px] text-zinc-600 tracking-widest mb-3">
                {p.mission.toUpperCase().replace("_", " ")}
              </p>
              <p className="text-xs text-zinc-500 italic leading-relaxed mb-4">
                &ldquo;{p.tagline}&rdquo;
              </p>
              <div className="flex items-center gap-1 font-mono text-[10px] text-zinc-500 group-hover:text-zinc-300 transition-colors">
                Deploy agents
                <ChevronRight className="h-3 w-3" />
              </div>
            </motion.button>
          ))}
        </div>
      </div>

      {/* ── Divider ── */}
      <div className="flex items-center gap-4">
        <div className="flex-1 h-px bg-zinc-800" />
        <span className="font-mono text-[10px] text-zinc-700 tracking-widest">
          OR CUSTOM MISSION
        </span>
        <div className="flex-1 h-px bg-zinc-800" />
      </div>

      {/* ── Mission type selector ── */}
      <div className="space-y-3">
        <p className="font-mono text-[10px] text-zinc-600 tracking-widest">MISSION TYPE</p>
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
      </div>

      {/* ── Target input ── */}
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
            disabled={isDeploying}
            className="flex items-center gap-2 px-6 py-2.5 bg-zinc-100 text-zinc-900 font-mono text-xs font-semibold tracking-widest hover:bg-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isDeploying ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <ChevronRight className="h-3.5 w-3.5" />}
            {isDeploying ? "DEPLOYING…" : "DEPLOY"}
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
  missionId,
  agents,
  bdDetails,
  brief,
  log,
  logRef,
}: {
  phase: Phase
  missionType: MissionType
  target: string
  missionId: string | null
  agents: Record<AgentName, AgentState>
  bdDetails: BDDetails
  brief: Brief | null
  log: string[]
  logRef: RefObject<HTMLDivElement | null>
}) {
  const missionDef = MISSIONS.find((m) => m.type === missionType)!

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

      {/* Bright Data showcase panel — full width */}
      <BDShowcasePanel bdDetails={bdDetails} phase={phase} />

      {/* Live log — full width below BD panel */}
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
          className="overflow-y-auto p-4 font-mono text-[10px] text-zinc-500 space-y-0.5 max-h-56"
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

      {/* Battle Brief (appears when complete) */}
      {phase === "complete" && brief && (
        <BattleBriefPanel brief={brief} missionId={missionId} target={target} />
      )}
    </div>
  )
}

// ── Bright Data showcase panel ─────────────────────────────────────────────

function BDShowcasePanel({ bdDetails, phase }: { bdDetails: BDDetails; phase: Phase }) {
  const totalCalls = BD_PRODUCTS.reduce((sum, p) => sum + (bdDetails[p.key]?.count ?? 0), 0)
  const productsLive = BD_PRODUCTS.filter((p) => (bdDetails[p.key]?.count ?? 0) > 0).length

  return (
    <div className="border border-zinc-700 bg-zinc-900/40">
      {/* Panel header */}
      <div className="border-b border-zinc-700 px-5 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* Bright Data wordmark placeholder */}
          <span className="font-mono text-[10px] font-bold tracking-widest text-zinc-100 bg-zinc-800 px-2 py-0.5 border border-zinc-600">
            BD
          </span>
          <span className="font-mono text-[10px] text-zinc-300 tracking-widest">
            Powered by Bright Data — All 5 products live
          </span>
        </div>
        <div className="flex items-center gap-4">
          <span className="font-mono text-[10px] text-zinc-500">
            {productsLive}/5 active
          </span>
          <span className="font-mono text-[10px] text-zinc-500">
            {totalCalls} total calls
          </span>
          {phase === "running" && (
            <span className="flex items-center gap-1.5 font-mono text-[10px] text-amber-400">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse block" />
              LIVE
            </span>
          )}
        </div>
      </div>

      {/* 5 product cards */}
      <div className="grid grid-cols-5 divide-x divide-zinc-800">
        {BD_PRODUCTS.map(({ key, label, Icon }) => {
          const detail = bdDetails[key]
          const count = detail?.count ?? 0
          const latencyMs = detail?.totalLatencyMs ?? 0
          const lastGoal = detail?.lastGoal ?? ""
          const lastStatus = detail?.lastStatus ?? ""
          const isActive = count > 0

          const statusDot =
            lastStatus === "ok"
              ? "bg-green-500"
              : lastStatus === "empty"
              ? "bg-amber-500"
              : lastStatus === "failed" || lastStatus === "timeout"
              ? "bg-red-500"
              : "bg-zinc-700"

          return (
            <div
              key={key}
              className="group relative flex flex-col gap-3 p-4 hover:bg-zinc-800/40 transition-colors"
            >
              {/* Icon + status dot */}
              <div className="flex items-center justify-between">
                <Icon
                  className={`h-4 w-4 ${isActive ? "text-zinc-300" : "text-zinc-700"}`}
                />
                {isActive && (
                  <span className={`w-1.5 h-1.5 rounded-full block ${statusDot}`} />
                )}
              </div>

              {/* Product label */}
              <p className={`font-mono text-[9px] tracking-widest ${isActive ? "text-zinc-400" : "text-zinc-700"}`}>
                {label}
              </p>

              {/* Call count — large */}
              <p className={`font-mono text-2xl font-bold ${isActive ? "text-zinc-100" : "text-zinc-800"}`}>
                {count}
              </p>

              {/* Latency */}
              <p className="font-mono text-[9px] text-zinc-600">
                {isActive ? `${(latencyMs / 1000).toFixed(1)}s total` : "—"}
              </p>

              {/* Last goal — truncated, monospace */}
              <p className="font-mono text-[9px] text-zinc-700 truncate" title={lastGoal}>
                {lastGoal || "—"}
              </p>

              {/* Hover tooltip — full goal */}
              {isActive && lastGoal && (
                <div className="pointer-events-none absolute bottom-full left-0 mb-2 z-10 w-64 hidden group-hover:block">
                  <div className="border border-zinc-600 bg-zinc-900 p-3 shadow-xl">
                    <p className="font-mono text-[9px] text-zinc-500 tracking-widest mb-1">
                      LAST CALL
                    </p>
                    <p className="font-mono text-[10px] text-zinc-300 leading-relaxed break-words">
                      {lastGoal}
                    </p>
                    {lastStatus && (
                      <p className={`font-mono text-[9px] mt-2 tracking-widest ${
                        lastStatus === "ok" ? "text-green-400" :
                        lastStatus === "empty" ? "text-amber-400" : "text-red-400"
                      }`}>
                        STATUS: {lastStatus.toUpperCase()}
                      </p>
                    )}
                    <p className="font-mono text-[9px] text-zinc-600 mt-1">
                      {latencyMs}ms cumulative
                    </p>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ── Agent row ──────────────────────────────────────────────────────────────

function AgentRow({ name, state }: { name: AgentName; state: AgentState }) {
  const { status, message } = state
  return (
    <motion.div
      className="flex items-center gap-4 px-1 py-1.5"
      animate={{ opacity: status === "idle" ? 0.4 : 1 }}
      transition={{ duration: 0.2 }}
    >
      <div className="w-4 shrink-0 flex justify-center">
        {status === "idle" && (
          <span className="w-1.5 h-1.5 rounded-full bg-zinc-800 block" />
        )}
        {status === "running" && (
          <Loader2 className="h-3.5 w-3.5 text-amber-400 animate-spin" />
        )}
        {status === "complete" && (
          <motion.div initial={{ scale: 0.5 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 400 }}>
            <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
          </motion.div>
        )}
        {status === "failed" && (
          <XCircle className="h-3.5 w-3.5 text-red-500" />
        )}
      </div>
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
      <AnimatePresence mode="wait">
        <motion.span
          key={message}
          initial={{ opacity: 0, x: 4 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          className="font-mono text-[11px] text-zinc-600 truncate"
        >
          {status === "idle" ? "—" : message}
        </motion.span>
      </AnimatePresence>
    </motion.div>
  )
}

// ── Battle Brief panel ─────────────────────────────────────────────────────

function BattleBriefPanel({
  brief,
  missionId,
  target,
}: {
  brief: Brief
  missionId: string | null
  target: string
}) {
  const { market_move_score, confidence_score, action_pack } = brief
  const recommended_move = (brief.recommended_move ?? "monitor").toUpperCase()
  const actions = action_pack.actions ?? {}

  const [diff, setDiff] = useState<MissionDiff | null>(null)
  const [diffModal, setDiffModal] = useState(false)
  const [slackModal, setSlackModal] = useState(false)
  const [slackUrl, setSlackUrl] = useState(() =>
    typeof window !== "undefined" ? (localStorage.getItem("warroom_slack_webhook") ?? "") : ""
  )
  const [slackSending, setSlackSending] = useState(false)

  useEffect(() => {
    if (!missionId) return
    setDiff(null)
    fetch(`${API_BASE}/missions/${missionId}/diff`)
      .then((r) => r.json())
      .then((d: MissionDiff) => { if (d.has_prior) setDiff(d) })
      .catch(() => {})
  }, [missionId])

  const handleCopyMarkdown = () => {
    const move = recommended_move
    const lines = [
      `# War Room AI — Executive Battle Brief`,
      ``,
      `**Target:** ${target}  `,
      `**Recommended Move:** ${move}  `,
      `**Market Move Score:** ${market_move_score}/100  `,
      `**Confidence:** ${confidence_score}/100`,
      ``,
      `## Situation`,
      action_pack.headline ?? "",
      action_pack.situation ?? "",
      ``,
      `## Immediate Actions`,
      ...(actions.immediate ?? []).map((a) => `- ${a}`),
      ``,
      `## This Week`,
      ...(actions.this_week ?? []).map((a) => `- ${a}`),
      ``,
      `## Watch`,
      ...(actions.watch ?? []).map((a) => `- ${a}`),
      ``,
      `## Commander Rationale`,
      action_pack.commander_rationale ?? "",
      ``,
      `---`,
      `*Generated by War Room AI · Powered by Bright Data*`,
    ]
    navigator.clipboard.writeText(lines.join("\n")).then(() => {
      toast.success("Brief copied to clipboard.")
    })
  }

  const handleDownloadPDF = async () => {
    if (!missionId) return
    try {
      const res = await fetch(`${API_BASE}/missions/${missionId}/brief/pdf`)
      if (!res.ok) {
        const err = (await res.json()) as { detail?: string }
        toast.error("PDF unavailable", { description: err.detail ?? "Check server logs." })
        return
      }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `warroom-brief-${target.replace(/\./g, "-")}-${missionId.slice(0, 8)}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      toast.error("PDF download failed.")
    }
  }

  const handleShare = async () => {
    if (!missionId) return
    try {
      const res = await fetch(`${API_BASE}/missions/${missionId}/brief/share`, {
        method: "POST",
      })
      if (!res.ok) throw new Error()
      const { share_url } = (await res.json()) as { share_url: string }
      const full = `${window.location.origin}${share_url}`
      await navigator.clipboard.writeText(full)
      toast.success("Share link copied to clipboard.", { description: full })
    } catch {
      toast.error("Share failed.")
    }
  }

  const handleSendSlack = async () => {
    if (!missionId || !slackUrl.trim()) return
    localStorage.setItem("warroom_slack_webhook", slackUrl.trim())
    setSlackSending(true)
    try {
      const res = await fetch(`${API_BASE}/missions/${missionId}/notify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          webhook_url: slackUrl.trim(),
          share_base: window.location.origin,
        }),
      })
      if (!res.ok) {
        const err = (await res.json()) as { detail?: string }
        toast.error("Slack delivery failed", { description: err.detail ?? "Check webhook URL." })
        return
      }
      toast.success("Brief sent to Slack!")
      setSlackModal(false)
    } catch {
      toast.error("Slack delivery failed.")
    } finally {
      setSlackSending(false)
    }
  }
  const moveStyle = MOVE_STYLES[recommended_move] ?? "text-zinc-400 border-zinc-600 bg-zinc-800/40"
  const scoreColor =
    market_move_score >= 80
      ? "text-red-400"
      : market_move_score >= 60
      ? "text-amber-400"
      : market_move_score >= 40
      ? "text-zinc-300"
      : "text-zinc-500"

  const priorDateStr = diff?.prior_date
    ? new Date(diff.prior_date).toLocaleDateString("en-US", { month: "short", day: "numeric" })
    : ""

  return (
    <>
    {/* ── Diff panel (only when a prior run exists) ── */}
    {diff && diff.has_prior && (
      <div className="border border-zinc-700/60 bg-zinc-900/20 px-5 py-3">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-4 flex-wrap">
            <span className="font-mono text-[9px] text-zinc-500 tracking-widest">
              VS. {priorDateStr.toUpperCase()} RUN
            </span>
            {diff.score_delta !== undefined && (
              <span className={`font-mono text-[10px] font-semibold ${
                diff.score_delta > 0 ? "text-green-400" : diff.score_delta < 0 ? "text-red-400" : "text-zinc-500"
              }`}>
                Score {diff.score_delta > 0 ? "+" : ""}{diff.score_delta}
              </span>
            )}
            {diff.confidence_delta !== undefined && (
              <span className={`font-mono text-[10px] ${
                diff.confidence_delta > 0 ? "text-green-400/70" : diff.confidence_delta < 0 ? "text-red-400/70" : "text-zinc-600"
              }`}>
                Confidence {diff.confidence_delta > 0 ? "+" : ""}{diff.confidence_delta}
              </span>
            )}
            {diff.move_changed ? (
              <span className="font-mono text-[10px] text-amber-400">
                {diff.prior_move} → {diff.current_move}
              </span>
            ) : (
              <span className="font-mono text-[10px] text-zinc-600">
                Move unchanged
              </span>
            )}
            {(diff.new_findings?.length ?? 0) > 0 && (
              <span className="font-mono text-[9px] text-green-500">
                +{diff.new_findings!.length} new
              </span>
            )}
            {(diff.resolved_findings?.length ?? 0) > 0 && (
              <span className="font-mono text-[9px] text-zinc-500">
                -{diff.resolved_findings!.length} resolved
              </span>
            )}
          </div>
          <button
            onClick={() => setDiffModal(true)}
            className="font-mono text-[9px] text-zinc-500 hover:text-zinc-200 transition-colors"
          >
            View diff →
          </button>
        </div>
      </div>
    )}

    {/* ── Diff detail modal ── */}
    {diffModal && diff && (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
        <div className="border border-zinc-700 bg-zinc-950 w-full max-w-2xl max-h-[80vh] overflow-y-auto shadow-2xl">
          <div className="border-b border-zinc-800 px-5 py-3 flex items-center justify-between sticky top-0 bg-zinc-950">
            <span className="font-mono text-[10px] text-zinc-300 tracking-widest">MISSION DIFF — {priorDateStr.toUpperCase()} vs NOW</span>
            <button onClick={() => setDiffModal(false)} className="text-zinc-600 hover:text-zinc-300">
              <X className="h-4 w-4" />
            </button>
          </div>
          <div className="p-5 space-y-5">
            {(diff.new_findings?.length ?? 0) > 0 && (
              <div>
                <p className="font-mono text-[9px] text-green-400 tracking-widest mb-2">NEW FINDINGS</p>
                {diff.new_findings!.map((f, i) => (
                  <div key={i} className="flex items-start gap-2 mb-2">
                    <span className="font-mono text-[9px] text-green-500 shrink-0 mt-0.5">NEW</span>
                    <p className="text-xs text-zinc-300 leading-relaxed">{f}</p>
                  </div>
                ))}
              </div>
            )}
            {(diff.resolved_findings?.length ?? 0) > 0 && (
              <div>
                <p className="font-mono text-[9px] text-zinc-500 tracking-widest mb-2">RESOLVED / NO LONGER SURFACED</p>
                {diff.resolved_findings!.map((f, i) => (
                  <div key={i} className="flex items-start gap-2 mb-2">
                    <span className="font-mono text-[9px] text-zinc-600 shrink-0 mt-0.5">OLD</span>
                    <p className="text-xs text-zinc-600 leading-relaxed line-through">{f}</p>
                  </div>
                ))}
              </div>
            )}
            {diff.prior_summary && (
              <div className="border-t border-zinc-800 pt-4">
                <p className="font-mono text-[9px] text-zinc-500 tracking-widest mb-2">PRIOR BRIEF SITUATION</p>
                <p className="text-xs text-zinc-500 leading-relaxed italic">{diff.prior_summary}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    )}

    <div className="border border-zinc-700 bg-zinc-900/40">
      <div className="border-b border-zinc-700 px-5 py-3 flex items-center justify-between">
        <span className="font-mono text-[10px] text-zinc-400 tracking-widest">
          EXECUTIVE BATTLE BRIEF
        </span>
        <span className="font-mono text-[10px] text-zinc-600">
          CONFIDENCE {confidence_score}/100
        </span>
      </div>

      <div className="p-6 space-y-6">
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

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <ActionColumn label="IMMEDIATE" items={actions.immediate ?? []} accentClass="text-red-400" />
          <ActionColumn label="THIS WEEK" items={actions.this_week ?? []} accentClass="text-amber-400" />
          <ActionColumn label="WATCH" items={actions.watch ?? []} accentClass="text-sky-400" />
        </div>

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

        {/* Action buttons */}
        <div className="border-t border-zinc-800 pt-4 flex flex-wrap items-center gap-3">
          <button
            onClick={handleCopyMarkdown}
            className="flex items-center gap-2 font-mono text-[10px] text-zinc-500 hover:text-zinc-200 border border-zinc-800 hover:border-zinc-600 px-3 py-2 transition-colors"
          >
            <Copy className="h-3 w-3" />
            Copy as Markdown
          </button>
          <button
            onClick={handleDownloadPDF}
            className="flex items-center gap-2 font-mono text-[10px] text-zinc-500 hover:text-zinc-200 border border-zinc-800 hover:border-zinc-600 px-3 py-2 transition-colors"
          >
            <Download className="h-3 w-3" />
            Download PDF
          </button>
          <button
            onClick={handleShare}
            className="flex items-center gap-2 font-mono text-[10px] text-zinc-500 hover:text-zinc-200 border border-zinc-800 hover:border-zinc-600 px-3 py-2 transition-colors"
          >
            <Link2 className="h-3 w-3" />
            Share Link
          </button>
          <button
            onClick={() => setSlackModal(true)}
            className="flex items-center gap-2 font-mono text-[10px] text-zinc-500 hover:text-zinc-200 border border-zinc-800 hover:border-zinc-600 px-3 py-2 transition-colors"
          >
            <Send className="h-3 w-3" />
            Send to Slack
          </button>
        </div>

        {/* Slack webhook modal */}
        {slackModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
            <div className="border border-zinc-700 bg-zinc-950 w-full max-w-md p-6 space-y-4 shadow-2xl">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-mono text-[10px] text-zinc-500 tracking-widest mb-1">SLACK DELIVERY</p>
                  <p className="text-sm font-semibold text-zinc-100">Send Battle Brief to Slack</p>
                </div>
                <button onClick={() => setSlackModal(false)} className="text-zinc-600 hover:text-zinc-300">
                  <X className="h-4 w-4" />
                </button>
              </div>
              <p className="text-xs text-zinc-500 leading-relaxed">
                Paste a Slack Incoming Webhook URL. The brief will be posted as a formatted Block Kit message.
                The URL is saved locally in your browser.
              </p>
              <input
                type="url"
                value={slackUrl}
                onChange={(e) => setSlackUrl(e.target.value)}
                placeholder="https://hooks.slack.com/services/T.../B.../..."
                className="w-full bg-zinc-900 border border-zinc-700 px-3 py-2.5 font-mono text-xs text-zinc-200 placeholder-zinc-700 outline-none focus:border-zinc-500 transition-colors"
                onKeyDown={(e) => e.key === "Enter" && handleSendSlack()}
              />
              <div className="flex items-center gap-3 pt-1">
                <button
                  onClick={handleSendSlack}
                  disabled={!slackUrl.trim() || slackSending}
                  className="flex items-center gap-2 px-4 py-2 bg-zinc-100 text-zinc-900 font-mono text-xs font-semibold hover:bg-white transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {slackSending ? <Loader2 className="h-3 w-3 animate-spin" /> : <Send className="h-3 w-3" />}
                  {slackSending ? "Sending…" : "Send Brief"}
                </button>
                <button
                  onClick={() => setSlackModal(false)}
                  className="font-mono text-xs text-zinc-600 hover:text-zinc-300 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
    </>
  )
}

// ── Schedules panel ────────────────────────────────────────────────────────

function SchedulesPanel({
  schedules,
  onRefresh,
  onRunNow,
}: {
  schedules: Schedule[]
  onRefresh: () => void
  onRunNow: (target: string, missionType: MissionType) => void
}) {
  const handleDelete = async (id: string) => {
    try {
      await fetch(`${API_BASE}/missions/schedules/${id}`, { method: "DELETE" })
      toast.success("Schedule removed.")
      onRefresh()
    } catch {
      toast.error("Failed to remove schedule.")
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <p className="font-mono text-[10px] text-zinc-600 tracking-widest mb-2">
          RECURRING MISSIONS · INNGEST SCHEDULER
        </p>
        <h1 className="text-3xl font-bold tracking-tight text-zinc-100">Scheduled Missions</h1>
        <p className="text-sm text-zinc-500 mt-1">
          Missions that run automatically on a schedule. Results appear in your mission history.
        </p>
      </div>

      {/* Inngest dev server note */}
      <div className="border border-zinc-800 bg-zinc-900/20 px-5 py-3">
        <p className="font-mono text-[10px] text-zinc-600">
          <span className="text-zinc-400">DEV SERVER</span> — start Inngest locally:{" "}
          <span className="text-zinc-300">npx inngest-cli@latest dev -u http://localhost:8000/api/inngest</span>
        </p>
      </div>

      {/* Schedule list */}
      {schedules.length === 0 ? (
        <div className="border border-zinc-800 bg-zinc-900/20 px-5 py-12 text-center">
          <p className="font-mono text-[10px] text-zinc-700">
            NO SCHEDULES — run the SQL migration first:
          </p>
          <p className="font-mono text-[9px] text-zinc-800 mt-1">
            api/scripts/create_mission_schedules.sql
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {schedules.map((s) => (
            <div
              key={s.id}
              className="border border-zinc-800 bg-zinc-900/20 px-5 py-4 flex items-center gap-6"
            >
              {/* Status dot */}
              <span
                className={`w-2 h-2 rounded-full shrink-0 ${s.active ? "bg-green-500" : "bg-zinc-700"}`}
              />

              {/* Label + meta */}
              <div className="flex-1 min-w-0">
                <p className="text-sm text-zinc-200 font-semibold truncate">
                  {s.label ?? `${s.target} · ${s.mission_type}`}
                </p>
                <div className="flex items-center gap-4 mt-1">
                  <span className="font-mono text-[9px] text-zinc-600">{s.cron}</span>
                  <span className="font-mono text-[9px] text-zinc-700">
                    {s.last_run_at
                      ? `Last ran ${new Date(s.last_run_at).toLocaleDateString()}`
                      : "Never run"}
                  </span>
                  {s.last_mission_id && (
                    <span className="font-mono text-[9px] text-zinc-700">
                      MISSION {s.last_mission_id.slice(0, 8).toUpperCase()}
                    </span>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={() => onRunNow(s.target, s.mission_type as MissionType)}
                  className="font-mono text-[10px] text-zinc-500 hover:text-zinc-200 border border-zinc-800 hover:border-zinc-600 px-3 py-1.5 transition-colors"
                >
                  Run now
                </button>
                {s.id !== "preset-anthropic" && (
                  <button
                    onClick={() => handleDelete(s.id)}
                    className="font-mono text-[10px] text-zinc-700 hover:text-red-400 border border-zinc-800 hover:border-red-900/40 px-3 py-1.5 transition-colors"
                  >
                    Remove
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <button
        onClick={onRefresh}
        className="flex items-center gap-2 font-mono text-[10px] text-zinc-600 hover:text-zinc-300 transition-colors"
      >
        <RefreshCw className="h-3 w-3" />
        Refresh
      </button>
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
              <span className={`font-mono text-[10px] mt-0.5 shrink-0 ${accentClass}`}>→</span>
              <span className="text-xs text-zinc-400 leading-relaxed">{item}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
