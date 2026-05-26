"use client"

// Day 2: Animated agent status card using Framer Motion.
// Shows agent name, current status (pending/thinking/completed/failed),
// latest message, and animates in when the agent activates.

export type AgentCardProps = {
  agent: "planner" | "researcher" | "skeptic" | "verifier" | "commander"
  status: "pending" | "thinking" | "completed" | "failed"
  message?: string
}

export function AgentCard({ agent, status }: AgentCardProps) {
  return (
    <div className="border border-zinc-800 bg-zinc-900/20 p-4">
      <p className="font-mono text-xs text-zinc-600">
        {agent.toUpperCase()} · {status.toUpperCase()} — Day 2
      </p>
    </div>
  )
}
