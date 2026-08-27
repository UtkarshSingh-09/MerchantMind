"use client";

import React, { useEffect, useRef } from "react";

interface NodePoint {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  label?: string;
  isHub?: boolean;
}

export function ParticleConstellation() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener("resize", handleResize);

    // Hub nodes inspired by Razorpay Foundation Model
    const hubs = [
      "PAYMENT GATEWAY",
      "ISSUING BANK",
      "ACQUIRING BANK",
      "PAYMENT PROCESSOR",
      "CHECKOUT PERSONALISATION",
      "FRAUD DETECTION",
      "SUCCESS RATE OPTIMIZATION",
      "WHATSAPP COMMERCE",
    ];

    const particles: NodePoint[] = [];
    const count = Math.min(Math.floor((width * height) / 10000), 90);

    for (let i = 0; i < count; i++) {
      const isHub = i < hubs.length;
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        radius: isHub ? 3.5 : Math.random() * 1.5 + 0.8,
        label: isHub ? hubs[i] : undefined,
        isHub,
      });
    }

    let mouseX = width / 2;
    let mouseY = height / 2;
    let isHovering = false;

    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouseX = e.clientX - rect.left;
      mouseY = e.clientY - rect.top;
      isHovering = true;
    };

    const handleMouseLeave = () => {
      isHovering = false;
    };

    window.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseleave", handleMouseLeave);

    const draw = () => {
      ctx.clearRect(0, 0, width, height);

      // Background ambient dark gradient
      const bgGrad = ctx.createRadialGradient(
        width / 2,
        height * 0.4,
        100,
        width / 2,
        height * 0.4,
        width * 0.8
      );
      bgGrad.addColorStop(0, "rgba(51, 149, 255, 0.04)");
      bgGrad.addColorStop(0.5, "rgba(12, 35, 64, 0.02)");
      bgGrad.addColorStop(1, "rgba(0, 0, 0, 0)");
      ctx.fillStyle = bgGrad;
      ctx.fillRect(0, 0, width, height);

      // Update & Draw particles
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;

        if (p.x < 0) p.x = width;
        if (p.x > width) p.x = 0;
        if (p.y < 0) p.y = height;
        if (p.y > height) p.y = 0;

        // Draw particle dot
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = p.isHub ? "#3395FF" : "rgba(255, 255, 255, 0.5)";
        ctx.shadowColor = p.isHub ? "#3395FF" : "rgba(255, 255, 255, 0.2)";
        ctx.shadowBlur = p.isHub ? 12 : 3;
        ctx.fill();
        ctx.shadowBlur = 0;

        // Label for hub nodes
        if (p.label) {
          ctx.font = "9px -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
          ctx.fillStyle = "rgba(148, 163, 184, 0.75)";
          ctx.letterSpacing = "1px";
          ctx.fillText(p.label, p.x + 8, p.y + 3);
        }

        // Connect with nearby particles
        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const dx = p.x - p2.x;
          const dy = p.y - p2.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 130) {
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(p2.x, p2.y);
            const alpha = (1 - dist / 130) * 0.18;
            ctx.strokeStyle = p.isHub || p2.isHub
              ? `rgba(51, 149, 255, ${alpha * 1.5})`
              : `rgba(255, 255, 255, ${alpha})`;
            ctx.lineWidth = p.isHub || p2.isHub ? 0.8 : 0.4;
            ctx.stroke();
          }
        }

        // Connect to mouse pointer if close
        if (isHovering) {
          const dx = p.x - mouseX;
          const dy = p.y - mouseY;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 160) {
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(mouseX, mouseY);
            const alpha = (1 - dist / 160) * 0.35;
            ctx.strokeStyle = `rgba(0, 192, 249, ${alpha})`;
            ctx.lineWidth = 0.8;
            ctx.stroke();
          }
        }
      }

      animationFrameId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseleave", handleMouseLeave);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="pointer-events-none fixed inset-0 z-0 h-full w-full opacity-70"
    />
  );
}
