import Link from "next/link";
import { Sparkles, MessageSquare, ShoppingCart, ArrowRight, ShieldCheck, Zap } from "lucide-react";

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col bg-zinc-950 text-zinc-100 selection:bg-indigo-500 selection:text-white">
      {/* Glow gradient */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 h-[450px] w-[800px] bg-gradient-to-tr from-indigo-600/20 via-violet-600/20 to-purple-600/10 blur-[130px] pointer-events-none rounded-full" />

      {/* Navigation */}
      <header className="relative z-10 border-b border-zinc-800/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-500 to-violet-600 text-white shadow-md">
              <Sparkles className="h-5 w-5" />
            </div>
            <span className="text-lg font-bold tracking-tight">MerchantMind</span>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/chat"
              className="flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-indigo-500 active:scale-95"
            >
              <MessageSquare className="h-4 w-4" />
              <span>Launch Live Store</span>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="relative z-10 flex flex-1 flex-col items-center justify-center px-6 py-20 text-center">
        <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3.5 py-1 text-xs font-semibold text-indigo-300 backdrop-blur-md">
          <Zap className="h-3.5 w-3.5 text-indigo-400" />
          <span>Track 01: AI Growth & Agentic Commerce | Razorpay Hackathon</span>
        </div>

        <h1 className="mt-8 max-w-3xl text-4xl font-extrabold tracking-tight sm:text-6xl sm:leading-tight">
          AI-Powered Growth Agent for{" "}
          <span className="bg-gradient-to-r from-indigo-400 via-violet-300 to-purple-400 bg-clip-text text-transparent">
            Razorpay Merchants
          </span>
        </h1>

        <p className="mt-6 max-w-2xl text-base leading-relaxed text-zinc-400 sm:text-lg">
          Transform your digital storefront into an autonomous AI shopping experience. Customers browse in natural language, receive intelligent budget-aware recommendations with reasoning, and checkout seamlessly.
        </p>

        {/* CTA Buttons */}
        <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
          <Link
            href="/chat"
            className="flex items-center gap-2.5 rounded-2xl bg-gradient-to-r from-indigo-500 to-violet-600 px-6 py-3.5 text-sm font-bold text-white shadow-xl transition hover:from-indigo-600 hover:to-violet-700 active:scale-95"
          >
            <ShoppingCart className="h-4 w-4" />
            <span>Try Conversational Checkout</span>
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>

        {/* Feature Grid */}
        <div className="mt-20 grid w-full max-w-5xl grid-cols-1 gap-6 text-left sm:grid-cols-3">
          <div className="rounded-2xl border border-zinc-800/80 bg-zinc-900/60 p-6 backdrop-blur-md">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-400">
              <MessageSquare className="h-5 w-5" />
            </div>
            <h3 className="mt-4 font-semibold text-zinc-100">Conversational Checkout</h3>
            <p className="mt-2 text-xs leading-relaxed text-zinc-400">
              Natural language catalog search with budget-bounded reasoning and multi-turn cart manipulation.
            </p>
          </div>

          <div className="rounded-2xl border border-zinc-800/80 bg-zinc-900/60 p-6 backdrop-blur-md">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-500/10 text-violet-400">
              <Sparkles className="h-5 w-5" />
            </div>
            <h3 className="mt-4 font-semibold text-zinc-100">Intelligent Upselling</h3>
            <p className="mt-2 text-xs leading-relaxed text-zinc-400">
              Smart cross-selling of complementary products (e.g. birthday candles with cake) to boost merchant AOV.
            </p>
          </div>

          <div className="rounded-2xl border border-zinc-800/80 bg-zinc-900/60 p-6 backdrop-blur-md">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-400">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <h3 className="mt-4 font-semibold text-zinc-100">Razorpay Ready</h3>
            <p className="mt-2 text-xs leading-relaxed text-zinc-400">
              Instant payment link generation and automated audit trail for every agent action and transaction.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-zinc-900 py-6 text-center text-xs text-zinc-600">
        MerchantMind © 2026 — Built for Razorpay AI Buildathon
      </footer>
    </div>
  );
}
