"use client";

import React, { useEffect, useRef } from "react";
import { VoiceState } from "@/lib/voice-manager";
import { Mic, MicOff, Volume2, Sparkles } from "lucide-react";

interface VoiceOrbProps {
  state: VoiceState;
  isActive: boolean;
  onToggle: () => void;
  size?: number;
}

export const VoiceOrb: React.FC<VoiceOrbProps> = ({
  state,
  isActive,
  onToggle,
  size = 72,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId: number;
    let angle = 0;
    const center = size / 2;

    const render = () => {
      ctx.clearRect(0, 0, size, size);
      angle += 0.04;

      // Color scheme according to state
      let primaryColor = "rgba(6, 182, 212, 0.8)"; // cyan (idle)
      let glowColor = "rgba(6, 182, 212, 0.3)";
      let ringColor = "rgba(6, 182, 212, 0.4)";
      let waveCount = 3;
      let amplitude = 4;

      if (!isActive) {
        primaryColor = "rgba(100, 116, 139, 0.6)";
        glowColor = "rgba(100, 116, 139, 0.1)";
        ringColor = "rgba(100, 116, 139, 0.2)";
        amplitude = 2;
      } else if (state === "listening") {
        primaryColor = "rgba(245, 158, 11, 0.9)"; // amber (listening)
        glowColor = "rgba(245, 158, 11, 0.4)";
        ringColor = "rgba(245, 158, 11, 0.5)";
        amplitude = 9;
      } else if (state === "thinking") {
        primaryColor = "rgba(168, 85, 247, 0.9)"; // purple (thinking)
        glowColor = "rgba(168, 85, 247, 0.4)";
        ringColor = "rgba(168, 85, 247, 0.6)";
        amplitude = 6;
      } else if (state === "speaking") {
        primaryColor = "rgba(16, 185, 129, 0.95)"; // emerald (speaking)
        glowColor = "rgba(16, 185, 129, 0.45)";
        ringColor = "rgba(16, 185, 129, 0.6)";
        amplitude = 11;
      }

      // Outer radial aura
      const gradient = ctx.createRadialGradient(
        center,
        center,
        4,
        center,
        center,
        center - 4
      );
      gradient.addColorStop(0, primaryColor);
      gradient.addColorStop(0.5, glowColor);
      gradient.addColorStop(1, "rgba(0, 0, 0, 0)");

      ctx.beginPath();
      ctx.arc(center, center, center - 6, 0, Math.PI * 2);
      ctx.fillStyle = gradient;
      ctx.fill();

      // Pulsing harmonic waveform rings
      for (let i = 0; i < waveCount; i++) {
        ctx.beginPath();
        const baseRadius = center * 0.48 + i * 4;
        const phaseShift = (i * Math.PI) / 2;

        for (let a = 0; a <= Math.PI * 2; a += 0.1) {
          const rOffset =
            Math.sin(a * 4 + angle * (i + 1) + phaseShift) * amplitude;
          const r = baseRadius + rOffset;
          const x = center + Math.cos(a) * r;
          const y = center + Math.sin(a) * r;
          if (a === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        }
        ctx.closePath();
        ctx.strokeStyle = ringColor;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      // Inner glowing core
      ctx.beginPath();
      const corePulse = Math.sin(angle * 2) * 2;
      ctx.arc(center, center, center * 0.28 + corePulse, 0, Math.PI * 2);
      ctx.fillStyle = primaryColor;
      ctx.shadowColor = primaryColor;
      ctx.shadowBlur = 12;
      ctx.fill();
      ctx.shadowBlur = 0;

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [state, isActive, size]);

  const getStateLabel = () => {
    if (!isActive) return "Tap for Voice";
    if (state === "listening") return "Listening...";
    if (state === "thinking") return "Thinking...";
    if (state === "speaking") return "Speaking...";
    return "Voice Ready";
  };

  const getStateColor = () => {
    if (!isActive) return "text-slate-400 border-slate-700/60";
    if (state === "listening") return "text-amber-400 border-amber-500/50 bg-amber-500/10";
    if (state === "thinking") return "text-purple-400 border-purple-500/50 bg-purple-500/10";
    if (state === "speaking") return "text-emerald-400 border-emerald-500/50 bg-emerald-500/10";
    return "text-cyan-400 border-cyan-500/50 bg-cyan-500/10";
  };

  return (
    <div className="flex flex-col items-center gap-1.5 select-none">
      <button
        onClick={onToggle}
        aria-label="Toggle Voice Mode"
        className="relative group focus:outline-none transition-transform active:scale-95"
      >
        <canvas
          ref={canvasRef}
          width={size}
          height={size}
          className="rounded-full cursor-pointer filter drop-shadow-[0_0_12px_rgba(6,182,212,0.3)] transition-all group-hover:scale-105"
        />
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          {!isActive ? (
            <MicOff className="w-5 h-5 text-slate-300 transition-transform group-hover:scale-110" />
          ) : state === "speaking" ? (
            <Volume2 className="w-5 h-5 text-white animate-pulse" />
          ) : (
            <Mic className="w-5 h-5 text-white animate-bounce" />
          )}
        </div>
      </button>

      <div
        className={`px-2 py-0.5 rounded-full text-[10px] font-mono tracking-wider border backdrop-blur-md uppercase font-semibold transition-all ${getStateColor()}`}
      >
        {getStateLabel()}
      </div>
    </div>
  );
};
