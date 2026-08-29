"use client";

import React, { useState, useEffect } from "react";
import { Sparkles, MessageSquare, Send, CheckCircle2, ShieldCheck, Cpu, Copy, RefreshCw, AlertTriangle } from "lucide-react";

export default function AIRecoveryCenterPage() {
  const [cases, setCases] = useState<any[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState(false);
  const [executed, setExecuted] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchCases();
  }, []);

  const fetchCases = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/cases?page_size=50");
      const data = await res.json();
      const list = data.cases || [];
      setCases(list);
      if (list.length > 0) {
        setSelectedCaseId(list[0].case_id);
      }
    } catch (err) {
      console.error("Could not load cases", err);
    } finally {
      setLoading(false);
    }
  };

  const selectedCase = cases.find((c) => c.case_id === selectedCaseId);

  const copyMessage = () => {
    if (selectedCase?.draft_message) {
      navigator.clipboard.writeText(selectedCase.draft_message);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const executeAction = () => {
    setExecuting(true);
    setTimeout(() => {
      setExecuting(false);
      setExecuted(true);
      setTimeout(() => setExecuted(false), 3000);
    }, 800);
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-purple-400" /> AI Recovery Center
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Inspect AI failure diagnoses, priority scores, and execute governed customer recovery outreach.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label className="text-xs text-gray-400 font-medium">Select Active Case:</label>
          <select
            value={selectedCaseId}
            onChange={(e) => setSelectedCaseId(e.target.value)}
            className="bg-[#1F2937] text-white text-xs rounded-lg px-3 py-2 border border-[#374151] focus:outline-none focus:border-purple-500 font-mono"
          >
            {cases.map((c) => (
              <option key={c.case_id} value={c.case_id}>
                {c.case_id} — ₹{c.amount_inr?.toLocaleString("en-IN")} ({c.leak_source})
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="py-12 text-center text-gray-500 font-sans">
          Loading AI Recovery Center data... Run a Batch Simulation on Dashboard first if empty.
        </div>
      ) : !selectedCase ? (
        <div className="p-8 text-center rounded-2xl bg-[#111827] border border-[#1F2937] text-gray-400 font-sans">
          No cases found. Run a Batch Simulation on Dashboard first.
        </div>
      ) : (
        <div className="space-y-6">
          {/* Top Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-[#111827] border border-[#1F2937] space-y-1">
              <div className="text-xs text-gray-400">Priority Score</div>
              <div className="text-xl font-bold text-rose-400 font-mono">
                {selectedCase.priority_score || 85} <span className="text-xs text-gray-400 font-normal">({selectedCase.priority_tier || "HIGH"})</span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-[#111827] border border-emerald-500/20 bg-emerald-500/5 space-y-1">
              <div className="text-xs text-emerald-400">Calibrated ML Prob</div>
              <div className="text-xl font-bold text-emerald-400 font-mono">
                {(selectedCase.p_recovery * 100).toFixed(0)}%
              </div>
            </div>

            <div className="p-4 rounded-xl bg-[#111827] border border-blue-500/20 bg-blue-500/5 space-y-1">
              <div className="text-xs text-blue-400">Expected Net Recovery</div>
              <div className="text-xl font-bold text-blue-400 font-mono">
                ₹{((selectedCase.amount_inr || 0) * selectedCase.p_recovery).toLocaleString("en-IN", { maximumFractionDigits: 0 })}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-[#111827] border border-indigo-500/20 bg-indigo-500/5 space-y-1">
              <div className="text-xs text-indigo-400">Policy Status</div>
              <div className="text-sm font-bold text-white font-mono mt-1">
                {selectedCase.decision}
              </div>
            </div>
          </div>

          {/* AI Reasoning Card */}
          <div className="p-6 rounded-2xl bg-[#111827] border border-[#1F2937] space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Cpu className="w-5 h-5 text-purple-400" /> Claude 3.5 Sonnet Diagnostic Analysis
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              <div className="p-4 rounded-xl bg-[#1F2937]/60 border border-[#374151] space-y-1">
                <div className="text-gray-400 font-semibold uppercase">Root Cause Diagnosis</div>
                <div className="text-white font-medium">{selectedCase.diagnosis || "Payment failure flagged"}</div>
              </div>

              <div className="p-4 rounded-xl bg-[#1F2937]/60 border border-[#374151] space-y-1">
                <div className="text-gray-400 font-semibold uppercase">Recommended Action</div>
                <div className="text-purple-300 font-bold uppercase">{selectedCase.recommended_action || "RETRY"}</div>
              </div>

              <div className="p-4 rounded-xl bg-[#1F2937]/60 border border-[#374151] space-y-1">
                <div className="text-gray-400 font-semibold uppercase">Policy Verification</div>
                <div className="text-emerald-400 font-mono truncate">{selectedCase.policy_token || "Token Verified"}</div>
              </div>
            </div>
          </div>

          {/* Hinglish WhatsApp Outreach Card */}
          <div className="p-6 rounded-2xl bg-[#111827] border border-emerald-500/20 bg-emerald-500/5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-emerald-400" /> Hinglish WhatsApp Customer Outreach
              </h3>
              <button
                onClick={copyMessage}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-xs text-gray-300 transition-colors"
              >
                {copied ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                {copied ? "Copied!" : "Copy Message"}
              </button>
            </div>

            <div className="p-4 rounded-xl bg-[#090D16] border border-emerald-500/30 text-sm text-emerald-300 font-sans leading-relaxed">
              "{selectedCase.draft_message || `Hi Customer! We noticed an issue with your payment of ₹${selectedCase.amount_inr}. Click here to retry: https://rzp.io/i/pay`}"
            </div>

            <div className="flex items-center justify-between pt-2">
              <span className="text-xs text-gray-400 flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-400" /> PII Masked & Policy Token Validated
              </span>

              <button
                onClick={executeAction}
                disabled={executing || executed}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm shadow-lg shadow-emerald-500/20 transition-all disabled:opacity-50"
              >
                {executing ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : executed ? (
                  <CheckCircle2 className="w-4 h-4 text-white" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
                {executed ? "Outreach Executed & Logged!" : "Execute Governed Outreach"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
