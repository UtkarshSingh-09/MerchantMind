"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Lock, X, ChevronDown } from "lucide-react";
import { ParticleConstellation } from "@/components/ParticleConstellation";
import { LiquidMetalButton } from "@/components/ui/liquid-metal-button";

export default function HomePage() {
  const router = useRouter();
  const [showVaultModal, setShowVaultModal] = useState(false);
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      setScrollY(window.scrollY || window.pageYOffset);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Calculate scroll progress for opacity fades
  const windowH = typeof window !== "undefined" ? window.innerHeight : 800;
  const heroOpacity = Math.max(0, 1 - scrollY / (windowH * 0.45));
  const introOpacity = Math.min(Math.max((scrollY - windowH * 0.35) / (windowH * 0.35), 0), 1);

  return (
    <div className="relative min-h-[220vh] bg-[#000000] text-[#e2e2e2] selection:bg-[#3395FF] selection:text-white overflow-x-hidden">
      {/* 3D WebGL Particle Universe: Expands Monogram & Reveals Multi-Node Network */}
      <ParticleConstellation />

      {/* Top Ambient Glow */}
      <div className="pointer-events-none fixed top-0 left-1/2 -translate-x-1/2 h-[450px] w-[900px] bg-gradient-to-tr from-[#3395FF]/12 via-[#00C0F9]/10 to-transparent blur-[160px] rounded-full z-0" />

      {/* Top Navigation Bar — Exact Stitch Design */}
      <header className="fixed top-0 left-0 right-0 z-50 w-full border-b border-white/10 bg-[#000000]/70 backdrop-blur-xl transition-all duration-300">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          {/* Brand Logo in Editorial Serif */}
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="font-editorial text-2xl md:text-3xl text-white tracking-tight hover:opacity-90 transition"
            >
              MerchantMind
            </Link>
          </div>

          {/* Minimalist Navigation Links */}
          <nav className="hidden md:flex items-center gap-8 text-sm">
            <a
              href="#"
              className="text-[#94A3B8] hover:text-white transition-colors"
            >
              Analytics
            </a>
            <a
              href="#"
              className="text-[#94A3B8] hover:text-white transition-colors"
            >
              Intelligence
            </a>
            <a
              href="#"
              className="text-[#94A3B8] hover:text-white transition-colors"
            >
              Architecture
            </a>
          </nav>

          {/* Action CTA */}
          <div className="flex items-center gap-4">
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

      {/* ========================================================================= */}
      {/* CHAPTER 1: HERO VIEW ("Step into the world of agentic payments.")         */}
      {/* ========================================================================= */}
      <div
        className="fixed inset-0 z-10 flex flex-col items-center justify-center px-6 text-center pointer-events-none transition-opacity duration-150"
        style={{
          opacity: heroOpacity,
          display: heroOpacity <= 0 ? "none" : "flex",
        }}
      >
        <div className="max-w-4xl mx-auto flex flex-col items-center">
          {/* Editorial Headline */}
          <h1 className="font-editorial text-5xl sm:text-7xl lg:text-[84px] leading-[1.05] tracking-tight text-white max-w-4xl drop-shadow-2xl">
            Step into the world of{" "}
            <span className="italic text-[#a5c8ff]">agentic payments.</span>
          </h1>

          {/* Narrative Subhead */}
          <p className="mt-8 text-base sm:text-lg text-[#94A3B8] max-w-2xl font-light leading-relaxed">
            For years, digital storefronts built static filters and manual search.
            But they existed in isolation. What if one model could
            understand catalogs, intent, upselling, and payments as a whole?
          </p>
        </div>

        {/* Scroll cue */}
        <div className="absolute bottom-8 flex flex-col items-center gap-2 opacity-60 animate-bounce">
          <span className="text-[10px] font-mono tracking-widest text-[#94A3B8] uppercase">
            Scroll to enter
          </span>
          <ChevronDown className="w-4 h-4 text-[#00C0F9]" />
        </div>
      </div>

      {/* ========================================================================= */}
      {/* CHAPTER 2: RADAR TUNNEL VIEW ("Introducing MerchantMind")                 */}
      {/* ========================================================================= */}
      <div
        className="fixed inset-0 z-10 flex flex-col items-center justify-center px-6 text-center pointer-events-none transition-opacity duration-200"
        style={{
          opacity: introOpacity,
          display: introOpacity <= 0 ? "none" : "flex",
        }}
      >
        <div className="max-w-4xl mx-auto flex flex-col items-center">
          <h2 className="font-editorial text-5xl sm:text-7xl lg:text-[84px] leading-[1.05] tracking-tight text-white max-w-3xl drop-shadow-[0_4px_30px_rgba(0,0,0,1)]">
            Introducing <span className="italic text-[#3395FF]">MerchantMind</span>
          </h2>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* CONNECT VAULT APERTURE FLASH MODAL                                        */}
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
