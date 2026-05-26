import type { Metadata } from "next"
import { Geist, Geist_Mono } from "next/font/google"
import { Toaster } from "sonner"
import "./globals.css"

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] })
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] })

export const metadata: Metadata = {
  title: "War Room AI — Autonomous Market Battlefield",
  description:
    "Deploy 5 autonomous agents to monitor competitors, suppliers, and threats. " +
    "Receive an Executive Battle Brief with a Market Move Score and Recommended Move.",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-background text-foreground">
        {children}
        <Toaster
          position="bottom-right"
          theme="dark"
          toastOptions={{
            classNames: {
              toast: "font-mono text-xs border-zinc-700 bg-zinc-900",
              title: "text-zinc-100",
              description: "text-zinc-500",
            },
          }}
        />
      </body>
    </html>
  )
}
