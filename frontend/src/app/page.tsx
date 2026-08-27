"use client";

import React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Sparkles,
  MessageSquare,
  ShieldCheck,
  Zap,
  TrendingUp,
  CreditCard,
  ShoppingBag,
  ArrowRight,
  Lock,
  Smartphone,
  CheckCircle2,
  Terminal,
} from "lucide-react";
import { ParticleConstellation } from "@/components/ParticleConstellation";
import { LiquidMetalButton } from "@/components/ui/liquid-metal-button";

export default function HomePage() {
  const router = useRouter();

  const handleLaunchStore = () => {
    router.push("/chat");
  };

  return (
    <div className="relative min-h-screen bg-[#000000] text-zinc-100 selection:bg-[#3395FF] selection:text-white overflow-x-hidden font-sans">
      {/* 3D Particle Constellation Galaxy Background */}
      <ParticleConstellation />

      {/* Top Ambient Glow Gradient */}
      <div className="pointer-events-none fixed top-0 left-1/2 -translate-x-1/2 h-[420px] w-[850px] bg-gradient-to-tr from-[#3395FF]/10 via-[#00C0F9]/10 to-[#02042B]/40 blur-[150px] rounded-full z-0" />

      {/* Navigation Bar */}
      <header className="relative z-20 border-b border-zinc-800/60 bg-black/60 backdrop-blur-xl sticky top-0">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          {/* Logo & Brand */}
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-[#3395FF] to-[#00C0F9] text-white shadow-lg shadow-[#3395FF]/20">
              <Sparkles className="h-5 w-5" />
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <span className="text-base font-bold tracking-tight text-white font-sans">
                  MerchantMind
                </span>
                <span className="rounded-full border border-[#3395FF]/30 bg-[#3395FF]/10 px-2 py-0.5 text-[10px] font-semibold text-[#00C0F9]">
                  Razorpay AI
                </span>
              </div>
            </div>
          </div>

          {/* Navigation Links & Liquid Metal Button */}
          <div className="flex items-center gap-4">
            <Link
              href="#features"
              className="hidden text-xs font-medium text-zinc-400 hover:text-white transition sm:block"
            >
              Architecture
            </Link>
            <Link
              href="#metrics"
              className="hidden text-xs font-medium text-zinc-400 hover:text-white transition sm:block"
            >
              Impact Metrics
            </Link>
            <Link
              href="/chat"
              className="flex items-center gap-1.5 text-xs font-medium text-zinc-300 hover:text-[#00C0F9] transition"
            >
              <span>Demo Store</span>
              <ArrowRight className="h-3 w-3" />
            </Link>

            <LiquidMetalButton
              label="Launch Store"
              onClick={handleLaunchStore}
            />
          </div>
        </div>
      </header>

      {/* Hero Section — Razorpay Vulcan Inspired */}
      <main className="relative z-10 mx-auto max-w-6xl px-6 pt-20 pb-28 text-center">
        {/* Category Super-title */}
        <div className="inline-flex items-center gap-2 rounded-full border border-zinc-800 bg-zinc-950/80 px-4 py-1.5 text-xs font-semibold text-zinc-300 backdrop-blur-md shadow-inner">
          <span className="flex h-2 w-2 rounded-full bg-[#00C0F9] animate-pulse" />
          <span className="tracking-widest uppercase text-[11px] text-[#00C0F9]">
            Razorpay Track 01 • AI Growth & Agentic Commerce
          </span>
        </div>

        {/* Main Editorial Headline */}
        <h1 className="mt-10 text-5xl font-normal tracking-tight sm:text-7xl lg:text-8xl leading-[1.08] text-white">
          Step into the world of{" "}
          <span className="italic font-serif font-light text-zinc-300 block sm:inline">
            agentic payments.
          </span>
        </h1>

        {/* Secondary Editorial Question Subhead */}
        <p className="mt-8 mx-auto max-w-3xl text-xl sm:text-2xl font-light text-zinc-300 leading-relaxed font-serif italic">
          &ldquo;What if one autonomous AI model could understand store catalogs, customer intent, smart upselling, and checkout as a whole?&rdquo;
        </p>

        {/* Description Body */}
        <p className="mt-4 mx-auto max-w-2xl text-sm sm:text-base text-zinc-400 leading-relaxed">
          MerchantMind converts static digital catalogs into high-converting AI shopping agents. Customers browse in natural language with budget-bounded reasoning, discover smart complementary pairings, and complete Razorpay payments in 1 click across Web and WhatsApp.
        </p>

        {/* Hero Interactive CTAs */}
        <div className="mt-12 flex flex-wrap items-center justify-center gap-5">
          <LiquidMetalButton
            label="Try Live Checkout"
            onClick={handleLaunchStore}
          />
          <Link
            href="/chat"
            className="flex items-center gap-2 rounded-full border border-zinc-800 bg-zinc-950/80 px-6 py-3.5 text-xs font-semibold text-zinc-300 backdrop-blur-md transition hover:border-zinc-700 hover:text-white hover:bg-zinc-900 active:scale-95"
          >
            <MessageSquare className="h-4 w-4 text-[#3395FF]" />
            <span>Open Conversational Chat</span>
          </Link>
        </div>

        {/* Bento Metrics Grid Inspired by Razorpay Foundation Model */}
        <div id="metrics" className="mt-28 grid grid-cols-1 gap-4 text-left sm:grid-cols-2 lg:grid-cols-4">
          {/* Metric Card 1 */}
          <div className="relative overflow-hidden rounded-2xl border border-zinc-800/90 bg-zinc-950/70 p-6 backdrop-blur-md transition-all hover:border-[#3395FF]/50 hover:shadow-lg hover:shadow-[#3395FF]/5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#3395FF]/10 text-[#3395FF]">
              <TrendingUp className="h-5 w-5" />
            </div>
            <div className="mt-5 text-3xl font-light tracking-tight text-white font-serif">
              35% More
            </div>
            <p className="mt-1 text-xs font-semibold uppercase tracking-wider text-[#00C0F9]">
              Average Order Value
            </p>
            <p className="mt-2 text-xs text-zinc-400 leading-relaxed">
              Autonomous context-aware pairing suggests complementary items within stated budgets.
            </p>
          </div>

          {/* Metric Card 2 */}
          <div className="relative overflow-hidden rounded-2xl border border-zinc-800/90 bg-zinc-950/70 p-6 backdrop-blur-md transition-all hover:border-[#3395FF]/50 hover:shadow-lg hover:shadow-[#3395FF]/5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-400">
              <Zap className="h-5 w-5" />
            </div>
            <div className="mt-5 text-3xl font-light tracking-tight text-white font-serif">
              &lt; 400ms
            </div>
            <p className="mt-1 text-xs font-semibold uppercase tracking-wider text-emerald-400">
              Agent Inference Time
            </p>
            <p className="mt-2 text-xs text-zinc-400 leading-relaxed">
              Powered by Groq Llama 3.3 70B with instant model fallback and token streaming.
            </p>
          </div>

          {/* Metric Card 3 */}
          <div className="relative overflow-hidden rounded-2xl border border-zinc-800/90 bg-zinc-950/70 p-6 backdrop-blur-md transition-all hover:border-[#3395FF]/50 hover:shadow-lg hover:shadow-[#3395FF]/5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-purple-500/10 text-purple-400">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div className="mt-5 text-3xl font-light tracking-tight text-white font-serif">
              100% Guardrails
            </div>
            <p className="mt-1 text-xs font-semibold uppercase tracking-wider text-purple-400">
              Budget & Safety Compliance
            </p>
            <p className="mt-2 text-xs text-zinc-400 leading-relaxed">
              Hard validation blocks overspending with full chronological audit logging.
            </p>
          </div>

          {/* Metric Card 4 */}
          <div className="relative overflow-hidden rounded-2xl border border-zinc-800/90 bg-zinc-950/70 p-6 backdrop-blur-md transition-all hover:border-[#3395FF]/50 hover:shadow-lg hover:shadow-[#3395FF]/5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#00C0F9]/10 text-[#00C0F9]">
              <Smartphone className="h-5 w-5" />
            </div>
            <div className="mt-5 text-3xl font-light tracking-tight text-white font-serif">
              550M+ Reach
            </div>
            <p className="mt-1 text-xs font-semibold uppercase tracking-wider text-[#00C0F9]">
              WhatsApp Commerce
            </p>
            <p className="mt-2 text-xs text-zinc-400 leading-relaxed">
              Native Meta Cloud API v21.0 conversational checkout and dormant customer campaigns.
            </p>
          </div>
        </div>

        {/* Feature Architectural Pillars */}
        <div id="features" className="mt-32 text-left">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <span className="text-xs font-bold tracking-widest uppercase text-[#3395FF]">
              Core Agent Architecture
            </span>
            <h2 className="mt-3 text-3xl sm:text-4xl font-normal font-serif text-white">
              Engineered for Enterprise Razorpay Merchants
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Pillar 1 */}
            <div className="rounded-3xl border border-zinc-800/90 bg-zinc-950/80 p-8 backdrop-blur-md flex flex-col justify-between">
              <div>
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#3395FF]/10 text-[#3395FF] border border-[#3395FF]/20">
                  <MessageSquare className="h-6 w-6" />
                </div>
                <h3 className="mt-6 text-lg font-bold text-white">
                  Conversational Checkout
                </h3>
                <p className="mt-3 text-xs text-zinc-400 leading-relaxed">
                  Natural language catalog search with budget limits, dietary preferences, and flavor intent. The agent provides transparent reasoning for every recommendation.
                </p>
              </div>
              <div className="mt-6 pt-6 border-t border-zinc-900 flex items-center gap-2 text-xs font-medium text-[#00C0F9]">
                <CheckCircle2 className="h-4 w-4" />
                <span>Multi-turn Cart Function Calling</span>
              </div>
            </div>

            {/* Pillar 2 */}
            <div className="rounded-3xl border border-zinc-800/90 bg-zinc-950/80 p-8 backdrop-blur-md flex flex-col justify-between">
              <div>
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <CreditCard className="h-6 w-6" />
                </div>
                <h3 className="mt-6 text-lg font-bold text-white">
                  Razorpay Payments & Webhooks
                </h3>
                <p className="mt-3 text-xs text-zinc-400 leading-relaxed">
                  Automated Razorpay Order generation and instant payment link delivery. Signed HMAC-SHA256 webhooks capture captures and confirm orders in real time.
                </p>
              </div>
              <div className="mt-6 pt-6 border-t border-zinc-900 flex items-center gap-2 text-xs font-medium text-emerald-400">
                <CheckCircle2 className="h-4 w-4" />
                <span>256-Bit Encrypted Settlement</span>
              </div>
            </div>

            {/* Pillar 3 */}
            <div className="rounded-3xl border border-zinc-800/90 bg-zinc-950/80 p-8 backdrop-blur-md flex flex-col justify-between">
              <div>
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
                  <Lock className="h-6 w-6" />
                </div>
                <h3 className="mt-6 text-lg font-bold text-white">
                  Guardrails & Immutable Audit
                </h3>
                <p className="mt-3 text-xs text-zinc-400 leading-relaxed">
                  Every decision, budget check, tool execution, and webhook is logged with reasoning to PostgreSQL. Queryable via <code className="text-[#00C0F9]">GET /api/orders/&#123;id&#125;/audit</code>.
                </p>
              </div>
              <div className="mt-6 pt-6 border-t border-zinc-900 flex items-center gap-2 text-xs font-medium text-purple-400">
                <CheckCircle2 className="h-4 w-4" />
                <span>Zero Hallucination Guardrails</span>
              </div>
            </div>
          </div>
        </div>

        {/* CTA Footer Banner */}
        <div className="mt-32 rounded-3xl border border-[#3395FF]/30 bg-gradient-to-br from-[#0C2340]/60 to-zinc-950/80 p-10 sm:p-14 text-center backdrop-blur-xl relative overflow-hidden">
          <div className="relative z-10 max-w-2xl mx-auto">
            <h3 className="text-3xl sm:text-4xl font-normal font-serif text-white">
              Ready to experience autonomous commerce?
            </h3>
            <p className="mt-4 text-sm text-zinc-400 leading-relaxed">
              Launch our live demonstration store and experience natural language shopping, smart upselling, and Razorpay checkout in action.
            </p>
            <div className="mt-8 flex justify-center">
              <LiquidMetalButton
                label="Launch Live Store"
                onClick={handleLaunchStore}
              />
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 border-t border-zinc-900 bg-black py-8 text-center text-xs text-zinc-600">
        <div className="mx-auto max-w-7xl px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Sparkles className="h-3.5 w-3.5 text-[#3395FF]" />
            <span className="font-semibold text-zinc-400">MerchantMind</span>
            <span>— Razorpay AI Buildathon 2026</span>
          </div>
          <div className="flex items-center gap-6 text-zinc-500">
            <span>Track 01: AI Growth</span>
            <span>MIT License</span>
            <Link href="/chat" className="text-[#3395FF] hover:underline">
              Demo Store
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
