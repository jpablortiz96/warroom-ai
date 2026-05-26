import Link from "next/link"
import { Shield } from "lucide-react"

export function Logo() {
  return (
    <Link
      href="/"
      className="flex items-center gap-2.5 hover:opacity-75 transition-opacity"
    >
      <Shield className="h-4 w-4 text-red-500" strokeWidth={2} />
      <span className="font-mono text-sm font-bold tracking-[0.12em] text-zinc-100">
        WAR ROOM
      </span>
      <span className="font-mono text-[10px] text-zinc-600 border border-zinc-800 px-1.5 py-0.5 tracking-widest">
        AI
      </span>
    </Link>
  )
}
