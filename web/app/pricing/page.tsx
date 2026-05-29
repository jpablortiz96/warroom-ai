import Link from "next/link"
import { ArrowLeft, Check, ArrowRight } from "lucide-react"
import { Logo } from "@/components/shared/logo"

const TIERS = [
  {
    name: "Solo",
    price: "$99",
    period: "/mo",
    description: "For individual analysts and founders who need intelligence on demand.",
    features: [
      "50 missions / month",
      "1 user",
      "All 3 mission types",
      "PDF export",
      "Public share links",
      "Mission diff & history",
      "Community support",
    ],
    cta: "Start free trial",
    popular: false,
  },
  {
    name: "Team",
    price: "$399",
    period: "/mo",
    description: "For GTM, finance, and security teams that need recurring intelligence.",
    features: [
      "250 missions / month",
      "10 users",
      "All 3 mission types",
      "Slack delivery",
      "Recurring scheduled missions",
      "PDF export + share links",
      "Mission diff & history",
      "Email + Slack support",
    ],
    cta: "Start free trial",
    popular: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "",
    description: "For organizations that need unlimited intelligence at scale.",
    features: [
      "Unlimited missions",
      "Unlimited users",
      "Custom mission templates",
      "CRM integrations (HubSpot, Salesforce)",
      "On-premise / self-hosted option",
      "SLA + dedicated support",
      "Custom Bright Data zones",
      "SSO + audit logs",
    ],
    cta: "Contact sales",
    popular: false,
  },
]

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Nav */}
      <nav className="border-b border-zinc-800/60 px-6">
        <div className="max-w-5xl mx-auto h-14 flex items-center justify-between">
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

      <div className="max-w-5xl mx-auto px-6 pt-16 pb-24">
        {/* Header */}
        <div className="text-center mb-14">
          <p className="font-mono text-[10px] text-zinc-600 tracking-widest mb-3">
            PRICING · WAR ROOM AI
          </p>
          <h1 className="text-4xl font-bold tracking-tight text-zinc-100 mb-3">
            Intelligence at every scale
          </h1>
          <p className="text-sm text-zinc-500 max-w-lg mx-auto leading-relaxed">
            Every tier powered by all 5 Bright Data products. No per-product limits. No lock-in.
            Cancel any time.
          </p>
        </div>

        {/* Tier cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {TIERS.map((tier) => (
            <div
              key={tier.name}
              className={`relative border p-7 flex flex-col ${
                tier.popular
                  ? "border-zinc-400 bg-zinc-900/60"
                  : "border-zinc-800 bg-zinc-900/20"
              }`}
            >
              {tier.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="font-mono text-[9px] tracking-widest px-3 py-1 bg-zinc-100 text-zinc-900 font-semibold">
                    MOST POPULAR
                  </span>
                </div>
              )}

              {/* Tier name */}
              <p className="font-mono text-[10px] text-zinc-600 tracking-widest mb-2">
                {tier.name.toUpperCase()}
              </p>

              {/* Price */}
              <div className="flex items-baseline gap-1 mb-3">
                <span className="text-4xl font-bold text-zinc-100">{tier.price}</span>
                {tier.period && (
                  <span className="font-mono text-sm text-zinc-600">{tier.period}</span>
                )}
              </div>

              <p className="text-xs text-zinc-500 leading-relaxed mb-6">{tier.description}</p>

              {/* Feature list */}
              <ul className="space-y-2.5 flex-1 mb-8">
                {tier.features.map((f) => (
                  <li key={f} className="flex items-start gap-2.5">
                    <Check className="h-3 w-3 text-zinc-400 shrink-0 mt-0.5" />
                    <span className="text-xs text-zinc-400 leading-relaxed">{f}</span>
                  </li>
                ))}
              </ul>

              {/* CTA */}
              <a
                href={tier.name === "Enterprise" ? "mailto:hello@warroom.ai" : "/war-room"}
                className={`flex items-center justify-center gap-2 py-2.5 font-mono text-xs font-semibold tracking-widest transition-colors ${
                  tier.popular
                    ? "bg-zinc-100 text-zinc-900 hover:bg-white"
                    : "border border-zinc-700 text-zinc-300 hover:border-zinc-500 hover:text-white"
                }`}
              >
                {tier.cta}
                <ArrowRight className="h-3 w-3" />
              </a>
            </div>
          ))}
        </div>

        {/* BD attribution footer */}
        <div className="mt-14 border-t border-zinc-800 pt-8 text-center">
          <p className="text-xs text-zinc-600 leading-relaxed max-w-2xl mx-auto">
            All tiers powered by{" "}
            <span className="text-zinc-400 font-semibold">Bright Data</span> infrastructure — SERP API,
            Web Scraper API, Web Unlocker, Scraping Browser, and MCP Server firing on every mission.
            Built for enterprise intelligence teams that ship.
          </p>
          <div className="flex items-center justify-center gap-6 mt-6 flex-wrap">
            <Link
              href="/war-room"
              className="font-mono text-[10px] text-zinc-500 hover:text-zinc-200 transition-colors"
            >
              Try the War Room →
            </Link>
            <Link
              href="/"
              className="font-mono text-[10px] text-zinc-600 hover:text-zinc-400 transition-colors"
            >
              Back to home
            </Link>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-zinc-800/50 px-6 py-4">
        <div className="max-w-5xl mx-auto flex flex-wrap items-center justify-between gap-3">
          <span className="font-mono text-[9px] text-zinc-800 tracking-widest">
            Built for Bright Data Web Data UNLOCKED · May 2026
          </span>
          <a
            href="https://github.com/jpablortiz96/warroom-ai"
            target="_blank"
            rel="noopener noreferrer"
            className="font-mono text-[9px] text-zinc-800 hover:text-zinc-600 transition-colors"
          >
            github.com/jpablortiz96/warroom-ai ↗
          </a>
        </div>
      </footer>
    </div>
  )
}
