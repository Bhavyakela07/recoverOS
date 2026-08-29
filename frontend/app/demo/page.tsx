"use client";

import React, { useState } from "react";
import { PlayCircle, ShieldCheck, CheckCircle2, AlertTriangle, ArrowUpRight, RefreshCw } from "lucide-react";

export default function DemoShowcasePage() {
  const [loading, setLoading] = useState(false);
  const [demoData, setDemoData] = useState<any>(null);

  const runDemoReplay = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/demo/replay");
      const data = await res.json();
      setDemoData(data);
    } catch (err) {
      console.error("Could not run demo replay", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <PlayCircle className="w-6 h-6 text-amber-400" /> Demo Showcase Replay
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Execute the curated 5-decision policy showcase (ALLOW, HUMAN_REVIEW, DENY, SUPPRESSED, CONTROL).
          </p>
        </div>

        <button
          onClick={runDemoReplay}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-sm shadow-lg shadow-amber-500/20 transition-all disabled:opacity-50"
        >
          {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <PlayCircle className="w-4 h-4 fill-slate-950" />}
          Trigger Curated Showcase Replay
        </button>
      </div>

      {demoData ? (
        <div className="space-y-6">
          <div className="p-5 rounded-2xl bg-[#111827] border border-[#1F2937] space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-blue-400" /> Showcase Policy Decision Pathways
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(demoData.showcase_outcomes || {}).map(([decision, explanation]: [string, any]) => (
                <div key={decision} className="p-4 rounded-xl bg-[#1F2937]/50 border border-[#374151] space-y-1">
                  <div className="text-xs font-mono font-bold text-amber-400 uppercase">{decision}</div>
                  <p className="text-xs text-gray-300 leading-relaxed">{explanation}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-[#111827] border border-[#1F2937] space-y-3">
            <h3 className="text-sm font-bold text-gray-200">Simulated Batch Outcome Report</h3>
            <pre className="p-4 rounded-xl bg-[#090D16] text-xs font-mono text-emerald-400 overflow-x-auto border border-gray-800">
              {JSON.stringify(demoData.batch_report, null, 2)}
            </pre>
          </div>
        </div>
      ) : (
        <div className="p-12 text-center rounded-2xl bg-[#111827] border border-[#1F2937] space-y-4 font-sans">
          <p className="text-gray-400 text-sm">Click "Trigger Curated Showcase Replay" above to test all 5 policy decision pathways live.</p>
        </div>
      )}
    </div>
  );
}
