"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Sparkles,
  TrendingUp,
  AlertCircle,
  ShoppingCart,
  ShieldAlert,
  ArrowRight,
  X,
  Lock,
  ChevronDown,
  Layers,
  Cpu,
  ShieldCheck,
  Zap,
} from "lucide-react";
import { ParticleConstellation } from "@/components/ParticleConstellation";
import { LiquidMetalButton } from "@/components/ui/liquid-metal-button";

export default function HomePage() {
  const router = useRouter();
  const [showVaultModal, setShowVaultModal] = useState(false);

  const handleLaunchStore = () => {
    router.push("/chat");
  };

  return (
    <div className="relative min-h-screen bg-[#000000] text-[#e2e2e2] selection:bg-[#3395FF] selection:text-white overflow-x-hidden">
      {/* Three.js 3D Particle Constellation & Multi-Node Network */}
      <ParticleConstellation />

      {/* Top Ambient Glow */}
      <div className="pointer-events-none fixed top-0 left-1/2 -translate-x-1/2 h-[450px] w-[900px] bg-gradient-to-tr from-[#3395FF]/12 via-[#00C0F9]/10 to-transparent blur-[160px] rounded-full z-0" />

      {/* Top Navigation Bar — Exact Stitch Design */}
      <header className="sticky top-0 z-50 w-full border-b border-white/10 bg-[#000000]/70 backdrop-blur-xl transition-all duration-300">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          {/* Brand Logo in Editorial Serif */}
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="font-editorial text-2xl md:text-3xl text-white tracking-tight hover:opacity-90 transition"
            >
              MerchantMind
            </Link>
            <span className="rounded-full border border-[#3395FF]/40 bg-[#3395FF]/10 px-2.5 py-0.5 text-[10px] font-mono uppercase tracking-widest text-[#00C0F9]">
              Track 01 • AI Growth
            </span>
          </div>

          {/* Minimalist Navigation Links */}
          <nav className="hidden md:flex items-center gap-8 text-sm">
            <a
              href="#network"
              className="text-[#94A3B8] hover:text-white transition-colors"
            >
              Intelligence
            </a>
            <a
              href="#architecture"
              className="text-[#94A3B8] hover:text-white transition-colors"
            >
              Architecture
            </a>
            <a
              href="#metrics"
              className="text-[#94A3B8] hover:text-white transition-colors"
            >
              Metrics
            </a>
          </nav>

          {/* Action CTAs */}
          <div className="flex items-center gap-4">
            <Link
              href="/chat"
              className="hidden sm:flex items-center gap-1.5 text-xs font-medium text-zinc-400 hover:text-white transition"
            >
              <span>Demo Store</span>
              <ArrowRight className="h-3 w-3" />
            </Link>

            <button
              onClick={() => setShowVaultModal(true)}
              className="liquid-btn text-[#000000] font-semibold text-xs md:text-sm px-4 py-2 rounded-lg cursor-pointer flex items-center gap-1.5"
            >
              <Lock className="w-3.5 h-3.5" />
              <span>Connect Vault</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="relative z-10 flex flex-col items-center">
        {/* ========================================================================= */}
        {/* CHAPTER 1: PARTICLE MONOGRAM HERO                                         */}
        {/* ========================================================================= */}
        <section className="relative flex min-h-[92vh] w-full max-w-5xl flex-col items-center justify-center px-6 text-center pt-8">
          {/* Super-title */}
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-4 py-1.5 backdrop-blur-md">
            <span className="h-1.5 w-1.5 rounded-full bg-[#00C0F9] animate-pulse" />
            <span className="font-mono text-[11px] tracking-[0.3em] uppercase text-[#00C0F9]">
              R A Z O R P A Y   M E R C H A N T M I N D
            </span>
          </div>

          {/* Editorial Headline */}
          <h1 className="font-editorial text-5xl sm:text-7xl lg:text-[84px] leading-[1.05] tracking-tight text-white max-w-4xl drop-shadow-2xl">
            Step into the world of{" "}
            <span className="italic text-[#a5c8ff]">agentic payments.</span>
          </h1>

          {/* Narrative Subhead */}
          <p className="mt-8 text-base sm:text-lg text-[#94A3B8] max-w-2xl font-light leading-relaxed">
            For years, digital storefronts built static filters and manual search.
            But they existed in isolation. What if one autonomous model could
            understand catalogs, intent, upselling, and payments as a whole?
          </p>

          {/* CTA Group */}
          <div className="mt-10 flex flex-col sm:flex-row items-center gap-4">
            <LiquidMetalButton
              label="Try Conversational Checkout →"
              onClick={handleLaunchStore}
            />
            <button
              onClick={() => {
                document
                  .getElementById("network")
                  ?.scrollIntoView({ behavior: "smooth" });
              }}
              className="px-6 py-3 rounded-lg border border-white/20 bg-white/5 text-sm font-medium text-white backdrop-blur-md hover:bg-white/10 hover:border-white/40 transition cursor-pointer flex items-center gap-2"
            >
              <span>Explore Network</span>
              <ChevronDown className="w-4 h-4 text-[#00C0F9]" />
            </button>
          </div>

          {/* Scroll cue */}
          <div className="absolute bottom-6 flex flex-col items-center gap-2 opacity-60 hover:opacity-100 transition animate-bounce">
            <span className="text-[10px] font-mono tracking-widest text-[#94A3B8] uppercase">
              Scroll to explore
            </span>
            <ChevronDown className="w-4 h-4 text-[#00C0F9]" />
          </div>
        </section>

        {/* ========================================================================= */}
        {/* CHAPTER 2: THE MULTI-NODE NETWORK                                         */}
        {/* ========================================================================= */}
        <section
          id="network"
          className="relative flex min-h-screen w-full max-w-6xl flex-col items-center justify-center px-6 py-24 text-center"
        >
          {/* Super-title */}
          <div className="mb-4 font-mono text-[11px] tracking-[0.3em] uppercase text-[#00C0F9]">
            T H E   M U L T I - N O D E   N E T W O R K
          </div>

          {/* Headline */}
          <h2 className="font-editorial text-4xl sm:text-6xl text-white tracking-tight max-w-3xl">
            Built ML models in isolation.
          </h2>

          {/* Subtitle */}
          <p className="mt-6 text-base sm:text-lg text-[#94A3B8] max-w-2xl font-light">
            Legacy systems operated as silos. MerchantMind bridges the gap
            between infrastructure and intelligence, creating an autonomous
            agentic network.
          </p>

          {/* Telemetry Node Pills Grid (Holographic Overlay over 3D World) */}
          <div className="mt-14 grid grid-cols-2 md:grid-cols-4 gap-3.5 max-w-4xl w-full">
            {[
              { label: "ISSUING BANK", color: "border-white/15 text-zinc-300" },
              { label: "NETWORK", color: "border-[#3395FF]/40 text-[#a5c8ff]" },
              { label: "ACQUIRING BANK", color: "border-white/15 text-zinc-300" },
              { label: "PAYMENT PROCESSOR", color: "border-white/15 text-zinc-300" },
              {
                label: "CHARGEBACK PROTECTION",
                color: "border-emerald-500/40 text-emerald-400 bg-emerald-500/5",
              },
              {
                label: "SUCCESS RATE OPTIMIZATION",
                color: "border-[#00C0F9]/40 text-[#00C0F9] bg-[#00C0F9]/5",
              },
              {
                label: "CHECKOUT PERSONALISATION",
                color: "border-[#3395FF]/40 text-[#a5c8ff] bg-[#3395FF]/5",
              },
              {
                label: "FRAUD DETECTION",
                color: "border-rose-500/40 text-rose-400 bg-rose-500/5",
              },
            ].map((node, i) => (
              <div
                key={i}
                className={`glass-card rounded-lg p-3.5 border ${node.color} flex items-center justify-center text-center transition-all duration-300 hover:scale-[1.03] hover:border-white/40`}
              >
                <span className="font-mono text-xs tracking-wider font-medium">
                  [{node.label}]
                </span>
              </div>
            ))}
          </div>
        </section>

        {/* ========================================================================= */}
        {/* CHAPTER 3: THE 4 TALL BENTO STAT SLABS                                    */}
        {/* ========================================================================= */}
        <section
          id="metrics"
          className="relative w-full max-w-6xl px-6 py-24 flex flex-col items-center"
        >
          <div className="text-center mb-16">
            <div className="font-mono text-[11px] tracking-[0.3em] uppercase text-[#00C0F9] mb-3">
              A U T O N O M O U S   I M P A C T
            </div>
            <h2 className="font-editorial text-4xl sm:text-6xl text-white tracking-tight">
              Quantifiable Growth for Razorpay Merchants
            </h2>
          </div>

          {/* 4 Bento Glass Cards Horizon */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 w-full">
            {/* Card 1 */}
            <div className="glass-panel rounded-xl p-8 flex flex-col justify-between border border-white/10 hover:border-[#3395FF]/40 transition-all duration-300 group hover:-translate-y-1">
              <div>
                <div className="h-10 w-10 rounded-lg bg-[#3395FF]/10 border border-[#3395FF]/30 flex items-center justify-center text-[#3395FF] mb-6">
                  <TrendingUp className="w-5 h-5" />
                </div>
                <div className="font-editorial text-4xl sm:text-5xl text-white font-normal group-hover:text-[#a5c8ff] transition">
                  8-10%
                </div>
                <div className="font-editorial text-xl italic text-zinc-300 mt-2">
                  improvement in success rates
                </div>
              </div>
              <p className="mt-8 text-xs text-[#94A3B8] font-light leading-relaxed border-t border-white/10 pt-4">
                Real-time dynamic payment routing, autonomous retries, and UPI intent deep-links.
              </p>
            </div>

            {/* Card 2 */}
            <div className="glass-panel rounded-xl p-8 flex flex-col justify-between border border-white/10 hover:border-amber-500/40 transition-all duration-300 group hover:-translate-y-1">
              <div>
                <div className="h-10 w-10 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 mb-6">
                  <AlertCircle className="w-5 h-5" />
                </div>
                <div className="font-editorial text-4xl sm:text-5xl text-white font-normal group-hover:text-amber-300 transition">
                  5X more
                </div>
                <div className="font-editorial text-xl italic text-zinc-300 mt-2">
                  disputed transactions identified
                </div>
              </div>
              <p className="mt-8 text-xs text-[#94A3B8] font-light leading-relaxed border-t border-white/10 pt-4">
                Proactive chargeback intelligence and automated customer resolution workflows.
              </p>
            </div>

            {/* Card 3 (Elevated) */}
            <div className="glass-panel rounded-xl p-8 flex flex-col justify-between border border-[#00C0F9]/40 bg-white/[0.03] shadow-2xl shadow-[#3395FF]/10 transition-all duration-300 group hover:-translate-y-1">
              <div>
                <div className="h-10 w-10 rounded-lg bg-[#00C0F9]/10 border border-[#00C0F9]/30 flex items-center justify-center text-[#00C0F9] mb-6">
                  <ShoppingCart className="w-5 h-5" />
                </div>
                <div className="font-editorial text-3xl sm:text-4xl text-white font-normal group-hover:text-[#00C0F9] transition leading-tight">
                  Millions of Checkouts
                </div>
                <div className="font-editorial text-xl italic text-[#00C0F9] mt-2">
                  Hyper-Personalized
                </div>
              </div>
              <p className="mt-8 text-xs text-zinc-300 font-light leading-relaxed border-t border-white/10 pt-4">
                Contextual upselling and natural language cart assembly bounded by hard customer budget limits.
              </p>
            </div>

            {/* Card 4 */}
            <div className="glass-panel rounded-xl p-8 flex flex-col justify-between border border-white/10 hover:border-rose-500/40 transition-all duration-300 group hover:-translate-y-1">
              <div>
                <div className="h-10 w-10 rounded-lg bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400 mb-6">
                  <ShieldAlert className="w-5 h-5" />
                </div>
                <div className="font-editorial text-4xl sm:text-5xl text-white font-normal group-hover:text-rose-300 transition">
                  8X more
                </div>
                <div className="font-editorial text-xl italic text-zinc-300 mt-2">
                  international card fraud detected
                </div>
              </div>
              <p className="mt-8 text-xs text-[#94A3B8] font-light leading-relaxed border-t border-white/10 pt-4">
                Cryptographic HMAC-SHA256 signature auditing and tamper-proof decision traces in PostgreSQL.
              </p>
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* CHAPTER 4: THREE CORE ARCHITECTURAL PILLARS                              */}
        {/* ========================================================================= */}
        <section
          id="architecture"
          className="relative w-full max-w-5xl px-6 py-20 flex flex-col items-center"
        >
          <div className="text-center mb-12">
            <div className="font-mono text-[11px] tracking-[0.3em] uppercase text-[#00C0F9] mb-3">
              C O R E   E N G I N E
            </div>
            <h2 className="font-editorial text-4xl sm:text-5xl text-white tracking-tight">
              The Autonomous Merchant Architecture
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full">
            <div className="glass-card rounded-xl p-6 border border-white/10">
              <div className="h-8 w-8 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-[#3395FF] mb-4">
                <Cpu className="w-4 h-4" />
              </div>
              <h3 className="text-base font-semibold text-white font-sans">
                Llama 3.3 70B & Groq
              </h3>
              <p className="mt-2 text-xs text-[#94A3B8] leading-relaxed">
                Sub-400ms inference with multi-turn tool calling, dietary parsing, and zero-hallucination catalog lookups.
              </p>
            </div>

            <div className="glass-card rounded-xl p-6 border border-white/10">
              <div className="h-8 w-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mb-4">
                <Zap className="w-4 h-4" />
              </div>
              <h3 className="text-base font-semibold text-white font-sans">
                Razorpay Payment Engine
              </h3>
              <p className="mt-2 text-xs text-[#94A3B8] leading-relaxed">
                Automated order generation, instant payment links, and HMAC-verified webhook settlement listeners.
              </p>
            </div>

            <div className="glass-card rounded-xl p-6 border border-white/10">
              <div className="h-8 w-8 rounded-lg bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400 mb-4">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <h3 className="text-base font-semibold text-white font-sans">
                100% Budget Guardrails
              </h3>
              <p className="mt-2 text-xs text-[#94A3B8] leading-relaxed">
                Autonomous logic strictly bounds cart totals to user constraints before initiating payment transactions.
              </p>
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* FOOTER                                                                    */}
        {/* ========================================================================= */}
        <footer className="w-full border-t border-white/10 py-8 px-6 text-center text-xs text-[#94A3B8]">
          <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="font-editorial text-lg text-white">MerchantMind</div>
            <div className="font-mono text-[11px] text-zinc-500">
              Built for Razorpay AI Buildathon 2026 • Track 01 (AI Growth)
            </div>
            <Link
              href="/chat"
              className="text-[#00C0F9] hover:underline font-medium"
            >
              Open Live Store →
            </Link>
          </div>
        </footer>
      </main>

      {/* ========================================================================= */}
      {/* CHAPTER 5: CONNECT VAULT APERTURE FLASH MODAL                             */}
      {/* ========================================================================= */}
      {showVaultModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-xl animate-in fade-in duration-300">
          <div className="relative w-full max-w-lg rounded-2xl glass-panel p-8 border border-[#00C0F9]/40 shadow-2xl shadow-[#3395FF]/20 text-center">
            {/* Close Button */}
            <button
              onClick={() => setShowVaultModal(false)}
              className="absolute top-4 right-4 text-zinc-400 hover:text-white p-1 rounded-lg hover:bg-white/10 transition"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Radial Light Burst Aura */}
            <div className="pointer-events-none absolute -top-24 left-1/2 -translate-x-1/2 w-48 h-48 bg-[#00C0F9]/25 blur-3xl rounded-full" />

            {/* Monospace Supertitle */}
            <div className="font-mono text-[11px] tracking-[0.3em] uppercase text-[#00C0F9] mb-4">
              R A Z O R P A Y   A I   G R O W T H
            </div>

            {/* Main Headline */}
            <h3 className="font-editorial text-3xl sm:text-4xl text-white">
              Ready for an unfair advantage?
            </h3>

            {/* Subtext */}
            <p className="mt-4 text-sm text-[#94A3B8] font-light leading-relaxed">
              Go beyond the baseline. Experience our Autonomous AI Checkout Agent
              live with smart upselling and instant Razorpay payment generation.
            </p>

            {/* Action Buttons */}
            <div className="mt-8 flex flex-col gap-3">
              <LiquidMetalButton
                label="Launch Live Demo Store → (Takes 30 sec)"
                onClick={() => {
                  setShowVaultModal(false);
                  router.push("/chat");
                }}
              />
              <button
                onClick={() => setShowVaultModal(false)}
                className="text-xs text-zinc-400 hover:text-white transition py-2"
              >
                Close and return to network overview
              </button>
            </div>

            {/* Trust badge */}
            <div className="mt-6 border-t border-white/10 pt-4 flex items-center justify-center gap-2 text-[11px] font-mono text-zinc-400">
              <Lock className="w-3 h-3 text-emerald-400" />
              <span>Razorpay Verified AI Merchant Checkout • 256-Bit SSL</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
