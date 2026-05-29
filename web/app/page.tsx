import Link from "next/link"
import {
  TrendingUp,
  Package,
  Shield,
  ArrowRight,
  Activity,
} from "lucide-react"
import { Logo } from "@/components/shared/logo"

const MISSIONS = [
  {
    track: "TRACK 1",
    Icon: TrendingUp,
    name: "Account Pulse",
    tagline: "GTM INTELLIGENCE",
    description:
      "Monitor competitor moves, hiring signals, funding events, and product launches across the live web.",
    tools: ["SERP API", "SCRAPER", "UNLOCKER"],
  },
  {
    track: "TRACK 2",
    Icon: Package,
    name: "Supplier Watch",
    tagline: "SUPPLY CHAIN RISK",
    description:
      "Assess supplier financial health, geopolitical exposure, and alternative sourcing opportunities.",
    tools: ["SCRAPER", "UNLOCKER", "BROWSER"],
  },
  {
    track: "TRACK 3",
    Icon: Shield,
    name: "Threat Surface",
    tagline: "SECURITY & COMPLIANCE",
    description:
      "Scan for leaked credentials, CVEs in the tech stack, regulatory flags, and dark web exposure.",
    tools: ["SERP API", "MCP SERVER", "BROWSER"],
  },
] as const

export default function Home() {
  return (
    <main className="min-h-screen bg-background">
      {/* ── Navigation ──────────────────────────────────────────────────── */}
      <nav className="border-b border-zinc-800/60 px-6">
        <div className="max-w-5xl mx-auto h-14 flex items-center justify-between">
          <Logo />
          <div className="flex items-center gap-4">
            <span className="hidden sm:block font-mono text-[10px] text-zinc-700 tracking-wider">
              BRIGHT DATA · WEB DATA UNLOCKED · MAY 2026
            </span>
            <span className="font-mono text-[10px] text-red-500 border border-red-900/40 bg-red-950/20 px-2 py-1 tracking-widest">
              HACKATHON DEMO
            </span>
          </div>
        </div>
      </nav>

      {/* ── Hero ────────────────────────────────────────────────────────── */}
      <section className="max-w-5xl mx-auto px-6 pt-24 pb-20">
        {/* Status chip */}
        <div className="mb-8">
          <span className="inline-flex items-center gap-2 font-mono text-[11px] text-zinc-500 border border-zinc-800 px-3 py-1.5 tracking-wider">
            <Activity className="h-3 w-3 text-green-500" strokeWidth={2.5} />
            5 AGENTS STANDING BY
          </span>
        </div>

        {/* Title */}
        <h1 className="text-[clamp(3rem,8vw,5.5rem)] font-bold tracking-tighter leading-[1.02] mb-5">
          War Room
          <span className="text-zinc-700">AI</span>
        </h1>

        {/* Tagline */}
        <p className="text-lg text-zinc-400 max-w-lg mb-3 leading-relaxed">
          Autonomous Market Battlefield for Enterprise Decision-Making
        </p>

        {/* Agent roll-call */}
        <p className="font-mono text-[11px] text-zinc-700 tracking-widest mb-12">
          PLANNER · RESEARCHER · SKEPTIC · VERIFIER · COMMANDER
        </p>

        {/* CTAs */}
        <div className="flex items-center gap-6">
          <Link
            href="/war-room"
            className="inline-flex items-center gap-2 bg-zinc-100 text-zinc-950 font-mono text-sm font-semibold px-5 py-2.5 hover:bg-white transition-colors"
          >
            Open War Room
            <ArrowRight className="h-4 w-4" strokeWidth={2.5} />
          </Link>
          <a
            href="https://github.com/jpablortiz96/warroom-ai"
            target="_blank"
            rel="noopener noreferrer"
            className="font-mono text-xs text-zinc-600 hover:text-zinc-300 transition-colors"
          >
            github ↗
          </a>
        </div>
      </section>

      {/* ── Section divider ─────────────────────────────────────────────── */}
      <div className="max-w-5xl mx-auto px-6 mb-8">
        <div className="flex items-center gap-4">
          <div className="flex-1 h-px bg-zinc-800" />
          <span className="font-mono text-[10px] text-zinc-700 tracking-widest">
            FLAGSHIP MISSIONS
          </span>
          <div className="flex-1 h-px bg-zinc-800" />
        </div>
      </div>

      {/* ── Mission cards ───────────────────────────────────────────────── */}
      <section className="max-w-5xl mx-auto px-6 pb-24 grid grid-cols-1 sm:grid-cols-3 gap-3">
        {MISSIONS.map(({ track, Icon, name, tagline, description, tools }) => (
          <div
            key={track}
            className="border border-zinc-800 bg-zinc-900/20 p-6 hover:border-zinc-700 hover:bg-zinc-900/40 transition-all group cursor-default"
          >
            {/* Card header row */}
            <div className="flex items-start justify-between mb-5">
              <div className="p-2 border border-zinc-800 text-zinc-500 group-hover:text-zinc-300 transition-colors">
                <Icon className="h-4 w-4" strokeWidth={1.5} />
              </div>
              <span className="font-mono text-[10px] text-zinc-700">{track}</span>
            </div>

            {/* Body */}
            <p className="font-mono text-[10px] text-zinc-600 tracking-wider mb-1">
              {tagline}
            </p>
            <h3 className="text-sm font-semibold text-zinc-100 mb-3">{name}</h3>
            <p className="text-xs text-zinc-500 leading-relaxed mb-5">{description}</p>

            {/* Bright Data product badges */}
            <div className="flex flex-wrap gap-1.5">
              {tools.map((tool) => (
                <span
                  key={tool}
                  className="font-mono text-[9px] text-zinc-700 border border-zinc-800 px-1.5 py-0.5 tracking-wider"
                >
                  {tool}
                </span>
              ))}
            </div>
          </div>
        ))}
      </section>

      {/* ── Footer metadata bar ─────────────────────────────────────────── */}
      <footer className="border-t border-zinc-800/50 px-6 py-5">
        <div className="max-w-5xl mx-auto flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-5">
            {[
              "MCP Server",
              "SERP API",
              "Web Unlocker",
              "Scraping Browser",
              "Web Scraper API",
            ].map((p) => (
              <span key={p} className="font-mono text-[10px] text-zinc-800">
                {p}
              </span>
            ))}
          </div>
          <div className="flex flex-wrap items-center gap-5">
            <span className="font-mono text-[10px] text-zinc-800">LangGraph · Claude · Supabase</span>
            <span className="font-mono text-[9px] text-zinc-800">Built for Bright Data Web Data UNLOCKED · May 2026</span>
            <a
              href="https://github.com/jpablortiz96/warroom-ai"
              target="_blank"
              rel="noopener noreferrer"
              className="font-mono text-[9px] text-zinc-800 hover:text-zinc-600 transition-colors"
            >
              github.com/jpablortiz96/warroom-ai ↗
            </a>
          </div>
        </div>
      </footer>
    </main>
  )
}
