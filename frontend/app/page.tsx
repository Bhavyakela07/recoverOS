"use client";

import React, { useState, useEffect } from "react";
import { DollarSign, TrendingUp, ShieldAlert, Activity, Play, RefreshCw, CheckCircle2, AlertTriangle, ArrowUpRight } from "lucide-react";

export default function ExecutiveDashboard() {
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<any>(null);
  const [caseCount, setCaseCount] = useState(50);
  const [holdoutRatio, setHoldoutRatio] = useState(0.15);

  const fetchBatchReport = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/batch/recovery", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          seed: 42,
          case_count: caseCount,
          holdout_ratio: holdoutRatio,
          include_suppressed: true,
          include_human_review: true
        })
      });
      const data = await res.json();
      setReport(data);
    } catch (err) {
      console.error("Failed to connect to RecoverOS API", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBatchReport();
  }, []);

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-800 pb-6">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            Executive Revenue Recovery Dashboard
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Real-time measured recovery economics across batch runs with holdout control group uplift math.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchBatchReport}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm shadow-lg shadow-blue-500/20 transition-all disabled:opacity-50"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-white" />}
            Run Batch Simulation
          </button>
        </div>
      </div>

      {/* Simulator Controls Card */}
      <div className="p-5 rounded-2xl bg-[#111827] border border-[#1F2937] space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-200 flex items-center gap-2">
            <Activity className="w-4 h-4 text-blue-400" /> Batch Recovery Simulator Controls
          </h3>
          <span className="text-xs text-gray-400">Randomized Holdout Group Assignment</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <div className="flex justify-between text-xs text-gray-300 font-medium mb-1.5">
              <span>Cases Detected per Batch</span>
              <span className="text-blue-400 font-mono">{caseCount} cases</span>
            </div>
            <input
              type="range"
              min="10"
              max="200"
              step="10"
              value={caseCount}
              onChange={(e) => setCaseCount(Number(e.target.value))}
              className="w-full h-2 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
            />
          </div>

          <div>
            <div className="flex justify-between text-xs text-gray-300 font-medium mb-1.5">
              <span>Holdout Control Group Ratio</span>
              <span className="text-emerald-400 font-mono">{(holdoutRatio * 100).toFixed(0)}%</span>
            </div>
            <input
              type="range"
              min="0.05"
              max="0.30"
              step="0.05"
              value={holdoutRatio}
              onChange={(e) => setHoldoutRatio(Number(e.target.value))}
              className="w-full h-2 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
            />
          </div>
        </div>
      </div>

      {/* Primary Financial Metric Tiles */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Tile 1: Revenue at Risk */}
        <div className="p-5 rounded-2xl bg-[#111827] border border-[#1F2937] space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold text-gray-400 uppercase tracking-wider">
            <span>Revenue at Risk</span>
            <DollarSign className="w-4 h-4 text-gray-500" />
          </div>
          <div className="text-2xl font-extrabold text-white font-mono">
            {report ? `₹${Number(report.revenue_at_risk).toLocaleString("en-IN", { minimumFractionDigits: 2 })}` : "—"}
          </div>
          <p className="text-xs text-gray-500">{report ? `${report.cases_detected} total cases detected` : "Loading..."}</p>
        </div>

        {/* Tile 2: Measured Money Recovered */}
        <div className="p-5 rounded-2xl bg-[#111827] border border-emerald-500/20 bg-emerald-500/5 space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold text-emerald-400 uppercase tracking-wider">
            <span>Measured Recovered</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-extrabold text-emerald-400 font-mono">
            {report ? `₹${Number(report.measured_money_recovered).toLocaleString("en-IN", { minimumFractionDigits: 2 })}` : "—"}
          </div>
          <p className="text-xs text-emerald-500/80">Observed rupee outcome across batch</p>
        </div>

        {/* Tile 3: Incremental Recovery Rate Uplift */}
        <div className="p-5 rounded-2xl bg-[#111827] border border-blue-500/20 bg-blue-500/5 space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold text-blue-400 uppercase tracking-wider">
            <span>Incremental Uplift</span>
            <TrendingUp className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-extrabold text-blue-400 font-mono">
            {report ? `${report.incremental_recovery_rate_pp > 0 ? "+" : ""}${report.incremental_recovery_rate_pp}%` : "—"}
          </div>
          <p className="text-xs text-blue-400/80">Treatment vs Control group math</p>
        </div>

        {/* Tile 4: Cost per Rupee Recovered */}
        <div className="p-5 rounded-2xl bg-[#111827] border border-[#1F2937] space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold text-gray-400 uppercase tracking-wider">
            <span>Cost per Rupee</span>
            <ShieldAlert className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-extrabold text-amber-400 font-mono">
            {report ? `₹${Number(report.cost_per_rupee_recovered).toFixed(3)}` : "—"}
          </div>
          <p className="text-xs text-gray-500">Intervention efficiency score</p>
        </div>
      </div>

      {/* Guardrail Metrics & Policy Compliance Panel */}
      {report && report.guardrail_metrics && (
        <div className="p-6 rounded-2xl bg-[#111827] border border-[#1F2937] space-y-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-indigo-400" /> Bounded Policy & Guardrail Metrics
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-3.5 rounded-xl bg-[#1F2937]/50 border border-[#374151]">
              <div className="text-xs text-gray-400">Quiet Hours Suppressed</div>
              <div className="text-lg font-bold text-amber-400 font-mono mt-1">
                {report.guardrail_metrics.suppression_rate}
              </div>
            </div>
            <div className="p-3.5 rounded-xl bg-[#1F2937]/50 border border-[#374151]">
              <div className="text-xs text-gray-400">Human Review Escalated</div>
              <div className="text-lg font-bold text-blue-400 font-mono mt-1">
                {report.guardrail_metrics.human_review_rate}
              </div>
            </div>
            <div className="p-3.5 rounded-xl bg-[#1F2937]/50 border border-[#374151]">
              <div className="text-xs text-gray-400">Dispute / Risk Blocked</div>
              <div className="text-lg font-bold text-rose-400 font-mono mt-1">
                {report.guardrail_metrics.policy_block_rate}
              </div>
            </div>
            <div className="p-3.5 rounded-xl bg-[#1F2937]/50 border border-[#374151]">
              <div className="text-xs text-gray-400">Customer Opt-Out Rate</div>
              <div className="text-lg font-bold text-emerald-400 font-mono mt-1">
                {report.guardrail_metrics.opt_out_rate}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
