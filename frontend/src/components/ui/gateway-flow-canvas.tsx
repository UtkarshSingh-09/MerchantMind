"use client";

import React, { useEffect, useRef } from "react";

interface GatewayFlowCanvasProps {
  opacity?: number;
}

export function GatewayFlowCanvas({ opacity = 1 }: GatewayFlowCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let width = 0;
    let height = 0;
    let explosions: Array<{ x: number; y: number; radius: number; life: number }> = [];

    function resize() {
      const dpr = window.devicePixelRatio || 1;
      width = canvas!.clientWidth || window.innerWidth;
      height = canvas!.clientHeight || window.innerHeight;
      canvas!.width = width * dpr;
      canvas!.height = height * dpr;
      ctx!.scale(dpr, dpr);
    }

    resize();
    window.addEventListener("resize", resize);

    const handleClick = (e: MouseEvent) => {
      const rect = canvas!.getBoundingClientRect();
      explosions.push({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
        radius: 0,
        life: 1,
      });
    };
    window.addEventListener("click", handleClick);

    const paths: Array<{
      isLeft: boolean;
      startY: number;
      targetY: number;
      color: string;
      speed: number;
      particles: Array<{ t: number; speed: number }>;
    }> = [];

    const numPaths = 70;
    const colors = ["rgba(51, 149, 255, 0.45)", "rgba(0, 192, 249, 0.4)", "rgba(244, 63, 94, 0.35)", "rgba(255, 255, 255, 0.3)"];

    for (let i = 0; i < numPaths; i++) {
      paths.push({
        isLeft: i % 3 !== 0,
        startY: (i / numPaths) * height * 1.3 - height * 0.15,
        targetY: (i % 3 === 0 ? 0.28 : i % 3 === 1 ? 0.5 : 0.72) * height,
        color: colors[i % colors.length],
        speed: 0.0018 + Math.random() * 0.0025,
        particles: [
          { t: Math.random(), speed: 0.002 + Math.random() * 0.003 },
          { t: Math.random(), speed: 0.0015 + Math.random() * 0.0025 },
        ],
      });
    }

    function getBezierPoint(
      t: number,
      p0: { x: number; y: number },
      p1: { x: number; y: number },
      p2: { x: number; y: number },
      p3: { x: number; y: number }
    ) {
      const u = 1 - t;
      return {
        x: u ** 3 * p0.x + 3 * u ** 2 * t * p1.x + 3 * u * t ** 2 * p2.x + t ** 3 * p3.x,
        y: u ** 3 * p0.y + 3 * u ** 2 * t * p1.y + 3 * u * t ** 2 * p2.y + t ** 3 * p3.y,
      };
    }

    let animationFrameId: number;

    function render() {
      ctx!.clearRect(0, 0, width, height);
      const centerX = width * 0.38; // Asymmetric focal point staging left silos

      // Update shockwave explosions
      explosions.forEach((exp) => {
        exp.radius += 12;
        exp.life -= 0.015;
      });
      explosions = explosions.filter((exp) => exp.life > 0);

      paths.forEach((path) => {
        const p0 = { x: path.isLeft ? 0 : width, y: path.startY };
        const p1 = { x: path.isLeft ? centerX * 0.45 : width - (width - centerX) * 0.45, y: path.startY };
        const p2 = { x: path.isLeft ? centerX * 0.8 : width - (width - centerX) * 0.8, y: path.targetY };
        const p3 = { x: centerX, y: path.targetY };

        // Draw curved glowing bezier stream
        ctx!.beginPath();
        ctx!.moveTo(p0.x, p0.y);
        ctx!.bezierCurveTo(p1.x, p1.y, p2.x, p2.y, p3.x, p3.y);
        ctx!.strokeStyle = path.color;
        ctx!.lineWidth = 1.0;
        ctx!.setLineDash([2, 5]);
        ctx!.stroke();
        ctx!.setLineDash([]);

        // Draw travelling light particles
        path.particles.forEach((p) => {
          p.t += p.speed;
          if (p.t > 1) {
            p.t = 0;
            path.startY += (Math.random() - 0.5) * 8;
          }

          let pos = getBezierPoint(p.t, p0, p1, p2, p3);

          // Shockwave distortion
          let dxTotal = 0,
            dyTotal = 0;
          explosions.forEach((exp) => {
            let dx = pos.x - exp.x;
            let dy = pos.y - exp.y;
            let dist = Math.hypot(dx, dy);
            if (dist < exp.radius + 100 && dist > exp.radius - 100) {
              let force = (1 - Math.abs(dist - exp.radius) / 100) * exp.life;
              dxTotal += (dx / dist) * force * 60;
              dyTotal += (dy / dist) * force * 60;
            }
          });

          pos.x += dxTotal;
          pos.y += dyTotal;

          // Glowing particle head
          ctx!.fillStyle = "#ffffff";
          ctx!.shadowColor = "#3395ff";
          ctx!.shadowBlur = 8;
          ctx!.fillRect(pos.x - 1.5, pos.y - 1.5, 3, 3);
          ctx!.shadowBlur = 0;
        });
      });

      animationFrameId = requestAnimationFrame(render);
    }

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("resize", resize);
      window.removeEventListener("click", handleClick);
    };
  }, []);

  return (
    <div
      className="absolute inset-0 w-full h-full pointer-events-none transition-opacity duration-150"
      style={{ opacity }}
    >
      <canvas ref={canvasRef} className="w-full h-full block" />
    </div>
  );
}
