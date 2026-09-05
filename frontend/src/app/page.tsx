"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Lock, X, ChevronDown } from "lucide-react";
import { ParticleConstellation } from "@/components/ParticleConstellation";
import { CommerceDataChaos } from "@/components/CommerceDataChaos";
import { DeepCosmosIsolation } from "@/components/DeepCosmosIsolation";
import { ConvergenceSingularity } from "@/components/ConvergenceSingularity";
import { TerminalDeploymentCTA } from "@/components/TerminalDeploymentCTA";
import { LightRayWarp } from "@/components/ui/light-ray-warp";
import { LiquidMetalButton } from "@/components/ui/liquid-metal-button";
import { PresentationModal, PresentationTab } from "@/components/PresentationModal";

export default function HomePage() {
  const router = useRouter();
  const [showVaultModal, setShowVaultModal] = useState(false);
  const [showPresentationModal, setShowPresentationModal] = useState(false);
  const [presentationTab, setPresentationTab] = useState<PresentationTab>("analytics");
  const [isWarping, setIsWarping] = useState(false);
  const [scrollY, setScrollY] = useState(0);

  const openPresentation = (tab: PresentationTab) => {
    setPresentationTab(tab);
    setShowPresentationModal(true);
  };

  const handleConnectVault = () => {
    setShowVaultModal(false);
    setShowPresentationModal(false);
    setIsWarping(true);
  };

  useEffect(() => {
    const handleScroll = () => {
      setScrollY(window.scrollY || window.pageYOffset);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Calculate scroll progress for multi-chapter opacity transitions
  const windowH = typeof window !== "undefined" ? window.innerHeight : 800;
  
  // Chapter 1: Hero View (0 to 0.45 * windowH)
  const heroOpacity = Math.max(0, 1 - scrollY / (windowH * 0.45));
  
  // Chapter 2: Radar Tunnel View (0.35 to 1.15 * windowH)
  const introFadeIn = Math.min(Math.max((scrollY - windowH * 0.35) / (windowH * 0.3), 0), 1);
  const introFadeOut = Math.max(0, 1 - Math.max(0, scrollY - windowH * 0.85) / (windowH * 0.3));
  const introOpacity = introFadeIn * introFadeOut;

  // Chapter 3: Commerce Data Chaos (1.05 to 2.1 * windowH)
  const chaosFadeIn = Math.min(Math.max((scrollY - windowH * 1.05) / (windowH * 0.3), 0), 1);
  const chaosFadeOut = Math.max(0, 1 - Math.max(0, scrollY - windowH * 1.75) / (windowH * 0.3));
  const chaosOpacity = chaosFadeIn * chaosFadeOut;

  // Chapter 4: Deep Cosmos Isolation (1.85 to 3.2 * windowH)
  const isolationFadeIn = Math.min(Math.max((scrollY - windowH * 1.85) / (windowH * 0.35), 0), 1);
  const isolationFadeOut = Math.max(0, 1 - Math.max(0, scrollY - windowH * 2.85) / (windowH * 0.35));
  const isolationOpacity = isolationFadeIn * isolationFadeOut;

  // Chapter 5: Convergence Singularity (2.95 to 4.4 * windowH)
  const convergenceFadeIn = Math.min(Math.max((scrollY - windowH * 2.95) / (windowH * 0.35), 0), 1);
  const convergenceFadeOut = Math.max(0, 1 - Math.max(0, scrollY - windowH * 4.15) / (windowH * 0.35));
  const convergenceOpacity = convergenceFadeIn * convergenceFadeOut;

  // Chapter 6: Terminal Deployment CTA (4.2 to 6.6 * windowH)
  const terminalFadeIn = Math.min(Math.max((scrollY - windowH * 4.25) / (windowH * 0.35), 0), 1);
  const terminalOpacity = terminalFadeIn;

  return (
    <div className="relative min-h-[660vh] bg-[#000000] text-[#e2e2e2] selection:bg-[#3395FF] selection:text-white overflow-x-hidden">
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

          {/* Minimalist Navigation Links with Direct Page Routing */}
          <nav className="flex items-center gap-4 sm:gap-8 text-xs sm:text-sm">
            <Link
              href="/analytics"
              className="text-[#94A3B8] hover:text-white transition-colors cursor-pointer py-1"
            >
              Analytics
            </Link>
            <Link
              href="/intelligence"
              className="text-[#94A3B8] hover:text-white transition-colors cursor-pointer py-1"
            >
              Intelligence
            </Link>
            <Link
              href="/architecture"
              className="text-[#94A3B8] hover:text-white transition-colors cursor-pointer py-1"
            >
              Architecture
            </Link>
          </nav>

          {/* Action CTA with Liquid Metal Design */}
          <div className="flex items-center gap-4">
            <LiquidMetalButton
              label="Connect Vault"
              onClick={handleConnectVault}
            />
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
        }}
      >
        {/* Subtle Radial Atmosphere Behind Text */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-radial from-[#3395FF]/10 via-transparent to-transparent blur-[120px] pointer-events-none" />

        {/* Supertitle */}
        <div className="inline-flex items-center gap-2 font-mono text-[11px] sm:text-[12px] tracking-[0.3em] uppercase text-[#3395FF] mb-6 font-medium px-3.5 py-1.5 rounded-full bg-[#3395FF]/10 border border-[#3395FF]/30 backdrop-blur-md drop-shadow-[0_0_12px_rgba(51,149,255,0.3)]">
          <span className="w-1.5 h-1.5 rounded-full bg-[#3395FF] animate-pulse" />
          <span>AUTONOMOUS AGENTIC COMMERCE</span>
        </div>

        {/* Hero Title */}
        <h1 className="font-editorial text-5xl sm:text-7xl lg:text-[88px] leading-[1.02] tracking-tight text-white max-w-5xl mb-8 drop-shadow-[0_4px_30px_rgba(0,0,0,0.8)]">
          Step into the world of <br />
          <span className="italic text-[#a5c8ff]">agentic payments.</span>
        </h1>

        {/* Subtitle */}
        <p className="text-base sm:text-lg text-[#CBD5E1] font-normal max-w-xl mx-auto leading-relaxed text-contrast-shadow">
          One continuous mind for catalog discovery, intelligent upsell reasoning,
          and instant Razorpay settlement.
        </p>

        {/* Scroll Indicator with Click Trigger to /architecture */}
        <Link
          href="/architecture"
          className="absolute bottom-10 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 font-mono text-[10px] tracking-widest text-[#94A3B8] hover:text-white uppercase pointer-events-auto cursor-pointer transition group"
        >
          <span className="group-hover:text-[#3395FF] transition">CLICK OR SCROLL TO EXPLORE ARCHITECTURE</span>
          <div className="w-[1px] h-8 bg-gradient-to-b from-[#3395FF] to-transparent animate-pulse" />
        </Link>
      </div>

      {/* ========================================================================= */}
      {/* CHAPTER 2: RADAR NETWORK VIEW ("Multi-Node Telemetry")                   */}
      {/* ========================================================================= */}
      <div
        className="fixed inset-0 z-10 flex flex-col items-center justify-center px-6 text-center pointer-events-none transition-opacity duration-150"
        style={{
          opacity: introOpacity,
        }}
      >
        <div className="max-w-4xl mx-auto">
          <div className="font-mono text-[11px] tracking-[0.25em] uppercase text-[#00C0F9] mb-4">
            NETWORK TOPOLOGY // MULTI-NODE
          </div>
          <h2 className="font-editorial text-4xl sm:text-6xl text-white mb-6 text-contrast-shadow">
            Autonomous commerce across every node.
          </h2>
          <p className="text-base sm:text-lg text-[#CBD5E1] font-normal max-w-2xl mx-auto text-contrast-shadow">
            From search indexing to live cart synthesis and merchant payment routes.
          </p>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* CHAPTER 3: COMMERCE DATA CHAOS ("Every catalog. Every craving...")       */}
      {/* ========================================================================= */}
      <CommerceDataChaos opacity={chaosOpacity} />

      {/* ========================================================================= */}
      {/* CHAPTER 4: DEEP COSMOS ISOLATION ("The Fragmentation / Isolated Silos")  */}
      {/* ========================================================================= */}
      <DeepCosmosIsolation opacity={isolationOpacity} />

      {/* ========================================================================= */}
      {/* CHAPTER 5: CONVERGENCE SINGULARITY ("What if one model...")              */}
      {/* ========================================================================= */}
      <ConvergenceSingularity opacity={convergenceOpacity} />

      {/* ========================================================================= */}
      {/* CHAPTER 6: TERMINAL DEPLOYMENT CTA ("Step into the future...")           */}
      {/* ========================================================================= */}
      <TerminalDeploymentCTA
        opacity={terminalOpacity}
        onOpenVaultModal={handleConnectVault}
      />

      {/* ========================================================================= */}
      {/* CINEMATIC LIGHT RAY WARP TRANSITION TO /CHAT                             */}
      {/* ========================================================================= */}
      <LightRayWarp
        active={isWarping}
        destination="/chat"
      />

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
                onClick={handleConnectVault}
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

      {/* ========================================================================= */}
      {/* EXECUTIVE PRESENTATION SUITE (ANALYTICS, INTELLIGENCE, ARCHITECTURE)     */}
      {/* ========================================================================= */}
      <PresentationModal
        isOpen={showPresentationModal}
        initialTab={presentationTab}
        onClose={() => setShowPresentationModal(false)}
        onLaunchDemo={handleConnectVault}
      />
    </div>
  );
}
