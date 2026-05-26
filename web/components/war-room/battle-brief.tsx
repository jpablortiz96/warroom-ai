"use client"

// Day 3: Executive Battle Brief renderer.
// Displays: headline, situation, key findings per agent, action pack,
// citations with confidence bars, and the full commander rationale.

export type BattleBriefProps = {
  missionId: string
  marketMoveScore: number
  recommendedMove: "ATTACK" | "DEFEND" | "WAIT" | "ESCALATE" | "MONITOR"
  headline: string
  situation: string
  actionPack: string[]
}

export function BattleBrief({ headline, recommendedMove }: BattleBriefProps) {
  return (
    <div className="border border-zinc-800 bg-zinc-900/20 p-6">
      <p className="font-mono text-[10px] text-zinc-600 tracking-widest mb-2">
        EXECUTIVE BATTLE BRIEF — Day 3
      </p>
      <p className="font-mono text-xs text-red-500">{recommendedMove}</p>
      <p className="text-sm text-zinc-300 mt-2">{headline}</p>
    </div>
  )
}
