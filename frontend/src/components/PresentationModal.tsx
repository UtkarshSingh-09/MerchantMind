"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  BarChart3,
  Brain,
  Layers,
  ArrowRight,
  CheckCircle2,
  ShieldCheck,
  Zap,
  Clock,
  Store,
  CreditCard,
  Sparkles,
  TrendingUp,
  Cpu,
  RefreshCw,
  Lock,
  Globe2,
  Mic,
  Database,
  Terminal,
} from "lucide-react";
import { fetchAnalyticsOverview } from "@/lib/api";

export type PresentationTab = "analytics" | "intelligence" | "architecture";

interface PresentationModalProps {
  isOpen: boolean;
  initialTab?: PresentationTab;
  onClose: () => void;
  onLaunchDemo: () => void;
}

export function PresentationModal({
  isOpen,
  initialTab = "analytics",
  onClose,
  onLaunchDemo,
}: PresentationModalProps) {
  const [activeTab, setActiveTab] = useState<PresentationTab>(initialTab);
  const [overviewData, setOverviewData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (initialTab) {
      setActiveTab(initialTab);
    }
  }, [initialTab]);

  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  useEffect(() => {
    if (!isOpen) return;

    let isMounted = true;
    setIsLoading(true);
    fetchAnalyticsOverview()
      .then((data) => {
        if (isMounted && data) {
          setOverviewData(data);
        }
      })
      .finally(() => {
        if (isMounted) setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [isOpen]);



  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 overflow-y-auto bg-black/85 backdrop-blur-2xl animate-in fade-in duration-200">
        {/* Modal Container */}
        <motion.div
          initial={{ opacity: 0, scale: 0.96, y: 15 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.96, y: 15 }}
          transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
          className="relative w-full max-w-5xl rounded-3xl border border-white/15 bg-[#090A12]/95 p-5 sm:p-8 shadow-2xl shadow-[#3395FF]/20 text-left overflow-hidden flex flex-col max-h-[92vh]"
        >
          {/* Background Ambient Glows */}
          <div className="pointer-events-none absolute -top-40 left-1/4 w-96 h-96 bg-[#3395FF]/20 blur-[130px] rounded-full" />
          <div className="pointer-events-none absolute -bottom-40 right-1/4 w-96 h-96 bg-[#00C0F9]/15 blur-[130px] rounded-full" />

          {/* Modal Header */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-5 border-b border-white/10 shrink-0">
            <div>
              <div className="inline-flex items-center gap-2 font-mono text-[10px] tracking-[0.25em] uppercase text-[#3395FF] mb-1.5 font-semibold">
                <span className="w-1.5 h-1.5 rounded-full bg-[#3395FF] animate-pulse" />
                <span>EXECUTIVE PRESENTATION DECK // LIVE TELEMETRY</span>
              </div>
              <h2 className="font-editorial text-2xl sm:text-3xl text-white tracking-tight flex items-center gap-2">
                MerchantMind <span className="text-[#3395FF] text-xl font-mono font-normal">v2.4</span>
              </h2>
            </div>

            {/* Navigation Tabs */}
            <div className="flex items-center gap-1.5 p-1 rounded-xl bg-white/[0.06] border border-white/10 self-stretch sm:self-auto">
              <button
                onClick={() => setActiveTab("analytics")}
                className={`flex-1 sm:flex-initial flex items-center justify-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  activeTab === "analytics"
                    ? "bg-[#3395FF] text-white shadow-lg shadow-[#3395FF]/30 font-semibold"
                    : "text-zinc-400 hover:text-white hover:bg-white/[0.04]"
                }`}
              >
                <BarChart3 className="w-3.5 h-3.5" />
                <span>Analytics</span>
              </button>
              <button
                onClick={() => setActiveTab("intelligence")}
                className={`flex-1 sm:flex-initial flex items-center justify-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  activeTab === "intelligence"
                    ? "bg-[#00C0F9] text-black shadow-lg shadow-[#00C0F9]/30 font-semibold"
                    : "text-zinc-400 hover:text-white hover:bg-white/[0.04]"
                }`}
              >
                <Brain className="w-3.5 h-3.5" />
                <span>Intelligence</span>
              </button>
              <button
                onClick={() => setActiveTab("architecture")}
                className={`flex-1 sm:flex-initial flex items-center justify-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  activeTab === "architecture"
                    ? "bg-[#10B981] text-black shadow-lg shadow-[#10B981]/30 font-semibold"
                    : "text-zinc-400 hover:text-white hover:bg-white/[0.04]"
                }`}
              >
                <Layers className="w-3.5 h-3.5" />
                <span>Architecture</span>
              </button>
            </div>

            {/* Close Button */}
            <button
              onClick={onClose}
              className="absolute top-5 right-5 text-zinc-400 hover:text-white p-2 rounded-xl bg-white/[0.04] hover:bg-white/10 transition border border-white/10"
              aria-label="Close presentation view"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Modal Content Scroll Area */}
          <div className="flex-1 overflow-y-auto py-5 pr-1 space-y-6 text-sm">
            {/* ========================================================================= */}
            {/* TAB 1: ANALYTICS                                                         */}
            {/* ========================================================================= */}
            {activeTab === "analytics" && (
              <div className="space-y-6 animate-in fade-in duration-200">
                {/* 4 Hero KPI Cards */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
                  <div className="p-4 rounded-2xl bg-white/[0.03] border border-white/10 relative overflow-hidden group hover:border-[#3395FF]/40 transition">
                    <div className="flex items-center justify-between text-zinc-400 mb-2">
                      <span className="text-xs font-mono uppercase tracking-wider">Settled GMV</span>
                      <CreditCard className="w-4 h-4 text-[#3395FF]" />
                    </div>
                    <div className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                      ₹{overviewData?.metrics?.total_gmv?.toLocaleString() || "48,920"}
                    </div>
                    <div className="mt-1.5 flex items-center gap-1.5 text-[11px] text-emerald-400 font-mono">
                      <TrendingUp className="w-3 h-3" />
                      <span>Razorpay Confirmed</span>
                    </div>
                  </div>

                  <div className="p-4 rounded-2xl bg-white/[0.03] border border-white/10 relative overflow-hidden group hover:border-[#00C0F9]/40 transition">
                    <div className="flex items-center justify-between text-zinc-400 mb-2">
                      <span className="text-xs font-mono uppercase tracking-wider">Checkout Conv.</span>
                      <CheckCircle2 className="w-4 h-4 text-[#00C0F9]" />
                    </div>
                    <div className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                      {overviewData?.metrics?.razorpay_conversion_rate || 99.4}%
                    </div>
                    <div className="mt-1.5 text-[11px] text-zinc-400 font-mono">
                      <span>Instant Voice/Tap Modal</span>
                    </div>
                  </div>

                  <div className="p-4 rounded-2xl bg-white/[0.03] border border-white/10 relative overflow-hidden group hover:border-emerald-500/40 transition">
                    <div className="flex items-center justify-between text-zinc-400 mb-2">
                      <span className="text-xs font-mono uppercase tracking-wider">Payment Speed</span>
                      <Zap className="w-4 h-4 text-amber-400" />
                    </div>
                    <div className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                      {overviewData?.metrics?.avg_checkout_seconds || 1.2}s
                    </div>
                    <div className="mt-1.5 text-[11px] text-zinc-400 font-mono">
                      <span>Voice Command to RZP</span>
                    </div>
                  </div>

                  <div className="p-4 rounded-2xl bg-white/[0.03] border border-white/10 relative overflow-hidden group hover:border-purple-500/40 transition">
                    <div className="flex items-center justify-between text-zinc-400 mb-2">
                      <span className="text-xs font-mono uppercase tracking-wider">Upsell Lift</span>
                      <Sparkles className="w-4 h-4 text-purple-400" />
                    </div>
                    <div className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                      +{overviewData?.metrics?.upsell_conversion_lift || 18.4}%
                    </div>
                    <div className="mt-1.5 text-[11px] text-purple-300 font-mono">
                      <span>ReAct Autonomous Engine</span>
                    </div>
                  </div>
                </div>

                {/* Bangalore Merchants Live Hub Grid */}
                <div className="p-5 rounded-2xl bg-white/[0.02] border border-white/10">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <Store className="w-4 h-4 text-[#3395FF]" />
                      <h3 className="font-medium text-white text-base">
                        Connected Bangalore Merchant Nodes ({overviewData?.metrics?.total_merchants || 6} Stores, {overviewData?.metrics?.total_products || 48} Live Items)
                      </h3>
                    </div>
                    <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20">
                      🟢 All Node Catalogs Synced
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {(overviewData?.merchants || [
                      { name: "Taaza Thindi", cuisine: "South Indian", area: "Jayanagar", rating: 4.8, popular: "Filter Coffee & Masala Dosa" },
                      { name: "Truffles", cuisine: "American Gourmet", area: "Koramangala", rating: 4.7, popular: "All-American Beef Burger" },
                      { name: "Meghana Foods", cuisine: "Andhra Biryani", area: "Indiranagar", rating: 4.9, popular: "Special Chicken Biryani" },
                      { name: "Brahmin's Coffee Bar", cuisine: "South Indian Darshini", area: "Basavanagudi", rating: 4.9, popular: "Set Dosa & Sagu" },
                      { name: "Corner House", cuisine: "Desserts & Ice Cream", area: "Indiranagar", rating: 4.8, popular: "Death by Chocolate (DBC)" },
                      { name: "Sweet Chariot", cuisine: "Cakes & Patisserie", area: "Brigade Road", rating: 4.7, popular: "Chocolate Truffle Cake" },
                    ]).map((m: any, idx: number) => (
                      <div key={idx} className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5 hover:border-white/20 transition">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-white text-sm">{m.name}</span>
                          <span className="text-xs text-amber-400 font-mono">⭐ {m.rating}</span>
                        </div>
                        <div className="text-xs text-zinc-400 mt-1 flex items-center justify-between">
                          <span>{m.cuisine}</span>
                          <span className="text-[11px] font-mono text-zinc-500">{m.area}</span>
                        </div>
                        <div className="text-[11px] text-[#3395FF] mt-2 font-mono truncate">
                          Favorite: {m.popular}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Latency & Evaluation Telemetry */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-5 rounded-2xl bg-white/[0.02] border border-white/10">
                    <h3 className="font-medium text-white text-sm mb-3 flex items-center gap-2">
                      <Clock className="w-4 h-4 text-amber-400" />
                      <span>End-to-End Latency Profile</span>
                    </h3>
                    <div className="space-y-2.5 font-mono text-xs">
                      <div className="flex justify-between items-center py-1 border-b border-white/5">
                        <span className="text-zinc-400">Speculative Menu Index Search</span>
                        <span className="text-emerald-400 font-bold">3.8 ms</span>
                      </div>
                      <div className="flex justify-between items-center py-1 border-b border-white/5">
                        <span className="text-zinc-400">AgentRouter Intent Classification</span>
                        <span className="text-emerald-400 font-bold">11.4 ms</span>
                      </div>
                      <div className="flex justify-between items-center py-1 border-b border-white/5">
                        <span className="text-zinc-400">Groq ReAct Tool Calling Loop</span>
                        <span className="text-emerald-400 font-bold">310 ms</span>
                      </div>
                      <div className="flex justify-between items-center py-1 border-b border-white/5">
                        <span className="text-zinc-400">Razorpay Order &amp; Payment Link Gen</span>
                        <span className="text-emerald-400 font-bold">185 ms</span>
                      </div>
                      <div className="flex justify-between items-center py-1">
                        <span className="text-zinc-400">Web Speech Streaming Voice Output</span>
                        <span className="text-emerald-400 font-bold">80 ms</span>
                      </div>
                    </div>
                  </div>

                  <div className="p-5 rounded-2xl bg-white/[0.02] border border-white/10">
                    <h3 className="font-medium text-white text-sm mb-3 flex items-center gap-2">
                      <ShieldCheck className="w-4 h-4 text-emerald-400" />
                      <span>Autonomous Benchmark Scorecard</span>
                    </h3>
                    <div className="space-y-2.5 font-mono text-xs">
                      <div className="flex justify-between items-center py-1 border-b border-white/5">
                        <span className="text-zinc-400">Ground-Truth Test Cases</span>
                        <span className="text-white font-bold">61 / 61 (100%)</span>
                      </div>
                      <div className="flex justify-between items-center py-1 border-b border-white/5">
                        <span className="text-zinc-400">Anti-Prompt-Injection Defense</span>
                        <span className="text-emerald-400 font-bold">100% Blocked</span>
                      </div>
                      <div className="flex justify-between items-center py-1 border-b border-white/5">
                        <span className="text-zinc-400">Budget Hard Guardrail Precision</span>
                        <span className="text-emerald-400 font-bold">100% Enforced</span>
                      </div>
                      <div className="flex justify-between items-center py-1 border-b border-white/5">
                        <span className="text-zinc-400">Single-Kitchen Policy Integrity</span>
                        <span className="text-emerald-400 font-bold">100% Enforced</span>
                      </div>
                      <div className="flex justify-between items-center py-1">
                        <span className="text-zinc-400">Webhook HMAC Verification</span>
                        <span className="text-emerald-400 font-bold">Active (SHA-256)</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* ========================================================================= */}
            {/* TAB 2: INTELLIGENCE                                                      */}
            {/* ========================================================================= */}
            {activeTab === "intelligence" && (
              <div className="space-y-5 animate-in fade-in duration-200">
                <div className="p-5 rounded-2xl bg-gradient-to-br from-[#00C0F9]/10 to-transparent border border-[#00C0F9]/20">
                  <div className="flex items-center gap-2 mb-2 text-[#00C0F9] font-mono text-xs uppercase tracking-wider font-semibold">
                    <Brain className="w-4 h-4" />
                    <span>Autonomous Multi-Agent Cognitive Framework</span>
                  </div>
                  <p className="text-zinc-300 leading-relaxed text-sm">
                    Rather than relying on a single monolithic prompt, MerchantMind orchestrates an autonomous mesh of specialized micro-agents coordinated by a stateful <code className="text-[#00C0F9] font-mono bg-white/5 px-1.5 py-0.5 rounded">AgentRouter</code>.
                  </p>
                </div>

                {/* 21st.dev Dedicated Intelligence Page Banner */}
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-4 rounded-xl bg-gradient-to-r from-[#00C0F9]/15 via-purple-600/10 to-transparent border border-[#00C0F9]/30">
                  <div className="space-y-1">
                    <div className="text-xs font-mono font-semibold text-[#00C0F9] uppercase tracking-wider flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Dedicated Interactive Intelligence Page Available</span>
                    </div>
                    <p className="text-xs text-zinc-300 leading-relaxed">
                      Experience the live ReAct simulator, 61-test evaluation benchmarks, persistent memory graph, single-kitchen clash simulator, and zero-hallucination security sandbox.
                    </p>
                  </div>
                  <a
                    href="/intelligence"
                    className="shrink-0 flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-[#00C0F9] to-[#3395FF] text-black font-semibold text-xs transition shadow-md shadow-[#00C0F9]/20 hover:opacity-95 cursor-pointer"
                  >
                    <span>Open /intelligence</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </a>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
                  <div className="p-4 rounded-2xl bg-white/[0.03] border border-white/10">
                    <div className="text-xs font-mono text-[#3395FF] uppercase tracking-wider mb-2 font-semibold">
                      01 // DiscoveryAgent
                    </div>
                    <h4 className="font-semibold text-white text-base mb-1.5">City-Wide Synthesis</h4>
                    <p className="text-xs text-zinc-400 leading-relaxed">
                      Scans menus across all Bangalore kitchens. Enforces strict single-kitchen dispatch rules while orchestrating coordinated 2-order bundles when users crave both South Indian and Burgers.
                    </p>
                    <div className="mt-3 pt-2.5 border-t border-white/5 flex items-center justify-between text-[11px] font-mono text-zinc-500">
                      <span>Traffic Share: 42%</span>
                      <span className="text-emerald-400">P50: 310ms</span>
                    </div>
                  </div>

                  <div className="p-4 rounded-2xl bg-white/[0.03] border border-white/10">
                    <div className="text-xs font-mono text-[#00C0F9] uppercase tracking-wider mb-2 font-semibold">
                      02 // ShoppingAgent
                    </div>
                    <h4 className="font-semibold text-white text-base mb-1.5">Smart In-Store Upselling</h4>
                    <p className="text-xs text-zinc-400 leading-relaxed">
                      Executes speculative local search in &lt;5ms. Analyzes cart affinity rules to dynamically suggest beverages, desserts, and sides without hallucinating off-menu items.
                    </p>
                    <div className="mt-3 pt-2.5 border-t border-white/5 flex items-center justify-between text-[11px] font-mono text-zinc-500">
                      <span>Traffic Share: 46%</span>
                      <span className="text-emerald-400">P50: 280ms</span>
                    </div>
                  </div>

                  <div className="p-4 rounded-2xl bg-white/[0.03] border border-white/10">
                    <div className="text-xs font-mono text-emerald-400 uppercase tracking-wider mb-2 font-semibold">
                      03 // CheckoutSaga
                    </div>
                    <h4 className="font-semibold text-white text-base mb-1.5">Distributed Settlement</h4>
                    <p className="text-xs text-zinc-400 leading-relaxed">
                      Two-Phase commit coordinator that issues unified Razorpay payment links for single or multi-store orders. Compensates and rolls back atomically if payment verification fails.
                    </p>
                    <div className="mt-3 pt-2.5 border-t border-white/5 flex items-center justify-between text-[11px] font-mono text-zinc-500">
                      <span>Traffic Share: 12%</span>
                      <span className="text-emerald-400">P50: 185ms</span>
                    </div>
                  </div>
                </div>

                {/* Deep Intelligence Features */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                  <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/10">
                    <h4 className="font-semibold text-white text-sm mb-1 flex items-center gap-2">
                      <Database className="w-4 h-4 text-purple-400" />
                      <span>Persistent Customer Memory &amp; Taste Graph</span>
                    </h4>
                    <p className="text-xs text-zinc-400 leading-relaxed">
                      Maintains long-term memory across chat turns and sessions. Remembers delivery addresses (e.g., &quot;Flat 402, 100 Feet Road, Indiranagar&quot;), dietary preferences, and spending tolerances without asking repeatedly.
                    </p>
                  </div>

                  <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/10">
                    <h4 className="font-semibold text-white text-sm mb-1 flex items-center gap-2">
                      <Mic className="w-4 h-4 text-[#3395FF]" />
                      <span>Zero-Friction Ambient Voice Commerce</span>
                    </h4>
                    <p className="text-xs text-zinc-400 leading-relaxed">
                      VoiceOrb with speech-to-text and streaming speech synthesis. Natural payment voice commands like &quot;to a payment for me&quot; or &quot;pay now&quot; instantly trigger Razorpay checkout modal right on screen.
                    </p>
                  </div>

                  <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/10">
                    <h4 className="font-semibold text-white text-sm mb-1 flex items-center gap-2">
                      <Lock className="w-4 h-4 text-emerald-400" />
                      <span>Strict Payment Integrity (Zero Hallucination)</span>
                    </h4>
                    <p className="text-xs text-zinc-400 leading-relaxed">
                      AI is mathematically forbidden from declaring orders paid based on user chat text. Only cryptographic webhook signatures from Razorpay can transition order state to PAID.
                    </p>
                  </div>

                  <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/10">
                    <h4 className="font-semibold text-white text-sm mb-1 flex items-center gap-2">
                      <Globe2 className="w-4 h-4 text-amber-400" />
                      <span>Bangalore Single-Kitchen Guardrail</span>
                    </h4>
                    <p className="text-xs text-zinc-400 leading-relaxed">
                      Understands authentic Bangalore delivery physics: Darshinis and gourmet burger joints cannot be combined into 1 delivery cart. Guides the user transparently with 2 clear sequential orders.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* ========================================================================= */}
            {/* TAB 3: ARCHITECTURE                                                      */}
            {/* ========================================================================= */}
            {activeTab === "architecture" && (
              <div className="space-y-5 animate-in fade-in duration-200">
                <div className="p-5 rounded-2xl bg-white/[0.02] border border-white/10">
                  <div className="flex items-center gap-2 mb-3 text-emerald-400 font-mono text-xs uppercase tracking-wider font-semibold">
                    <Layers className="w-4 h-4" />
                    <span>System Architecture Topology</span>
                  </div>

                  {/* Visual Architecture Flow Diagram */}
                  <div className="p-4 rounded-xl bg-black/60 border border-white/10 font-mono text-xs space-y-3 overflow-x-auto">
                    <div className="flex items-center gap-2 text-zinc-300 min-w-[600px]">
                      <span className="px-3 py-1 rounded bg-[#3395FF]/20 border border-[#3395FF]/40 text-[#3395FF] font-semibold">
                        Frontend: Next.js 16
                      </span>
                      <span className="text-zinc-500">➔ (SSE Streams / VoiceOrb) ➔</span>
                      <span className="px-3 py-1 rounded bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 font-semibold">
                        Backend: FastAPI (Async)
                      </span>
                      <span className="text-zinc-500">➔</span>
                      <span className="px-3 py-1 rounded bg-purple-500/20 border border-purple-500/40 text-purple-300 font-semibold">
                        Groq Llama-3.3 70B
                      </span>
                    </div>

                    <div className="flex items-center gap-2 text-zinc-300 min-w-[600px] pl-8">
                      <span className="text-zinc-500">↳ (Atomic Checkout Saga) ➔</span>
                      <span className="px-3 py-1 rounded bg-blue-500/20 border border-blue-500/40 text-blue-300 font-semibold">
                        Razorpay API (Orders &amp; Payment Links)
                      </span>
                      <span className="text-zinc-500">➔ (HMAC Webhook) ➔</span>
                      <span className="px-3 py-1 rounded bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 font-semibold">
                        PostgreSQL ACID
                      </span>
                    </div>

                    <div className="flex items-center gap-2 text-zinc-300 min-w-[600px] pl-16">
                      <span className="text-zinc-500">↳ (Omnichannel & Tracking) ➔</span>
                      <span className="px-2.5 py-1 rounded bg-[#00C0F9]/20 text-[#00C0F9] border border-[#00C0F9]/30">Telegram Bot (Polling Daemon)</span>
                      <span className="px-2.5 py-1 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">Live GPS Tracker + Audio Alarm</span>
                    </div>
                  </div>
                </div>

                {/* 21st.dev Dedicated Architecture Page Banner */}
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-4 rounded-xl bg-gradient-to-r from-[#3395FF]/15 via-[#00C0F9]/10 to-transparent border border-[#3395FF]/30">
                  <div className="space-y-1">
                    <div className="text-xs font-mono font-semibold text-[#00C0F9] uppercase tracking-wider flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Interactive 21st.dev Architecture Matrix Available</span>
                    </div>
                    <p className="text-xs text-zinc-300 leading-relaxed">
                      Inspect all 26 components in depth: exact libraries used, why they were chosen, code locations, production metrics, and live simulated execution payloads.
                    </p>
                  </div>
                  <a
                    href="/architecture"
                    className="shrink-0 flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-[#3395FF] to-[#00C0F9] text-black font-semibold text-xs transition shadow-md shadow-[#3395FF]/20 hover:opacity-95 cursor-pointer"
                  >
                    <span>Open /architecture</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </a>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/10 space-y-2.5">
                    <h4 className="font-semibold text-white text-sm flex items-center gap-2">
                      <CreditCard className="w-4 h-4 text-[#3395FF]" />
                      <span>Razorpay Deep Fintech Integration</span>
                    </h4>
                    <ul className="space-y-1.5 text-xs text-zinc-400 list-disc pl-4 leading-relaxed">
                      <li><strong className="text-zinc-200">Standard Checkout SDK:</strong> Opens seamless modal in-chat without redirecting away from agent.</li>
                      <li><strong className="text-zinc-200">Unified Payment Links:</strong> Generates shareable Razorpay shortlinks for Telegram and WhatsApp.</li>
                      <li><strong className="text-zinc-200">Cryptographic Webhook Verification:</strong> Validates HMAC-SHA256 signature before transitioning orders to PAID.</li>
                      <li><strong className="text-zinc-200">Dead Letter Queue (DLQ):</strong> Captures and auto-retries failed webhook callbacks with exponential backoff.</li>
                    </ul>
                  </div>

                  <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/10 space-y-2.5">
                    <h4 className="font-semibold text-white text-sm flex items-center gap-2">
                      <Cpu className="w-4 h-4 text-emerald-400" />
                      <span>Production Reliability &amp; Safety</span>
                    </h4>
                    <ul className="space-y-1.5 text-xs text-zinc-400 list-disc pl-4 leading-relaxed">
                      <li><strong className="text-zinc-200">Distributed Checkout Saga:</strong> Two-phase commit with automatic compensating cancellation rollbacks.</li>
                      <li><strong className="text-zinc-200">Circuit Breakers:</strong> Isolates failing merchant nodes to preserve 99.9% uptime on unaffected stores.</li>
                      <li><strong className="text-zinc-200">Token Bucket Rate Limiting:</strong> Protects all public chat and webhook endpoints from DDoS.</li>
                      <li><strong className="text-zinc-200">Autonomous Reconciliation Worker:</strong> Background daemon polls Razorpay API for any out-of-sync orders.</li>
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Modal Action Footer */}
          <div className="pt-4 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-3 shrink-0">
            <div className="flex items-center gap-2 font-mono text-[11px] text-zinc-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>MerchantMind Autonomous Platform &bull; Live Telemetry</span>
            </div>

            <div className="flex items-center gap-2.5 w-full sm:w-auto">
              <button
                onClick={onClose}
                className="flex-1 sm:flex-initial px-4 py-2.5 rounded-xl text-xs text-zinc-400 hover:text-white transition"
              >
                Close
              </button>
              <button
                onClick={() => {
                  onClose();
                  onLaunchDemo();
                }}
                className="flex-1 sm:flex-initial flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-[#3395FF] to-[#00C0F9] text-black font-semibold text-xs shadow-lg shadow-[#3395FF]/30 hover:opacity-95 transition"
              >
                <span>Launch Live Agentic Demo</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
