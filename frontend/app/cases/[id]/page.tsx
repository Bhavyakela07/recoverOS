"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { ArrowLeft, ShieldCheck, Cpu, Sparkles, CheckCircle2, Download, MessageSquare, AlertCircle } from "lucide-react";

export default function CaseDossierPage({ params }: { params: { id: string } }) {
  const [dossier, setDossier] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchDossier();
  }, [params.id]);

  const fetchDossier = async () => {
    setLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/cases/${params.id}/dossier`);
      if (!res.ok) throw new Error("Case dossier not found");
      const data = await res.json();
      setDossier(data);
    } catch (err: any) {
      setError(err.message || "Failed to load dossier");
    } finally {
      setLoading(false);
    }
  };

  const downloadJSONDossier = () => {
    if (!dossier) return;
    const blob = new Blob([JSON.stringify(dossier, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Decision_Dossier_${dossier.case_id}.json`;
    a.click();
  };

  if (loading) {
    return (
      <div className="py-12 text-center text-gray-400 max-w-4xl mx-auto font-sans">
        Loading Decision Dossier audit records...
      </div>
    );
  }

  if (error || !dossier) {
    return (
      <div className="py-12 text-center max-w-4xl mx-auto space-y-4 font-sans">
        <div className="text-rose-400 font-bold text-lg">Case Not Found</div>
        <p className="text-gray-400 text-sm">Case ID '{params.id}' was not found in active batch memory.</p>
        <Link href="/cases" className="inline-flex items-center gap-2 text-blue-400 text-sm font-semibold">
          <ArrowLeft className="w-4 h-4" /> Return to Cases Explorer
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Top Header & Export Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-800 pb-5">
        <div>
          <Link href="/cases" className="inline-flex items-center gap-1.5 text-xs text-gray-400 hover:text-white mb-2">
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Cases Explorer
          </Link>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            Decision Dossier <span className="font-mono text-blue-400 text-lg">#{dossier.case_id}</span>
          </h1>
          <p className="text-xs text-gray-400 mt-0.5">
            Audit-ready governance timeline & cryptographic policy proof token.
          </p>
        </div>

        <button
          onClick={downloadJSONDossier}
          className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-sm shadow-lg shadow-emerald-500/20 transition-all"
        >
          <Download className="w-4 h-4" /> Export Audit Dossier JSON
        </button>
      </div>

      {/* Audit Pipeline Timeline */}
      <div className="space-y-6">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-blue-400" /> Governed Decision Audit Pipeline
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Step 1: Leak Detected */}
          <div className="p-4 rounded-xl bg-[#111827] border border-[#1F2937] space-y-2">
            <div className="text-xs text-gray-400 font-semibold uppercase">Step 1: Leak Detected</div>
            <div className="text-sm font-bold text-white">{dossier.leak_source}</div>
            <p className="text-xs text-gray-500">Event received and normalized into RevenueLeak entity.</p>
          </div>

          {/* Step 2: Calibrated ML Score */}
          <div className="p-4 rounded-xl bg-[#111827] border border-emerald-500/20 bg-emerald-500/5 space-y-2">
            <div className="text-xs text-emerald-400 font-semibold uppercase flex items-center gap-1">
              <Cpu className="w-3.5 h-3.5" /> Step 2: ML Probability
            </div>
            <div className="text-xl font-extrabold text-emerald-400 font-mono">
              {(dossier.ml_scoring.p_recovery * 100).toFixed(0)}%
            </div>
            <p className="text-xs text-emerald-500/80">Brier score estimate: {dossier.ml_scoring.calibration_brier_score}</p>
          </div>

          {/* Step 3: Claude AI Diagnosis */}
          <div className="p-4 rounded-xl bg-[#111827] border border-blue-500/20 bg-blue-500/5 space-y-2">
            <div className="text-xs text-blue-400 font-semibold uppercase flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5" /> Step 3: Claude Reasoning
            </div>
            <div className="text-xs font-semibold text-blue-300 line-clamp-2">
              {dossier.ai_reasoning.diagnosis}
            </div>
            <p className="text-xs text-blue-400/80">Rec Action: {dossier.ai_reasoning.recommended_action}</p>
          </div>

          {/* Step 4: Policy Token & Decision */}
          <div className="p-4 rounded-xl bg-[#111827] border border-indigo-500/20 bg-indigo-500/5 space-y-2">
            <div className="text-xs text-indigo-400 font-semibold uppercase">Step 4: Policy Decision</div>
            <div className="text-sm font-bold text-white font-mono">{dossier.policy_governance.decision}</div>
            <p className="text-xs text-indigo-300 font-mono truncate">{dossier.policy_governance.policy_token || "No Token Required"}</p>
          </div>
        </div>
      </div>

      {/* Raw Dossier JSON Inspection Panel */}
      <div className="p-5 rounded-2xl bg-[#111827] border border-[#1F2937] space-y-3">
        <h3 className="text-sm font-bold text-gray-200">Audit Proof Payload</h3>
        <pre className="p-4 rounded-xl bg-[#090D16] text-xs font-mono text-emerald-400 overflow-x-auto border border-gray-800">
          {JSON.stringify(dossier, null, 2)}
        </pre>
      </div>
    </div>
  );
}
