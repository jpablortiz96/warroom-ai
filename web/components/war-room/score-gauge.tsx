"use client"

// Day 3: Market Move Score radial gauge using Recharts RadialBarChart.
// Score 0–100. Color zones: 0–30 green (safe), 31–60 amber (caution), 61–100 red (critical).
// Animated fill on mount.

export type ScoreGaugeProps = {
  score: number
  recommendedMove: "ATTACK" | "DEFEND" | "WAIT" | "ESCALATE" | "MONITOR"
}

export function ScoreGauge({ score, recommendedMove }: ScoreGaugeProps) {
  return (
    <div className="border border-zinc-800 bg-zinc-900/20 p-6 flex flex-col items-center gap-2">
      <p className="font-mono text-[10px] text-zinc-600">MARKET MOVE SCORE</p>
      <p className="font-mono text-4xl font-bold text-zinc-100">{score}</p>
      <p className="font-mono text-xs text-zinc-500">{recommendedMove} — Day 3</p>
    </div>
  )
}
