import { notFound } from "next/navigation"

const API_BASE = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/+$/, "")

type Brief = {
  market_move_score: number
  recommended_move: string
  confidence_score: number
  action_pack: {
    headline?: string
    situation?: string
    actions?: { immediate?: string[]; this_week?: string[]; watch?: string[] }
    commander_rationale?: string
  }
}

type Mission = {
  id: string
  target: string
  mission_type: string
  status: string
  created_at: string
}

async function getData(id: string): Promise<{ mission: Mission; brief: Brief } | null> {
  try {
    const res = await fetch(`${API_BASE}/share/${id}`, { cache: "no-store" })
    if (!res.ok) return null
    return res.json()
  } catch {
    return null
  }
}

const MOVE_COLORS: Record<string, string> = {
  ATTACK: "#ef4444",
  DEFEND: "#f59e0b",
  ESCALATE: "#f87171",
  WAIT: "#71717a",
  MONITOR: "#38bdf8",
}

export default async function SharePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const data = await getData(id)
  if (!data) notFound()

  const { mission, brief } = data
  const move = (brief.recommended_move ?? "MONITOR").toUpperCase()
  const moveColor = MOVE_COLORS[move] ?? "#71717a"
  const actions = brief.action_pack.actions ?? {}
  const scoreColor =
    brief.market_move_score >= 80
      ? "#ef4444"
      : brief.market_move_score >= 60
      ? "#f59e0b"
      : brief.market_move_score >= 40
      ? "#d4d4d4"
      : "#71717a"

  return (
    <div style={{ minHeight: "100vh", background: "#0a0a0a", color: "#d4d4d4", fontFamily: "'Courier New', monospace" }}>
      {/* Nav */}
      <div style={{ borderBottom: "1px solid #27272a", padding: "0 24px" }}>
        <div style={{ maxWidth: 800, margin: "0 auto", height: 56, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <span style={{ fontWeight: "bold", letterSpacing: 2, color: "#fff", fontSize: 14 }}>
            WAR ROOM <span style={{ color: "#ef4444" }}>AI</span>
          </span>
          <span style={{ fontSize: 9, color: "#555", letterSpacing: 2 }}>
            PUBLIC BATTLE BRIEF
          </span>
        </div>
      </div>

      <div style={{ maxWidth: 800, margin: "0 auto", padding: "40px 24px 80px" }}>
        {/* Mission header */}
        <div style={{ marginBottom: 32 }}>
          <div style={{ fontSize: 9, letterSpacing: 2, color: "#555", marginBottom: 6, textTransform: "uppercase" }}>
            {mission.mission_type.replace("_", " ")} · {new Date(mission.created_at).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}
          </div>
          <h1 style={{ fontSize: 28, fontWeight: "bold", color: "#fff", margin: 0 }}>{mission.target}</h1>
        </div>

        {/* Score block */}
        <div style={{ border: "1px solid #333", background: "#111", padding: 24, marginBottom: 24, display: "flex", gap: 40, alignItems: "center" }}>
          <div>
            <div style={{ fontSize: 9, color: "#555", letterSpacing: 2, marginBottom: 4 }}>MARKET MOVE SCORE</div>
            <div style={{ fontSize: 56, fontWeight: "bold", color: scoreColor, lineHeight: 1 }}>
              {brief.market_move_score}
            </div>
          </div>
          <div>
            <div style={{ fontSize: 9, color: "#555", letterSpacing: 2, marginBottom: 8 }}>RECOMMENDED MOVE</div>
            <div style={{ fontSize: 14, fontWeight: "bold", letterSpacing: 3, color: moveColor, border: `1px solid ${moveColor}40`, padding: "8px 20px" }}>
              {move}
            </div>
          </div>
          <div>
            <div style={{ fontSize: 9, color: "#555", letterSpacing: 2, marginBottom: 4 }}>CONFIDENCE</div>
            <div style={{ fontSize: 24, color: "#aaa" }}>{brief.confidence_score}<span style={{ fontSize: 12, color: "#555" }}>/100</span></div>
          </div>
        </div>

        {/* Situation */}
        {brief.action_pack.headline && (
          <div style={{ marginBottom: 24 }}>
            <div style={{ fontSize: 9, color: "#555", letterSpacing: 2, marginBottom: 8 }}>SITUATION</div>
            <p style={{ fontSize: 14, color: "#fff", fontWeight: "bold", marginBottom: 8 }}>{brief.action_pack.headline}</p>
            {brief.action_pack.situation && (
              <p style={{ fontSize: 12, color: "#999", lineHeight: 1.7 }}>{brief.action_pack.situation}</p>
            )}
          </div>
        )}

        {/* Actions grid */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16, marginBottom: 24 }}>
          {([
            { label: "IMMEDIATE", items: actions.immediate ?? [], color: "#ef4444" },
            { label: "THIS WEEK", items: actions.this_week ?? [], color: "#f59e0b" },
            { label: "WATCH", items: actions.watch ?? [], color: "#38bdf8" },
          ] as const).map(({ label, items, color }) => (
            <div key={label} style={{ border: "1px solid #333", background: "#111", padding: 16 }}>
              <div style={{ fontSize: 9, color, letterSpacing: 2, marginBottom: 12 }}>{label}</div>
              {items.length === 0
                ? <div style={{ color: "#333" }}>—</div>
                : items.map((item, i) => (
                    <div key={i} style={{ fontSize: 11, color: "#aaa", marginBottom: 6, paddingLeft: 16, position: "relative" }}>
                      <span style={{ position: "absolute", left: 0, color }}>→</span>
                      {item}
                    </div>
                  ))}
            </div>
          ))}
        </div>

        {/* Rationale */}
        {brief.action_pack.commander_rationale && (
          <div style={{ borderTop: "1px solid #333", paddingTop: 16, marginBottom: 24 }}>
            <div style={{ fontSize: 9, color: "#555", letterSpacing: 2, marginBottom: 8 }}>COMMANDER RATIONALE</div>
            <p style={{ fontSize: 11, color: "#777", lineHeight: 1.7 }}>{brief.action_pack.commander_rationale}</p>
          </div>
        )}

        {/* Footer */}
        <div style={{ borderTop: "1px solid #27272a", paddingTop: 16, fontSize: 9, color: "#444", display: "flex", justifyContent: "space-between" }}>
          <span>Generated by War Room AI · Powered by Bright Data</span>
          <span>MISSION {id.slice(0, 8).toUpperCase()}</span>
        </div>
      </div>
    </div>
  )
}
