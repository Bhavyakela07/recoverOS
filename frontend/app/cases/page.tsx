"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Database, Search, Filter, ArrowUpRight, ShieldCheck, AlertTriangle, FileText, CheckCircle } from "lucide-react";

export default function CasesExplorerPage() {
  const [cases, setCases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterDecision, setFilterDecision] = useState("ALL");
  const [filterPriority, setFilterPriority] = useState("ALL");

  useEffect(() => {
    fetchCases();
  }, []);

  const fetchCases = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/cases?page_size=50");
      const data = await res.json();
      setCases(data.cases || []);
    } catch (err) {
      console.error("Could not fetch cases", err);
    } finally {
      setLoading(false);
    }
  };

  const filteredCases = cases.filter((c) => {
    const matchesSearch =
      c.case_id.toLowerCase().includes(search.toLowerCase()) ||
      c.customer_id.toLowerCase().includes(search.toLowerCase());
    const matchesDecision =
      filterDecision === "ALL" || c.decision.toUpperCase() === filterDecision.toUpperCase();
    const matchesPriority =
      filterPriority === "ALL" || (c.priority_tier && c.priority_tier.toUpperCase() === filterPriority.toUpperCase());
    return matchesSearch && matchesDecision && matchesPriority;
  });

  const getDecisionBadge = (decision: string) => {
    const d = decision.toUpperCase();
    if (d === "ALLOW") {
      return <span className="px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-semibold">ALLOW</span>;
    } else if (d === "HUMAN_REVIEW") {
      return <span className="px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 text-xs font-semibold">HUMAN REVIEW</span>;
    } else if (d === "SUPPRESSED") {
      return <span className="px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 text-xs font-semibold">SUPPRESSED</span>;
    } else if (d === "CONTROL") {
      return <span className="px-2.5 py-1 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20 text-xs font-semibold">CONTROL</span>;
    }
    return <span className="px-2.5 py-1 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 text-xs font-semibold">DENY</span>;
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Database className="w-6 h-6 text-emerald-400" /> Recovery Case Explorer
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Search, filter, and inspect governed policy decision records and Decision Dossiers.
          </p>
        </div>

        <button
          onClick={fetchCases}
          className="px-3.5 py-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-200 text-xs font-medium transition-colors"
        >
          Refresh Cases
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 rounded-xl bg-[#111827] border border-[#1F2937]">
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-gray-500 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search by Case ID or Customer..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-[#1F2937] text-gray-200 text-xs rounded-lg pl-9 pr-4 py-2.5 border border-[#374151] focus:outline-none focus:border-blue-500"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
          <div className="flex items-center gap-1">
            <span className="text-[11px] text-gray-400 font-semibold mr-1">Decision:</span>
            {["ALL", "ALLOW", "HUMAN_REVIEW", "SUPPRESSED", "DENY"].map((d) => (
              <button
                key={d}
                onClick={() => setFilterDecision(d)}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                  filterDecision === d
                    ? "bg-blue-600 text-white font-bold"
                    : "bg-gray-800/60 text-gray-400 hover:bg-gray-700 hover:text-gray-200"
                }`}
              >
                {d.replace("_", " ")}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-1 border-l border-gray-700 pl-2">
            <span className="text-[11px] text-gray-400 font-semibold mr-1">Priority:</span>
            {["ALL", "HIGH", "MEDIUM", "LOW"].map((p) => (
              <button
                key={p}
                onClick={() => setFilterPriority(p)}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                  filterPriority === p
                    ? "bg-rose-600 text-white font-bold"
                    : "bg-gray-800/60 text-gray-400 hover:bg-gray-700 hover:text-gray-200"
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Cases Data Table */}
      <div className="rounded-2xl bg-[#111827] border border-[#1F2937] overflow-hidden shadow-xl">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-[#1F2937] bg-[#0F172A]/50 text-xs font-semibold text-gray-400 uppercase">
              <th className="py-3.5 px-4">Case ID</th>
              <th className="py-3.5 px-4">Leak Source</th>
              <th className="py-3.5 px-4">Amount</th>
              <th className="py-3.5 px-4">ML Prob (p_rec)</th>
              <th className="py-3.5 px-4">Priority Score</th>
              <th className="py-3.5 px-4">Policy Decision</th>
              <th className="py-3.5 px-4">Reason Code</th>
              <th className="py-3.5 px-4 text-right">Dossier</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1F2937] text-xs text-gray-300 font-mono">
            {loading ? (
              <tr>
                <td colSpan={8} className="py-8 text-center text-gray-500 font-sans">
                  Loading recovery cases...
                </td>
              </tr>
            ) : filteredCases.length === 0 ? (
              <tr>
                <td colSpan={8} className="py-8 text-center text-gray-500 font-sans">
                  No cases found matching filters. Run a Batch Simulation on Dashboard first.
                </td>
              </tr>
            ) : (
              filteredCases.map((c) => (
                <tr key={c.case_id} className="hover:bg-[#1E293B]/40 transition-colors">
                  <td className="py-3.5 px-4 font-bold text-white">{c.case_id}</td>
                  <td className="py-3.5 px-4 text-gray-400 font-sans">{c.leak_source}</td>
                  <td className="py-3.5 px-4 text-white font-bold">₹{c.amount_inr?.toLocaleString("en-IN")}</td>
                  <td className="py-3.5 px-4 text-emerald-400 font-bold">
                    {(c.p_recovery * 100).toFixed(0)}%
                  </td>
                  <td className="py-3.5 px-4 font-sans">
                    <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                      c.priority_tier === "HIGH" ? "bg-rose-500/10 text-rose-400 border border-rose-500/20" :
                      c.priority_tier === "MEDIUM" ? "bg-amber-500/10 text-amber-400 border border-amber-500/20" :
                      "bg-slate-500/10 text-slate-400 border border-slate-500/20"
                    }`}>
                      {c.priority_score || 75} ({c.priority_tier || "HIGH"})
                    </span>
                  </td>
                  <td className="py-3.5 px-4">{getDecisionBadge(c.decision)}</td>
                  <td className="py-3.5 px-4 text-gray-400 text-[11px]">{c.reason_code}</td>
                  <td className="py-3.5 px-4 text-right font-sans">
                    <Link
                      href={`/cases/${c.case_id}`}
                      className="inline-flex items-center gap-1 text-blue-400 hover:text-blue-300 text-xs font-semibold"
                    >
                      Inspect <ArrowUpRight className="w-3.5 h-3.5" />
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
