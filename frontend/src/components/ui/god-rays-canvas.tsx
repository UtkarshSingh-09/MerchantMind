"use client";

import React, { useEffect, useRef } from "react";

interface GodRaysCanvasProps {
  intensity?: number;
  className?: string;
}

export function GodRaysCanvas({
  intensity = 1.0,
  className = "",
}: GodRaysCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const gl = canvas.getContext("webgl");
    if (!gl) return;

    const vsSource = `
      attribute vec2 a_position;
      varying vec2 v_uv;
      void main() {
        v_uv = (a_position + 1.0) * 0.5;
        gl_Position = vec4(a_position, 0.0, 1.0);
      }
    `;

    const fsSource = `
      precision highp float;
      uniform vec2 u_resolution;
      uniform float u_time;
      uniform float u_intensity;
      varying vec2 v_uv;

      // Pseudo-random noise
      float hash(vec2 p) {
        return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
      }

      float noise(vec2 p) {
        vec2 i = floor(p);
        vec2 f = fract(p);
        vec2 u = f * f * (3.0 - 2.0 * f);
        return mix(mix(hash(i + vec2(0.0, 0.0)), hash(i + vec2(1.0, 0.0)), u.x),
                   mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
      }

      float fbm(vec2 p) {
        float v = 0.0;
        float a = 0.5;
        vec2 shift = vec2(100.0);
        mat2 rot = mat2(cos(0.5), sin(0.5), -sin(0.5), cos(0.5));
        for (int i = 0; i < 4; ++i) {
          v += a * noise(p);
          p = rot * p * 2.0 + shift;
          a *= 0.5;
        }
        return v;
      }

      void main() {
        vec2 uv = gl_FragCoord.xy / u_resolution.xy;
        vec2 p = uv - vec2(0.5, 0.95); // Light source origin near top-center
        p.x *= u_resolution.x / u_resolution.y;

        float angle = atan(p.y, p.x);
        float dist = length(p);

        // Volumetric light rays calculation
        float ray1 = sin(angle * 12.0 + u_time * 1.2) * 0.5 + 0.5;
        float ray2 = sin(angle * 24.0 - u_time * 0.8) * 0.5 + 0.5;
        float ray3 = sin(angle * 38.0 + u_time * 1.8) * 0.5 + 0.5;
        float rays = (ray1 * 0.5 + ray2 * 0.3 + ray3 * 0.2);

        // Atmospheric dust turbulence
        float clouds = fbm(vec2(angle * 4.0, dist * 2.0 - u_time * 0.3));
        rays = pow(rays * clouds, 1.3) * 2.2;

        // Attenuation over distance
        float attenuation = 1.0 / (1.0 + dist * 1.8);
        float beam = rays * attenuation * u_intensity;

        // Color grading: Deep Midnight -> Electric Azure -> Neon Cyan -> Pure White Core
        vec3 colBlack = vec3(0.01, 0.02, 0.05);
        vec3 colBlue  = vec3(0.12, 0.38, 0.95);
        vec3 colCyan  = vec3(0.0, 0.82, 0.98);
        vec3 colWhite = vec3(1.0, 1.0, 1.0);

        vec3 color = mix(colBlack, colBlue, clamp(beam * 1.5, 0.0, 1.0));
        color = mix(color, colCyan, clamp((beam - 0.4) * 2.0, 0.0, 1.0));
        color = mix(color, colWhite, clamp((beam - 0.85) * 3.0, 0.0, 1.0));

        // Core light flare
        float core = smoothstep(0.35, 0.0, dist) * u_intensity * 1.8;
        color += colWhite * core;

        gl_FragColor = vec4(color, clamp(beam * 1.4 + core, 0.0, 1.0));
      }
    `;

    function createShader(gl: WebGLRenderingContext, type: number, source: string) {
      const shader = gl.createShader(type);
      if (!shader) return null;
      gl.shaderSource(shader, source);
      gl.compileShader(shader);
      if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
        gl.deleteShader(shader);
        return null;
      }
      return shader;
    }

    const vs = createShader(gl, gl.VERTEX_SHADER, vsSource);
    const fs = createShader(gl, gl.FRAGMENT_SHADER, fsSource);
    if (!vs || !fs) return;

    const program = gl.createProgram();
    if (!program) return;
    gl.attachShader(program, vs);
    gl.attachShader(program, fs);
    gl.linkProgram(program);

    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) return;

    gl.useProgram(program);

    const positionBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
    gl.bufferData(
      gl.ARRAY_BUFFER,
      new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1]),
      gl.STATIC_DRAW
    );

    const posAttr = gl.getAttribLocation(program, "a_position");
    gl.enableVertexAttribArray(posAttr);
    gl.vertexAttribPointer(posAttr, 2, gl.FLOAT, false, 0, 0);

    const uRes = gl.getUniformLocation(program, "u_resolution");
    const uTime = gl.getUniformLocation(program, "u_time");
    const uIntensity = gl.getUniformLocation(program, "u_intensity");

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = window.innerWidth * dpr;
      canvas.height = window.innerHeight * dpr;
      gl.viewport(0, 0, canvas.width, canvas.height);
      gl.uniform2f(uRes, canvas.width, canvas.height);
    };

    window.addEventListener("resize", resize);
    resize();

    let animationId: number;
    let startTime = performance.now();

    const render = (time: number) => {
      animationId = requestAnimationFrame(render);
      const elapsed = (time - startTime) * 0.001;

      gl.uniform1f(uTime, elapsed);
      gl.uniform1f(uIntensity, intensity);
      gl.drawArrays(gl.TRIANGLES, 0, 6);
    };

    animationId = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener("resize", resize);
      gl.deleteProgram(program);
      gl.deleteShader(vs);
      gl.deleteShader(fs);
      gl.deleteBuffer(positionBuffer);
    };
  }, [intensity]);

  return (
    <canvas
      ref={canvasRef}
      className={`absolute inset-0 w-full h-full pointer-events-none ${className}`}
    />
  );
}
