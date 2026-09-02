"use client";

import React, { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

interface LightRayWarpProps {
  active: boolean;
  destination?: string;
}

export function LightRayWarp({
  active,
  destination = "/chat",
}: LightRayWarpProps) {
  const router = useRouter();
  const [stage, setStage] = useState<"idle" | "beam" | "expand" | "flash">("idle");
  const hasNavigated = useRef(false);

  useEffect(() => {
    if (!active) {
      setStage("idle");
      hasNavigated.current = false;
      return;
    }

    // Phase 1: Light beams ignite
    setStage("beam");

    // Phase 2: Beams expand across screen
    const t1 = setTimeout(() => {
      setStage("expand");
    }, 300);

    // Phase 3: Full flash and navigate
    const t2 = setTimeout(() => {
      setStage("flash");
    }, 600);

    // Phase 4: Navigate after flash fills screen
    const t3 = setTimeout(() => {
      if (!hasNavigated.current) {
        hasNavigated.current = true;
        router.push(destination);
      }
    }, 850);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
    };
  }, [active, destination, router]);

  if (!active || stage === "idle") return null;

  return (
    <div className="fixed inset-0 z-[200] pointer-events-none overflow-hidden">
      {/* 1. Backdrop darkening */}
      <div
        className="absolute inset-0 bg-black transition-opacity duration-300"
        style={{ opacity: stage === "beam" ? 0.6 : stage === "expand" ? 0.8 : 1 }}
      />

      {/* 2. Central radiant light burst */}
      <div
        className="absolute top-1/2 left-1/2 rounded-full transition-all ease-out"
        style={{
          width: stage === "beam" ? "120px" : stage === "expand" ? "300vmax" : "400vmax",
          height: stage === "beam" ? "120px" : stage === "expand" ? "300vmax" : "400vmax",
          transform: "translate(-50%, -50%)",
          background: "radial-gradient(circle, rgba(255,255,255,1) 0%, rgba(0,192,249,0.8) 30%, rgba(51,149,255,0.4) 60%, transparent 100%)",
          opacity: 1,
          transitionDuration: stage === "beam" ? "200ms" : stage === "expand" ? "400ms" : "250ms",
        }}
      />

      {/* 3. Vertical laser spine */}
      <div
        className="absolute left-1/2 top-0 bottom-0 -translate-x-1/2 bg-white transition-all ease-out"
        style={{
          width: stage === "beam" ? "3px" : stage === "expand" ? "100vw" : "100vw",
          opacity: 1,
          transitionDuration: "300ms",
          boxShadow: "0 0 40px #00C0F9, 0 0 80px #3395FF, 0 0 120px #fff",
        }}
      />

      {/* 4. Horizontal laser blade */}
      <div
        className="absolute top-1/2 left-0 right-0 -translate-y-1/2 bg-white transition-all ease-out"
        style={{
          height: stage === "beam" ? "2px" : stage === "expand" ? "100vh" : "100vh",
          opacity: 1,
          transitionDuration: "300ms",
          boxShadow: "0 0 40px #00C0F9, 0 0 80px #3395FF",
        }}
      />

      {/* 5. Final white wash */}
      {stage === "flash" && (
        <div className="absolute inset-0 bg-white animate-in fade-in duration-200" />
      )}
    </div>
  );
}
