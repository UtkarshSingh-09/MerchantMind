"use client";

import React from "react";

interface DeepCosmosIsolationProps {
  opacity: number;
}

export function DeepCosmosIsolation({ opacity }: DeepCosmosIsolationProps) {
  if (opacity <= 0.01) return null;

  const smoothProgress = Math.min(opacity, 1.0);
  const zoomFactor = 1.0 + (1.0 - smoothProgress) * 1.4;
  const translateY = (1 - smoothProgress) * 20;

  return (
    <div
      className="fixed inset-0 z-10 flex items-center justify-between pointer-events-none overflow-hidden bg-transparent"
      style={{
        opacity: smoothProgress,
        transform: `scale(${zoomFactor})`,
      }}
    >
      {/* Ambient Lighting on the left stage */}
      <div className="absolute top-1/2 left-[28%] -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-radial from-[#3395FF]/8 via-[#00C0F9]/3 to-transparent blur-[140px] pointer-events-none" />

      {/* Main Container Layout */}
      <div
        className="relative z-20 w-full max-w-7xl mx-auto px-6 md:px-12 flex flex-col md:flex-row items-center justify-between h-full pointer-events-auto transition-transform duration-100 ease-out"
        style={{
          transform: `translateY(${translateY}px)`,
        }}
      >
        {/* Left Column: 3 Isolated Telemetry Node Badges Anchored to 3D Silos */}
        <div className="relative w-full md:w-1/2 h-[380px] md:h-[500px] flex flex-col justify-around">
          {/* Node 1: Discovery (Top Left) */}
          <div className="relative md:absolute top-4 md:top-[16%] left-0 md:left-[10%] animate-float float-delay-1">
            <div className="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full font-mono text-[11px] uppercase tracking-widest text-[#d4e4fa] bg-[#051424]/80 border border-rose-500/40 backdrop-blur-md shadow-[0_0_15px_rgba(244,63,94,0.2)] hover:border-rose-500/80 transition">
              <span className="w-2 h-2 rounded-full bg-rose-400 animate-pulse" />
              <span>01 // DISCOVERY (ISOLATED)</span>
            </div>
          </div>

          {/* Node 2: Revenue (Center) */}
          <div className="relative md:absolute top-8 md:top-[48%] left-0 md:left-[32%] animate-float float-delay-2">
            <div className="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full font-mono text-[11px] uppercase tracking-widest text-[#d4e4fa] bg-[#051424]/80 border border-[#3395FF]/50 backdrop-blur-md shadow-[0_0_15px_rgba(51,149,255,0.25)] hover:border-[#3395FF]/90 transition">
              <span className="w-2 h-2 rounded-full bg-[#3395FF] animate-pulse" />
              <span>02 // REVENUE (BLIND UPSELL)</span>
            </div>
          </div>

          {/* Node 3: Settlement (Bottom Left) */}
          <div className="relative md:absolute top-12 md:top-[78%] left-0 md:left-[14%] animate-float float-delay-3">
            <div className="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full font-mono text-[11px] uppercase tracking-widest text-[#d4e4fa] bg-[#051424]/80 border border-[#00C0F9]/50 backdrop-blur-md shadow-[0_0_15px_rgba(0,192,249,0.25)] hover:border-[#00C0F9]/90 transition">
              <span className="w-2 h-2 rounded-full bg-[#00C0F9] animate-pulse" />
              <span>03 // SETTLEMENT (DROPOFF)</span>
            </div>
          </div>
        </div>

        {/* Right Column: Editorial Narrative & Telemetry Stats */}
        <div className="w-full md:w-1/2 flex flex-col justify-center pl-0 md:pl-10 mt-8 md:mt-0">
          <div className="max-w-xl">
            {/* Supertitle */}
            <div className="font-mono text-[11px] sm:text-[12px] tracking-[0.3em] uppercase text-[#3395FF] mb-4 font-medium drop-shadow-[0_0_8px_rgba(51,149,255,0.4)]">
              THE FRAGMENTATION
            </div>

            {/* Main Headline */}
            <h2 className="font-editorial text-4xl sm:text-5xl lg:text-[54px] leading-[1.08] tracking-tight text-white mb-3 drop-shadow-[0_4px_30px_rgba(0,0,0,1)]">
              For years, merchants stacked tools for search, upselling, and checkout.
            </h2>
            <h3 className="font-editorial text-3xl sm:text-4xl lg:text-[44px] leading-[1.1] tracking-tight text-[#A5C8FF] italic mb-6">
              But they existed in isolation.
            </h3>

            {/* Narrative Body */}
            <p className="text-sm sm:text-base text-[#CBD5E1] font-light leading-relaxed mb-8 max-w-lg">
              Keyword search ignores customer constraints. Upsell engines blow past budgets. 
              Checkout knows nothing about the conversation that just happened.
            </p>

            {/* Telemetry Stats Bar */}
            <div className="border-t border-dashed border-white/15 pt-6 flex items-center gap-8 sm:gap-12">
              <div>
                <div className="font-mono text-[10px] tracking-wider uppercase text-zinc-400 mb-1">
                  LATENCY
                </div>
                <div className="font-mono text-base sm:text-lg font-semibold text-[#a5c8ff]">
                  0.4ms
                </div>
              </div>

              <div>
                <div className="font-mono text-[10px] tracking-wider uppercase text-zinc-400 mb-1">
                  ECOSYSTEM
                </div>
                <div className="font-mono text-base sm:text-lg font-semibold text-[#82d6ff]">
                  3 SILOS
                </div>
              </div>

              <div>
                <div className="font-mono text-[10px] tracking-wider uppercase text-zinc-400 mb-1">
                  STATUS
                </div>
                <div className="font-mono text-base sm:text-lg font-semibold text-emerald-400 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block animate-ping" />
                  <span>UNIFIED READY</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
