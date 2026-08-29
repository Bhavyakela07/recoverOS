"use client";

import React, { useState, useEffect } from "react";
import { Layers, PieChart, TrendingUp, ShieldAlert, Cpu, CheckCircle2, BarChart2 } from "lucide-react";

export default function AnalyticsHubPage() {
  const [cases, setCases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCases();
  }, []);

  const fetchCases = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/cases?page_size=100");
      const data = await res.json();
      setCases(data.cases || []);
    } catch (err) {
      console.error("Failed to load analytics cases", err);
    } finally {
      setLoading(false);
    }
  };

  const highPriority = cases.filter((c) => c.priority_tier === "HIGH").length;
  const medPriority = cases.filter((c) => c.priority_tier === "MEDIUM").length;
  const lowPriority = cases.filter((c) => c.priority_tier === "LOW").length;

  const paymentFailures = cases.filter((c) => c.leak_source === "payment_failure").length;
  const checkoutAbandonments = cases.filter((c) => c.leak_source === "checkout_abandonment").length;
  const subscriptionFailures = cases.filter((c) => c.leak_source === "subscription_failure").length;
  const overdueReceivables = cases.filter((c) => c.leak_source === "overdue_receivable").length;

  const allowedCases = cases.filter((c) => c.decision === "ALLOW").length;
  const reviewCases = cases.filter((c) => c.decision === "HUMAN_REVIEW").length;
  const suppressedCases = cases.filter((c) => c.decision === "SUPPRESSED").length;
  const controlCases = cases.filter((c) => c.is_control).length;

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Layers className="w-6 h-6 text-indigo-400" /> Analytics & ML Insights Hub
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Priority tier distributions, Track 03 direction breakdowns, and calibrated ML probability performance.
          </p>
        </div>

        <button
          onClick={fetchCases}
          className="px-3.5 py-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-200 text-xs font-medium transition-colors"
        >
          Refresh Analytics
        </button>
      </div>

      {loading ? (
        <div className="py-12 text-center text-gray-500 font-sans">
          Loading analytics breakdown... Run a Batch Simulation on Dashboard first if empty.
        </div>
      ) : (
        <div className="space-y-8">
          {/* Section 1: Priority Tier Distribution */}
          <div className="p-6 rounded-2xl bg-[#111827] border border-[#1F2937] space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <PieChart className="w-5 h-5 text-rose-400" /> Rule-Based Priority Score Distribution
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-5 rounded-xl bg-rose-500/5 border border-rose-500/20 space-y-2">
                <div className="flex justify-between text-xs font-bold text-rose-400 uppercase">
                  <span>High Priority Tier</span>
                  <span>Score 70–100</span>
                </div>
                <div className="text-3xl font-extrabold text-white font-mono">{highPriority} cases</div>
                <p className="text-xs text-rose-300">Urgent recovery candidates with high LTV & probability</p>
              </div>

              <div className="p-5 rounded-xl bg-amber-500/5 border border-amber-500/20 space-y-2">
                <div className="flex justify-between text-xs font-bold text-amber-400 uppercase">
                  <span>Medium Priority Tier</span>
                  <span>Score 40–69</span>
                </div>
                <div className="text-3xl font-extrabold text-white font-mono">{medPriority} cases</div>
                <p className="text-xs text-amber-300">Standard automated outreach candidates</p>
              </div>

              <div className="p-5 rounded-xl bg-slate-500/5 border border-slate-500/20 space-y-2">
                <div className="flex justify-between text-xs font-bold text-slate-400 uppercase">
                  <span>Low Priority Tier</span>
                  <span>Score 0–39</span>
                </div>
                <div className="text-3xl font-extrabold text-white font-mono">{lowPriority} cases</div>
                <p className="text-xs text-slate-400">Low-amount or low-probability failures</p>
              </div>
            </div>
          </div>

          {/* Section 2: All 4 Track 03 Direction Breakdown */}
          <div className="p-6 rounded-2xl bg-[#111827] border border-[#1F2937] space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <BarChart2 className="w-5 h-5 text-emerald-400" /> Track 03 Revenue Leak Source Breakdown
            </h3>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="p-4 rounded-xl bg-[#1F2937]/50 border border-[#374151] space-y-1">
                <div className="text-xs text-gray-400">Payment Failure</div>
                <div className="text-2xl font-bold text-white font-mono">{paymentFailures}</div>
                <div className="text-[11px] text-emerald-400">Instant Retry Links</div>
              </div>

              <div className="p-4 rounded-xl bg-[#1F2937]/50 border border-[#374151] space-y-1">
                <div className="text-xs text-gray-400">Checkout Abandonment</div>
                <div className="text-2xl font-bold text-white font-mono">{checkoutAbandonments}</div>
                <div className="text-[11px] text-blue-400">Cart Restore Outreach</div>
              </div>

              <div className="p-4 rounded-xl bg-[#1F2937]/50 border border-[#374151] space-y-1">
                <div className="text-xs text-gray-400">Subscription Failure</div>
                <div className="text-2xl font-bold text-white font-mono">{subscriptionFailures}</div>
                <div className="text-[11px] text-purple-400">Mandate Sequencer</div>
              </div>

              <div className="p-4 rounded-xl bg-[#1F2937]/50 border border-[#374151] space-y-1">
                <div className="text-xs text-gray-400">Overdue Receivable</div>
                <div className="text-2xl font-bold text-white font-mono">{overdueReceivables}</div>
                <div className="text-[11px] text-amber-400">Promise-to-Pay Tracker</div>
              </div>
            </div>
          </div>

          {/* Section 3: Bounded Policy Governance Breakdown */}
          <div className="p-6 rounded-2xl bg-[#111827] border border-[#1F2937] space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-indigo-400" /> Bounded Policy Engine Outcomes
            </h3>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300">
                <div className="text-xs uppercase font-bold">ALLOW (Executed)</div>
                <div className="text-2xl font-extrabold font-mono mt-1">{allowedCases}</div>
              </div>

              <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-300">
                <div className="text-xs uppercase font-bold">HUMAN REVIEW</div>
                <div className="text-2xl font-extrabold font-mono mt-1">{reviewCases}</div>
              </div>

              <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300">
                <div className="text-xs uppercase font-bold">SUPPRESSED</div>
                <div className="text-2xl font-extrabold font-mono mt-1">{suppressedCases}</div>
              </div>

              <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-300">
                <div className="text-xs uppercase font-bold">CONTROL GROUP</div>
                <div className="text-2xl font-extrabold font-mono mt-1">{controlCases}</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
