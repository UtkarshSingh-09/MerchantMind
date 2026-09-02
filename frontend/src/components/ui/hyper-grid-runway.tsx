"use client";

import React, { useEffect, useRef, useState } from "react";

interface HyperGridRunwayProps {
  opacity?: number;
}

export function HyperGridRunway({ opacity = 1 }: HyperGridRunwayProps) {
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      setMousePos({ x, y });
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  if (opacity <= 0.01) return null;

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 w-full h-full pointer-events-none overflow-hidden select-none bg-[#02050B] transition-opacity duration-300"
      style={{ opacity }}
    >
      {/* 1. Monumental Horizon Light Burst & Atmosphere */}
      <div className="absolute top-[32%] left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1100px] h-[550px] bg-radial from-[#3395FF]/28 via-[#00C0F9]/12 to-transparent blur-[140px] pointer-events-none" />

      {/* 2. Horizon Laser Datum Lines (Double Glowing Line) */}
      <div className="absolute top-[42%] left-0 right-0 h-[1.5px] bg-gradient-to-r from-transparent via-[#00C0F9]/80 to-transparent shadow-[0_0_15px_#00C0F9]" />
      <div className="absolute top-[42%] left-0 right-0 h-[8px] bg-gradient-to-r from-transparent via-[#3395FF]/40 to-transparent blur-md" />

      {/* 3. 3D Perspective Ground Grid Runway (High Contrast, Wide Angle) */}
      <div
        className="absolute inset-x-0 bottom-0 top-[25%] origin-bottom overflow-hidden"
        style={{
          perspective: "800px",
          transformStyle: "preserve-3d",
        }}
      >
        {/* Base Glowing Grid Plane */}
        <div
          className="absolute inset-0 w-full h-[300%] origin-bottom"
          style={{
            transform: "rotateX(75deg) translateY(-25%)",
            backgroundImage: `
              linear-gradient(to right, rgba(51, 149, 255, 0.32) 1.5px, transparent 1.5px),
              linear-gradient(to bottom, rgba(51, 149, 255, 0.32) 1.5px, transparent 1.5px)
            `,
            backgroundSize: "70px 70px",
            maskImage:
              "linear-gradient(to top, rgba(0,0,0,1) 40%, rgba(0,0,0,0.6) 75%, transparent 100%)",
            WebkitMaskImage:
              "linear-gradient(to top, rgba(0,0,0,1) 40%, rgba(0,0,0,0.6) 75%, transparent 100%)",
          }}
        />

        {/* Dynamic Cursor Laser Spotlight on Grid */}
        <div
          className="absolute inset-0 w-full h-[300%] origin-bottom transition-opacity duration-200"
          style={{
            transform: "rotateX(75deg) translateY(-25%)",
            backgroundImage: `
              linear-gradient(to right, rgba(0, 240, 255, 0.85) 2px, transparent 2px),
              linear-gradient(to bottom, rgba(0, 240, 255, 0.85) 2px, transparent 2px)
            `,
            backgroundSize: "70px 70px",
            maskImage: `radial-gradient(circle 420px at ${mousePos.x}px ${mousePos.y * 1.5}px, black 25%, transparent 85%)`,
            WebkitMaskImage: `radial-gradient(circle 420px at ${mousePos.x}px ${mousePos.y * 1.5}px, black 25%, transparent 85%)`,
          }}
        />

        {/* Central Runway Speed Tracks */}
        <div
          className="absolute left-1/2 -translate-x-1/2 w-[340px] h-[300%] origin-bottom pointer-events-none"
          style={{
            transform: "rotateX(75deg) translateY(-25%)",
            background:
              "linear-gradient(90deg, transparent, rgba(51,149,255,0.15), rgba(0,192,249,0.35), rgba(51,149,255,0.15), transparent)",
            boxShadow: "0 0 40px rgba(0,192,249,0.3)",
          }}
        />
      </div>

      {/* 4. Upper Atmospheric Grid (Subtle Horizon Reflection) */}
      <div
        className="absolute inset-x-0 top-0 bottom-[60%] origin-top overflow-hidden opacity-40"
        style={{
          perspective: "800px",
          transformStyle: "preserve-3d",
        }}
      >
        <div
          className="absolute inset-0 w-full h-[200%] origin-top"
          style={{
            transform: "rotateX(-75deg) translateY(-20%)",
            backgroundImage: `
              linear-gradient(to right, rgba(51, 149, 255, 0.18) 1px, transparent 1px),
              linear-gradient(to bottom, rgba(51, 149, 255, 0.18) 1px, transparent 1px)
            `,
            backgroundSize: "80px 80px",
            maskImage:
              "linear-gradient(to bottom, rgba(0,0,0,0.8) 10%, rgba(0,0,0,0.3) 60%, transparent 100%)",
            WebkitMaskImage:
              "linear-gradient(to bottom, rgba(0,0,0,0.8) 10%, rgba(0,0,0,0.3) 60%, transparent 100%)",
          }}
        />
      </div>

      {/* 5. Vignette Depth Overlay */}
      <div className="absolute inset-0 bg-radial from-transparent via-black/30 to-black pointer-events-none" />
    </div>
  );
}
