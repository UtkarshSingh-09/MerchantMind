"use client";

import React from "react";
import { PlasmaTorusCanvas } from "@/components/ui/plasma-torus-canvas";

interface ConvergenceSingularityProps {
  opacity: number;
}

export function ConvergenceSingularity({ opacity }: ConvergenceSingularityProps) {
  if (opacity <= 0.01) return null;

  const smoothProgress = Math.min(opacity, 1.0);
  const translateY = (1 - smoothProgress) * 25;
  const zoomFactor = 1.0 + (1.0 - smoothProgress) * 1.4;

  return (
    <div
      className="fixed inset-0 z-10 flex items-center justify-center pointer-events-none overflow-hidden bg-transparent"
      style={{
        opacity: smoothProgress,
        transform: `scale(${zoomFactor})`,
      }}
    >
      {/* Live 3D Hyper-Dimensional Plasma Torus Knot */}
      <PlasmaTorusCanvas opacity={smoothProgress} />

      {/* Soft Ambient Depth Glow behind the 3D Plasma Knot */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[500px] bg-radial from-[#3b82f6]/6 via-transparent to-transparent blur-[140px] pointer-events-none" />

      {/* Foreground Content: Monumental Centered Typography with Contrast Shield */}
      <div
        className="relative z-20 max-w-5xl mx-auto px-6 flex flex-col items-center justify-center text-center pointer-events-auto transition-transform duration-100 ease-out"
        style={{
          transform: `translateY(${translateY}px)`,
        }}
      >
        {/* Soft Radial Contrast Shield behind Text to Guarantee Legibility */}
        <div className="absolute inset-0 max-w-2xl mx-auto h-[420px] top-1/2 -translate-y-1/2 bg-black/65 blur-2xl rounded-full -z-10 pointer-events-none" />

        {/* Supertitle */}
        <div className="inline-flex items-center gap-2 font-mono text-[11px] sm:text-[12px] tracking-[0.35em] uppercase text-[#00C0F9] mb-5 font-semibold px-4 py-1.5 rounded-full bg-[#00C0F9]/10 border border-[#00C0F9]/40 backdrop-blur-md drop-shadow-[0_2px_12px_rgba(0,0,0,0.9)]">
          <span className="w-1.5 h-1.5 rounded-full bg-[#00C0F9] animate-ping" />
          <span>THE UNIFIED INTELLIGENCE</span>
        </div>

        {/* Climax Headline */}
        <h2 className="font-editorial text-4xl sm:text-6xl md:text-7xl lg:text-[76px] leading-[1.05] tracking-tight text-white max-w-4xl mb-6 drop-shadow-[0_4px_30px_rgba(0,0,0,1)] [text-shadow:_0_2px_16px_rgba(0,0,0,0.95),_0_6px_35px_rgba(0,0,0,1)]">
          What if <span className="italic text-[#a5c8ff]">one model</span> could understand commerce as a whole?
        </h2>

        {/* Supporting Philosophy (Crisp, High-Contrast Text with Black Drop Shadow) */}
        <p className="text-sm sm:text-base md:text-lg text-[#F1F5F9] font-normal leading-relaxed max-w-2xl mb-10 drop-shadow-[0_2px_10px_rgba(0,0,0,1)] [text-shadow:_0_2px_12px_rgba(0,0,0,0.95),_0_4px_25px_rgba(0,0,0,1)]">
          Not disjointed tools passing static payloads. But a single continuous mind that searches with empathy,
          recommends with budget precision, and settles payments instantly.
        </p>

        {/* 4 Unified Capability Pills */}
        <div className="flex flex-wrap items-center justify-center gap-3 max-w-3xl">
          <div className="px-4 py-2 rounded-full font-mono text-[10px] sm:text-[11px] uppercase tracking-wider text-[#d4e3ff] bg-[#3395FF]/10 border border-[#3395FF]/30 backdrop-blur-md shadow-[0_0_15px_rgba(51,149,255,0.15)] hover:border-[#3395FF]/70 transition">
            01 // INTENT SYNTHESIS
          </div>

          <div className="px-4 py-2 rounded-full font-mono text-[10px] sm:text-[11px] uppercase tracking-wider text-[#c0e8ff] bg-[#00C0F9]/10 border border-[#00C0F9]/30 backdrop-blur-md shadow-[0_0_15px_rgba(0,192,249,0.15)] hover:border-[#00C0F9]/70 transition">
            02 // DYNAMIC CART REASONING
          </div>

          <div className="px-4 py-2 rounded-full font-mono text-[10px] sm:text-[11px] uppercase tracking-wider text-[#a5c8ff] bg-[#a5c8ff]/10 border border-[#a5c8ff]/30 backdrop-blur-md shadow-[0_0_15px_rgba(165,200,255,0.15)] hover:border-[#a5c8ff]/70 transition">
            03 // AUTONOMOUS UPSELLING
          </div>

          <div className="px-4 py-2 rounded-full font-mono text-[10px] sm:text-[11px] uppercase tracking-wider text-white bg-white/5 border border-white/20 backdrop-blur-md shadow-[0_0_15px_rgba(255,255,255,0.1)] hover:border-white/50 transition">
            04 // INSTANT SETTLEMENT
          </div>
        </div>
      </div>
    </div>
  );
}
