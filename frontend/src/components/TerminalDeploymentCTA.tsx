"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { ShieldCheck } from "lucide-react";
import { HyperGridRunway } from "@/components/ui/hyper-grid-runway";
import { LiquidMetalButton } from "@/components/ui/liquid-metal-button";

interface TerminalDeploymentCTAProps {
  opacity: number;
  onOpenVaultModal?: () => void;
}

export function TerminalDeploymentCTA({
  opacity,
  onOpenVaultModal,
}: TerminalDeploymentCTAProps) {
  const router = useRouter();

  if (opacity <= 0.01) return null;

  const smoothProgress = Math.min(opacity, 1.0);
  const translateY = (1 - smoothProgress) * 25;
  const scale = 0.92 + smoothProgress * 0.08;

  return (
    <div
      className="fixed inset-0 z-20 flex items-center justify-center pt-16 pb-6 px-4 pointer-events-none overflow-hidden bg-transparent"
      style={{
        opacity: smoothProgress,
      }}
    >
      {/* 21st.dev HyperGrid & Infinite Perspective Horizon Runway */}
      <HyperGridRunway opacity={smoothProgress} />

      {/* Center Monolithic Glass Terminal Card (All 4 Outlines Clearly Visible) */}
      <div
        className="relative z-30 w-full max-w-lg mx-auto pointer-events-auto transition-transform duration-150 ease-out flex flex-col items-center justify-center"
        style={{
          transform: `translateY(${translateY}px) scale(${scale})`,
        }}
      >
        <div className="relative w-full rounded-2xl bg-[#090D14]/92 border border-[#3395FF]/60 backdrop-blur-2xl p-6 sm:p-7 shadow-[0_0_60px_rgba(51,149,255,0.25)] overflow-hidden text-center flex flex-col items-center">
          {/* Top Glowing Cyan Laser Accent Strip */}
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-[#00C0F9] to-transparent shadow-[0_0_15px_#00C0F9]" />

          {/* Ambient Background Aura inside Card */}
          <div className="pointer-events-none absolute -top-24 left-1/2 -translate-x-1/2 w-64 h-64 bg-[#3395FF]/20 blur-3xl rounded-full" />

          {/* Card Header: System Status Bar */}
          <div className="flex items-center justify-between w-full pb-4 border-b border-white/10 mb-5">
            <div className="flex items-center gap-2">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
              </span>
              <span className="font-mono text-[10px] tracking-widest text-emerald-400 font-semibold uppercase">
                SYSTEM STATUS: AUTONOMOUS CORE ACTIVE
              </span>
            </div>

            <div className="font-mono text-[10px] tracking-wider text-zinc-400 uppercase px-2 py-0.5 rounded bg-white/5 border border-white/10">
              v2.4.0-DEPLOY
            </div>
          </div>

          {/* Main Climax Headline */}
          <div className="mb-2">
            <h2 className="font-editorial text-3xl sm:text-4xl lg:text-[44px] leading-[1.1] text-white tracking-tight drop-shadow-[0_4px_30px_rgba(0,0,0,0.8)]">
              Step into the future of{" "}
              <span className="italic text-[#a5c8ff]">agentic commerce.</span>
            </h2>
          </div>

          {/* Supporting Pitch */}
          <p className="text-xs sm:text-sm text-[#94A3B8] font-light leading-relaxed max-w-sm mx-auto mb-6">
            Deploy MerchantMind to unify catalog search, intelligent upselling, and instant checkout in a single autonomous flow.
          </p>

          {/* 3 Value Telemetry Badges */}
          <div className="grid grid-cols-3 gap-2 w-full mb-6">
            <div className="rounded-lg bg-white/[0.03] border border-white/10 py-2.5 px-2 text-center">
              <div className="font-mono text-[9px] text-zinc-400 uppercase tracking-wider mb-0.5">
                EXECUTION
              </div>
              <div className="font-mono text-xs font-semibold text-white">
                100% Autonomous
              </div>
            </div>

            <div className="rounded-lg bg-white/[0.03] border border-white/10 py-2.5 px-2 text-center">
              <div className="font-mono text-[9px] text-zinc-400 uppercase tracking-wider mb-0.5">
                LATENCY
              </div>
              <div className="font-mono text-xs font-semibold text-[#82d6ff]">
                0.4ms Engine
              </div>
            </div>

            <div className="rounded-lg bg-white/[0.03] border border-white/10 py-2.5 px-2 text-center">
              <div className="font-mono text-[9px] text-zinc-400 uppercase tracking-wider mb-0.5">
                SECURITY
              </div>
              <div className="font-mono text-xs font-semibold text-emerald-400">
                Zero Leakage
              </div>
            </div>
          </div>

          {/* Single Primary Action Button: CONNECT VAULT */}
          <div className="flex items-center justify-center w-full mb-5">
            <LiquidMetalButton
              label="CONNECT VAULT"
              onClick={() => {
                if (onOpenVaultModal) {
                  onOpenVaultModal();
                } else {
                  router.push("/chat");
                }
              }}
            />
          </div>

          {/* Footer Trust Guarantee Micro-copy */}
          <div className="pt-3.5 border-t border-dashed border-white/10 flex items-center justify-center gap-2 text-center text-zinc-500 font-mono text-[9.5px] uppercase tracking-wider w-full">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400/80 inline" />
            <span>PCI-DSS Level 1 Compliant • 99.99% Uptime • Razorpay Verified Partner</span>
          </div>
        </div>
      </div>
    </div>
  );
}
