"use client";

import React, { useEffect, useState } from "react";

interface ChipItem {
  text: string;
  x: number; // percentage
  y: number; // percentage
  rotation: number; // deg
  duration: number; // s
  delay: number; // s
  speed: number; // parallax multiplier
  glow: boolean;
}

const RAW_CHIPS = [
  "EGGLESS", "UNDER ₹800", "BIRTHDAY", "GLUTEN-FREE", "VANILLA", 
  "RED VELVET", "₹450", "₹1200", "SUGAR-FREE", "SAME DAY", 
  "COD", "UPI", "CREDIT CARD", "VEGAN", "ORGANIC", 
  "2KG", "ANNIVERSARY", "CHOCOLATE", "BUTTERSCOTCH", "PREMIUM"
];

// Pre-calculated deterministic positions to avoid hydration mismatch and avoid center text collision
const STATIC_CHIP_POSITIONS: Omit<ChipItem, "text">[] = [
  { x: 8, y: 15, rotation: -3, duration: 8, delay: 0, speed: 0.03, glow: false },
  { x: 78, y: 14, rotation: 4, duration: 9, delay: -2, speed: 0.04, glow: true },
  { x: 12, y: 38, rotation: -2, duration: 7, delay: -4, speed: 0.025, glow: false },
  { x: 86, y: 36, rotation: 3, duration: 10, delay: -1, speed: 0.035, glow: true },
  { x: 44, y: 12, rotation: 1, duration: 8.5, delay: -3, speed: 0.02, glow: false },
  { x: 6, y: 62, rotation: -4, duration: 9.5, delay: -5, speed: 0.045, glow: false },
  { x: 82, y: 58, rotation: 2, duration: 7.5, delay: -2.5, speed: 0.03, glow: true },
  { x: 15, y: 82, rotation: 3, duration: 11, delay: -6, speed: 0.035, glow: false },
  { x: 74, y: 80, rotation: -3, duration: 8, delay: -1.5, speed: 0.04, glow: false },
  { x: 42, y: 88, rotation: 2, duration: 9, delay: -3.5, speed: 0.025, glow: true },
  { x: 26, y: 22, rotation: -2, duration: 10.5, delay: -4.5, speed: 0.03, glow: false },
  { x: 68, y: 24, rotation: 4, duration: 8.2, delay: -0.5, speed: 0.038, glow: true },
  { x: 88, y: 72, rotation: -1, duration: 9.8, delay: -5.2, speed: 0.042, glow: false },
  { x: 5, y: 48, rotation: 3, duration: 7.8, delay: -2.1, speed: 0.028, glow: false },
  { x: 92, y: 22, rotation: -4, duration: 11.2, delay: -3.8, speed: 0.032, glow: false },
  { x: 28, y: 84, rotation: 2, duration: 8.7, delay: -1.2, speed: 0.026, glow: false },
  { x: 62, y: 86, rotation: -2, duration: 9.1, delay: -4.1, speed: 0.034, glow: false },
  { x: 18, y: 26, rotation: 4, duration: 10.1, delay: -2.8, speed: 0.031, glow: false },
  { x: 72, y: 46, rotation: -3, duration: 8.4, delay: -5.0, speed: 0.04, glow: true },
  { x: 84, y: 86, rotation: 1, duration: 9.3, delay: -1.9, speed: 0.036, glow: false },
];

interface CommerceDataChaosProps {
  opacity: number;
}

export function CommerceDataChaos({ opacity }: CommerceDataChaosProps) {
  const [mouseOffset, setMouseOffset] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const centerX = window.innerWidth / 2;
      const centerY = window.innerHeight / 2;
      setMouseOffset({
        x: e.clientX - centerX,
        y: e.clientY - centerY,
      });
    };

    window.addEventListener("mousemove", handleMouseMove, { passive: true });
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  if (opacity <= 0.01) return null;

  // As chapter 3 fades out, scale up outwards simulating diving through data
  const zoomFactor = 1.0 + (1.0 - Math.min(opacity, 1.0)) * 1.2;

  return (
    <div
      className="fixed inset-0 z-10 flex items-center justify-center pointer-events-none overflow-hidden"
      style={{
        opacity,
        transform: `scale(${zoomFactor})`,
      }}
    >
      {/* Ambient Blue Core Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[500px] bg-radial from-[#3395FF]/8 via-[#00C0F9]/4 to-transparent blur-[120px] rounded-full pointer-events-none" />

      {/* Center Editorial Typography */}
      <div className="relative z-30 flex flex-col items-center justify-center text-center px-6 max-w-4xl mx-auto">
        <h2 className="font-editorial text-4xl sm:text-6xl md:text-[68px] leading-[1.08] tracking-tight text-white drop-shadow-[0_4px_35px_rgba(0,0,0,0.9)]">
          Every catalog. Every craving.{" "}
          <span className="italic text-[#a5c8ff]">Every constraint.</span>
        </h2>

        {/* Thin Electric Blue Divider */}
        <div className="w-[120px] h-[1px] bg-gradient-to-r from-transparent via-[#3395FF]/60 to-transparent mx-auto mt-8 mb-4 shadow-[0_0_10px_rgba(51,149,255,0.4)]" />

        {/* Telemetry Monospace Metadata Readout */}
        <p className="font-mono text-[10px] sm:text-[11px] tracking-[0.3em] uppercase text-[#00C0F9] font-medium drop-shadow-[0_0_8px_rgba(0,192,249,0.3)]">
          12,847 PRODUCT SIGNALS PER SECOND
        </p>
      </div>

      {/* Floating Commerce Signals Matrix */}
      <div className="absolute inset-0 w-full h-full pointer-events-auto z-20">
        {RAW_CHIPS.map((chipText, index) => {
          const item = STATIC_CHIP_POSITIONS[index] || STATIC_CHIP_POSITIONS[0];
          const offsetX = mouseOffset.x * item.speed;
          const offsetY = mouseOffset.y * item.speed;

          return (
            <div
              key={chipText + index}
              className="absolute chip-wrapper"
              style={{
                left: `${item.x}%`,
                top: `${item.y}%`,
                animationDuration: `${item.duration}s`,
                animationDelay: `${item.delay}s`,
              }}
            >
              <div
                className={`cursor-default px-3.5 py-1.5 rounded-full font-mono text-[10px] uppercase tracking-widest transition-all duration-300 backdrop-blur-md select-none ${
                  item.glow
                    ? "bg-[#3395FF]/10 border border-[#3395FF]/30 text-[#d4e3ff] shadow-[0_0_15px_rgba(51,149,255,0.15)] hover:border-[#3395FF]/60 hover:bg-[#3395FF]/20 hover:scale-105"
                    : "bg-white/[0.04] border border-white/10 text-[#94a3b8] hover:border-white/30 hover:bg-white/[0.08] hover:text-white hover:scale-105"
                }`}
                style={{
                  transform: `rotate(${item.rotation}deg) translate(${offsetX}px, ${offsetY}px)`,
                }}
              >
                {chipText}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
