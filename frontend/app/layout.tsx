import "./globals.css";
import React from "react";
import Link from "next/link";
import { LayoutDashboard, Database, PlayCircle, ShieldCheck, Activity, Layers } from "lucide-react";

export const metadata = {
  title: "RecoverOS — AI Revenue Recovery Decision Engine",
  description: "Razorpay Buildathon Track 03: AI Revenue Recovery Decision Engine",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#0B0F19] text-gray-100 min-h-screen flex flex-col">
        {/* Top Header */}
        <header className="border-b border-[#1F2937] bg-[#111827]/80 backdrop-blur sticky top-0 z-50 px-6 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center font-bold text-white shadow-lg shadow-blue-500/20">
              R
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight text-white flex items-center gap-2">
                RecoverOS <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono">v0.3.0</span>
              </span>
              <p className="text-xs text-gray-400">Razorpay Buildathon · Track 03: AI Revenue Recovery</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              API Online (http://localhost:8000)
            </div>
            <div className="px-3 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-mono">
              Policy Engine v1.0.0
            </div>
          </div>
        </header>

        {/* Main Body with Navigation Sidebar */}
        <div className="flex flex-1">
          {/* Sidebar */}
          <aside className="w-64 border-r border-[#1F2937] bg-[#0F172A]/50 p-4 space-y-6 flex flex-col justify-between">
            <div className="space-y-1">
              <div className="px-3 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Platform Navigation
              </div>
              <Link
                href="/"
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-200 hover:bg-[#1E293B] hover:text-white transition-colors"
              >
                <LayoutDashboard className="w-4 h-4 text-blue-400" />
                Executive Dashboard
              </Link>
              <Link
                href="/recovery"
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-200 hover:bg-[#1E293B] hover:text-white transition-colors"
              >
                <Activity className="w-4 h-4 text-purple-400" />
                AI Recovery Center
              </Link>
              <Link
                href="/cases"
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-200 hover:bg-[#1E293B] hover:text-white transition-colors"
              >
                <Database className="w-4 h-4 text-emerald-400" />
                Case Explorer & Dossier
              </Link>
              <Link
                href="/analytics"
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-200 hover:bg-[#1E293B] hover:text-white transition-colors"
              >
                <Layers className="w-4 h-4 text-indigo-400" />
                Analytics & ML Insights
              </Link>
              <Link
                href="/demo"
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-200 hover:bg-[#1E293B] hover:text-white transition-colors"
              >
                <PlayCircle className="w-4 h-4 text-amber-400" />
                Demo Showcase Replay
              </Link>
            </div>

            <div className="p-3.5 rounded-xl bg-[#1E293B]/60 border border-[#334155] space-y-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-gray-300">
                <ShieldCheck className="w-4 h-4 text-blue-400" /> Bounded Autonomy Policy
              </div>
              <p className="text-xs text-gray-400 leading-relaxed">
                Deterministic PolicyEngine governs all ML probability scores & LLM recommendations.
              </p>
            </div>
          </aside>

          {/* Page Content */}
          <main className="flex-1 p-8 overflow-y-auto">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
