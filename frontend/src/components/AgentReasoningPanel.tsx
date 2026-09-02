"use client";

import React, { useState } from "react";
import { Brain, ShieldCheck, ShoppingCart, Search, CreditCard, Sparkles, AlertTriangle, X, Zap, Activity, Lock, Cpu, Clock } from "lucide-react";

export interface ReasoningLog {
  action: string;
  reasoning: string;
  timestamp?: string;
  data?: any;
  latency_ms?: number;
  telemetry_pills?: Array<{ name: string; icon: string; duration_ms: number; category: string }>;
}

interface AgentReasoningPanelProps {
  logs: ReasoningLog[];
  isOpen: boolean;
  onClose: () => void;
}

export function AgentReasoningPanel({ logs, isOpen, onClose }: AgentReasoningPanelProps) {
  const [activeTab, setActiveTab] = useState<"reasoning" | "telemetry">("reasoning");

  if (!isOpen) return null;

  // Extract dynamic OpenTelemetry spans from trace log events
  const latestTraceLog = [...logs].reverse().find((l) => l.action === "trace" && (l.data?.trace_data || l.data?.spans));
  const traceData = latestTraceLog?.data?.trace_data || latestTraceLog?.data;
  const rawSpans: Array<{ name: string; category: string; duration_ms: number; metadata?: any }> = traceData?.spans || [];
  const totalMs: number = traceData?.total_latency_ms || rawSpans.reduce((acc, s) => acc + (s.duration_ms || 0), 0) || 1;

  const getActionIcon = (action: string) => {
    switch (action) {
      case "budget_extraction":
      case "budget_check":
        return <ShieldCheck className="h-3.5 w-3.5 text-amber-400" />;
      case "security_check":
      case "prompt_injection_blocked":
        return <Lock className="h-3.5 w-3.5 text-rose-400" />;
      case "budget_guardrail_blocked":
        return <AlertTriangle className="h-3.5 w-3.5 text-rose-400" />;
      case "search_all_stores":
      case "search_catalog":
        return <Search className="h-3.5 w-3.5 text-[#0891B2]" />;
      case "add_to_cart":
      case "remove_from_cart":
        return <ShoppingCart className="h-3.5 w-3.5 text-emerald-400" />;
      case "select_store":
        return <Sparkles className="h-3.5 w-3.5 text-[#A78BFA]" />;
      case "checkout_and_pay":
      case "checkout_saga":
        return <CreditCard className="h-3.5 w-3.5 text-[#0891B2]" />;
      case "trace":
        return <Zap className="h-3.5 w-3.5 text-yellow-400" />;
      default:
        return <Brain className="h-3.5 w-3.5 text-zinc-400" />;
    }
  };

  const getActionBadgeColor = (action: string) => {
    switch (action) {
      case "budget_extraction":
      case "budget_check":
        return "bg-amber-500/10 border-amber-500/30 text-amber-300";
      case "security_check":
      case "prompt_injection_blocked":
        return "bg-rose-500/15 border-rose-500/40 text-rose-300";
      case "budget_guardrail_blocked":
        return "bg-rose-500/10 border-rose-500/30 text-rose-300";
      case "search_all_stores":
      case "search_catalog":
        return "bg-[#0891B2]/10 border-[#0891B2]/30 text-[#0891B2]";
      case "add_to_cart":
        return "bg-emerald-500/10 border-emerald-500/30 text-emerald-300";
      case "select_store":
        return "bg-[#7C3AED]/15 border-[#7C3AED]/30 text-[#A78BFA]";
      case "checkout_and_pay":
      case "checkout_saga":
        return "bg-[#0891B2]/10 border-[#0891B2]/30 text-[#0891B2]";
      case "trace":
        return "bg-yellow-500/10 border-yellow-500/30 text-yellow-300";
      default:
        return "bg-[#1E1E2E] border-[#2A2A3E] text-zinc-300";
    }
  };

  return (
    <div className="fixed inset-y-0 right-0 z-50 flex w-full max-w-md flex-col bg-[#0A0A12]/95 border-l border-[#2A2A3E] shadow-2xl backdrop-blur-2xl transition-all duration-300 sm:max-w-lg">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#2A2A3E] px-4.5 py-3.5">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7.5 w-7.5 items-center justify-center rounded-xl bg-[#7C3AED]/15 border border-[#7C3AED]/30 text-[#A78BFA]">
            <Brain className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-xs sm:text-sm font-bold text-[#F0EEFF] flex items-center gap-2">
              Agent Decision Engine
              <span className="rounded-full bg-[#7C3AED]/20 px-2 py-0.5 text-[10px] font-semibold text-[#A78BFA]">
                {logs.length}
              </span>
            </h3>
            <p className="text-[10px] text-zinc-400">Multi-Hop Reasoning, Security & OTel Telemetry</p>
          </div>
        </div>

        <button
          onClick={onClose}
          className="flex h-7.5 w-7.5 items-center justify-center rounded-xl bg-[#12121E] border border-[#2A2A3E] text-zinc-400 hover:text-white hover:border-[#7C3AED]/40 transition"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-[#2A2A3E] px-4 bg-[#0A0A12]/60">
        <button
          onClick={() => setActiveTab("reasoning")}
          className={`flex items-center gap-1.5 py-2.5 px-3 text-xs font-semibold border-b-2 transition ${
            activeTab === "reasoning"
              ? "border-[#7C3AED] text-[#A78BFA]"
              : "border-transparent text-zinc-400 hover:text-zinc-200"
          }`}
        >
          <Brain className="h-3.5 w-3.5" /> Reasoning Chain ({logs.length})
        </button>
        <button
          onClick={() => setActiveTab("telemetry")}
          className={`flex items-center gap-1.5 py-2.5 px-3 text-xs font-semibold border-b-2 transition ${
            activeTab === "telemetry"
              ? "border-[#0891B2] text-[#0891B2]"
              : "border-transparent text-zinc-400 hover:text-zinc-200"
          }`}
        >
          <Activity className="h-3.5 w-3.5" /> OpenTelemetry Latency
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 font-sans">
        {activeTab === "telemetry" ? (
          <div className="space-y-4">
            <div className="rounded-2xl border border-[#2A2A3E] bg-[#12121E] p-3.5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-zinc-200 flex items-center gap-1.5">
                  <Cpu className="h-3.5 w-3.5 text-[#0891B2]" /> Dynamic Multi-Hop Spans
                </span>
                {traceData && (
                  <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                    Total: {totalMs.toFixed(1)}ms
                  </span>
                )}
              </div>

              {rawSpans.length === 0 ? (
                <div className="py-6 text-center text-zinc-500 text-xs">
                  <Clock className="h-6 w-6 mx-auto mb-2 text-zinc-600 animate-pulse" />
                  <p className="font-medium text-zinc-400">No active trace recorded yet</p>
                  <p className="text-[11px] text-zinc-600 mt-0.5">
                    Send a shopping query to stream real-time millisecond spans from the backend.
                  </p>
                </div>
              ) : (
                <div className="space-y-2.5">
                  {rawSpans.map((s, idx) => {
                    const pct = Math.max(6, Math.min(100, Math.round((s.duration_ms / totalMs) * 100)));
                    return (
                      <div key={idx} className="space-y-1">
                        <div className="flex justify-between text-[11px] text-zinc-300">
                          <span className="font-medium flex items-center gap-1">
                            <span className="text-zinc-500 font-mono">#{idx + 1}</span> {s.name}
                            <span className="text-[9px] uppercase px-1 py-0.2 rounded bg-zinc-800 text-zinc-400 font-mono">
                              {s.category}
                            </span>
                          </span>
                          <span className="font-mono text-cyan-400 font-semibold">{s.duration_ms.toFixed(1)}ms</span>
                        </div>
                        <div className="h-1.5 w-full bg-[#1E1E2E] rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-cyan-400 to-[#7C3AED] rounded-full transition-all duration-300"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            <div className="rounded-2xl border border-[#2A2A3E] bg-[#12121E] p-3.5 space-y-2">
              <h4 className="text-xs font-bold text-zinc-200">Architecture Resilience Controls</h4>
              <div className="grid grid-cols-2 gap-2 text-[11px]">
                <div className="p-2 rounded-xl bg-[#1E1E2E] border border-[#2A2A3E]">
                  <span className="text-zinc-400 block text-[10px]">Idempotency</span>
                  <span className="font-semibold text-emerald-400">SHA-256 Redis TTL</span>
                </div>
                <div className="p-2 rounded-xl bg-[#1E1E2E] border border-[#2A2A3E]">
                  <span className="text-zinc-400 block text-[10px]">Concurrency</span>
                  <span className="font-semibold text-cyan-400">with_for_update() Row Locks</span>
                </div>
                <div className="p-2 rounded-xl bg-[#1E1E2E] border border-[#2A2A3E]">
                  <span className="text-zinc-400 block text-[10px]">Failure Recovery</span>
                  <span className="font-semibold text-purple-400">3-Phase Saga Rollback</span>
                </div>
                <div className="p-2 rounded-xl bg-[#1E1E2E] border border-[#2A2A3E]">
                  <span className="text-zinc-400 block text-[10px]">Guardrails</span>
                  <span className="font-semibold text-rose-400">Prompt Injection Filter</span>
                </div>
              </div>
            </div>
          </div>
        ) : logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-center">
            <Brain className="h-8 w-8 text-zinc-700 mb-2.5 animate-pulse" />
            <p className="text-xs sm:text-sm font-medium text-zinc-400">No decisions recorded yet</p>
            <p className="text-[11px] text-zinc-600 mt-0.5 max-w-xs">
              Chat or search to view the agent&apos;s real-time reasoning.
            </p>
          </div>
        ) : (
          logs.map((log, index) => {
            const formattedTime = log.timestamp
              ? new Date(log.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })
              : `Step ${index + 1}`;

            return (
              <div
                key={index}
                className="relative flex gap-3 rounded-2xl border border-[#2A2A3E] bg-[#12121E] p-3 transition hover:border-[#7C3AED]/30"
              >
                <div className="flex flex-col items-center">
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-xl bg-[#1E1E2E] border border-[#2A2A3E]">
                    {getActionIcon(log.action)}
                  </div>
                  {index !== logs.length - 1 && <div className="mt-2 w-0.5 flex-1 bg-[#2A2A3E]" />}
                </div>

                <div className="flex-1 space-y-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <span
                      className={`inline-flex items-center rounded-md border px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider ${getActionBadgeColor(
                        log.action
                      )}`}
                    >
                      {log.action.replace(/_/g, " ")}
                    </span>
                    <span className="text-[10px] font-mono text-zinc-500 shrink-0">{formattedTime}</span>
                  </div>

                  <p className="text-xs text-zinc-300 leading-relaxed break-words">{log.reasoning}</p>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Footer Info */}
      <div className="border-t border-[#2A2A3E] bg-[#0A0A12] px-4 py-2.5 text-[10px] text-zinc-500 flex items-center justify-between">
        <span className="flex items-center gap-1 text-emerald-400">
          <ShieldCheck className="h-3 w-3" /> Audited in PostgreSQL
        </span>
        <span className="font-mono text-zinc-400">OTel Dynamic Instrumentation</span>
      </div>
    </div>
  );
}
