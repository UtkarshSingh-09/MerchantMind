"use client";

import React, { useEffect, useRef } from "react";

interface SingularityCoreCanvasProps {
  opacity?: number;
}

export function SingularityCoreCanvas({ opacity = 1 }: SingularityCoreCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const gl = canvas.getContext("webgl") || (canvas.getContext("experimental-webgl") as WebGLRenderingContext | null);
    if (!gl) return;

    let width = (canvas.width = canvas.clientWidth || window.innerWidth);
    let height = (canvas.height = canvas.clientHeight || window.innerHeight);

    const vs = `
      attribute vec2 a_position;
      varying vec2 v_uv;
      void main() {
        v_uv = a_position * 0.5 + 0.5;
        gl_Position = vec4(a_position, 0.0, 1.0);
      }
    `;

    const fs = `
      precision highp float;
      varying vec2 v_uv;
      uniform float u_time;
      uniform vec2 u_resolution;
      uniform vec2 u_mouse;

      // Fast procedural hash & noise
      float hash(vec2 p) {
        p = fract(p * vec2(123.34, 456.21));
        p += dot(p, p + 45.32);
        return fract(p.x * p.y);
      }

      float noise(vec2 st) {
        vec2 i = floor(st);
        vec2 f = fract(st);
        float a = hash(i);
        float b = hash(i + vec2(1.0, 0.0));
        float c = hash(i + vec2(0.0, 1.0));
        float d = hash(i + vec2(1.0, 1.0));
        vec2 u = f * f * (3.0 - 2.0 * f);
        return mix(a, b, u.x) + (c - a) * u.y * (1.0 - u.x) + (d - b) * u.y * u.x;
      }

      float fbm(vec2 st) {
        float value = 0.0;
        float amplitude = 0.5;
        for (int i = 0; i < 4; i++) {
          value += amplitude * noise(st);
          st *= 2.1;
          amplitude *= 0.5;
        }
        return value;
      }

      void main() {
        vec2 uv = (v_uv - 0.5) * u_resolution / min(u_resolution.x, u_resolution.y);
        float dist = length(uv);
        float angle = atan(uv.y, uv.x);
        
        // 1. Radiant Singularity Core
        float coreGlow = smoothstep(0.38, 0.0, dist) * 0.85;
        float innerSingularity = smoothstep(0.12, 0.0, dist) * 1.6;
        
        // 2. Gravitational Energy Rays
        float rays = 0.0;
        for (int i = 0; i < 8; i++) {
          float offset = float(i) * (6.28318 / 8.0);
          rays += pow(abs(sin(angle * 4.0 + u_time * 0.4 + offset)), 18.0);
        }
        rays *= smoothstep(0.55, 0.05, dist) * 0.45;

        // 3. Concentric Orbiting Photon Rings
        float ring1 = smoothstep(0.008, 0.0, abs(dist - 0.22)) * (0.6 + 0.4 * sin(angle * 6.0 + u_time * 1.5));
        float ring2 = smoothstep(0.006, 0.0, abs(dist - 0.35)) * (0.5 + 0.5 * sin(angle * 12.0 - u_time * 1.2));
        float ring3 = smoothstep(0.005, 0.0, abs(dist - 0.48)) * 0.3;

        // 4. Inflowing Spiral Particle Dust
        vec2 spiralUv = vec2(
          dist * cos(angle + dist * 3.5 - u_time * 0.3),
          dist * sin(angle + dist * 3.5 - u_time * 0.3)
        );
        float spiralDust = fbm(spiralUv * 8.0) * smoothstep(0.65, 0.1, dist) * 0.35;

        // Composite Colors
        vec3 cyanTint = vec3(0.0, 0.75, 0.98);
        vec3 blueTint = vec3(0.2, 0.58, 1.0);
        vec3 coreWhite = vec3(0.95, 0.98, 1.0);

        vec3 color = vec3(0.0);
        color += blueTint * (coreGlow + rays + spiralDust);
        color += cyanTint * (ring1 + ring2 + ring3 + coreGlow * 0.5);
        color += coreWhite * innerSingularity;

        gl_FragColor = vec4(color, 1.0);
      }
    `;

    function createShader(type: number, src: string) {
      const s = gl!.createShader(type)!;
      gl!.shaderSource(s, src);
      gl!.compileShader(s);
      return s;
    }

    const prog = gl.createProgram()!;
    gl.attachShader(prog, createShader(gl.VERTEX_SHADER, vs));
    gl.attachShader(prog, createShader(gl.FRAGMENT_SHADER, fs));
    gl.linkProgram(prog);
    gl.useProgram(prog);

    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);

    const pos = gl.getAttribLocation(prog, "a_position");
    gl.enableVertexAttribArray(pos);
    gl.vertexAttribPointer(pos, 2, gl.FLOAT, false, 0, 0);

    const uTime = gl.getUniformLocation(prog, "u_time");
    const uRes = gl.getUniformLocation(prog, "u_resolution");
    const uMouse = gl.getUniformLocation(prog, "u_mouse");

    let mouse = { x: width / 2, y: height / 2 };
    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      if (rect.width && rect.height) {
        mouse.x = e.clientX - rect.left;
        mouse.y = e.clientY - rect.top;
      }
    };
    window.addEventListener("mousemove", handleMouseMove);

    let animationId: number;
    const render = (t: number) => {
      if (canvas.clientWidth !== width || canvas.clientHeight !== height) {
        width = canvas.width = canvas.clientWidth || window.innerWidth;
        height = canvas.height = canvas.clientHeight || window.innerHeight;
        gl.viewport(0, 0, width, height);
      }

      if (uTime) gl.uniform1f(uTime, t * 0.001);
      if (uRes) gl.uniform2f(uRes, width, height);
      if (uMouse) gl.uniform2f(uMouse, mouse.x, mouse.y);

      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      animationId = requestAnimationFrame(render);
    };

    animationId = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener("mousemove", handleMouseMove);
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
