"use client";

import React, { useEffect, useRef } from "react";
import * as THREE from "three";

interface PlasmaTorusCanvasProps {
  opacity?: number;
}

export function PlasmaTorusCanvas({ opacity = 1 }: PlasmaTorusCanvasProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    let width = container.clientWidth || window.innerWidth;
    let height = container.clientHeight || window.innerHeight;

    // Dedicated Scene & Camera (Positioned for wide framing)
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 2000);
    camera.position.z = 540;

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    const group = new THREE.Group();
    scene.add(group);

    // 1. Primary Luminous Wireframe Plasma Knot (Wider 130px radius with slimmer 22px tube for open text center)
    const knotGeom = new THREE.TorusKnotGeometry(130, 22, 180, 26, 2, 3);
    const wireMat = new THREE.MeshBasicMaterial({
      color: 0x3b82f6,
      wireframe: true,
      transparent: true,
      opacity: 0.16,
      blending: THREE.AdditiveBlending,
    });
    const wireMesh = new THREE.Mesh(knotGeom, wireMat);
    group.add(wireMesh);

    // 2. High-Density Refined Particle Lattice (Subtle, non-distracting)
    const particleCount = 3200;
    const posAttr = knotGeom.attributes.position;
    const pPositions = new Float32Array(particleCount * 3);
    const pColors = new Float32Array(particleCount * 3);

    const c1 = new THREE.Color(0x3b82f6); // Soft blue
    const c2 = new THREE.Color(0x60a5fa); // Calm sky blue
    const c3 = new THREE.Color(0x94a3b8); // Muted slate silver

    for (let i = 0; i < particleCount; i++) {
      const idx = Math.floor(Math.random() * (posAttr.count - 1));
      pPositions[i * 3] = posAttr.getX(idx) + (Math.random() - 0.5) * 6;
      pPositions[i * 3 + 1] = posAttr.getY(idx) + (Math.random() - 0.5) * 6;
      pPositions[i * 3 + 2] = posAttr.getZ(idx) + (Math.random() - 0.5) * 6;

      const col = i % 3 === 0 ? c1 : i % 3 === 1 ? c2 : c3;
      pColors[i * 3] = col.r;
      pColors[i * 3 + 1] = col.g;
      pColors[i * 3 + 2] = col.b;
    }

    const pGeom = new THREE.BufferGeometry();
    pGeom.setAttribute("position", new THREE.BufferAttribute(pPositions, 3));
    pGeom.setAttribute("color", new THREE.BufferAttribute(pColors, 3));

    const pMat = new THREE.PointsMaterial({
      size: 1.8,
      vertexColors: true,
      transparent: true,
      opacity: 0.5,
      blending: THREE.AdditiveBlending,
      sizeAttenuation: true,
    });
    const particles = new THREE.Points(pGeom, pMat);
    group.add(particles);

    // 3. Subtle Hairline Orbiting Rings
    const ring1Geom = new THREE.TorusGeometry(165, 1.2, 16, 100);
    const ring1Mat = new THREE.MeshBasicMaterial({
      color: 0x3b82f6,
      wireframe: true,
      transparent: true,
      opacity: 0.25,
      blending: THREE.AdditiveBlending,
    });
    const ring1 = new THREE.Mesh(ring1Geom, ring1Mat);
    group.add(ring1);

    const ring2Geom = new THREE.TorusGeometry(205, 1.2, 16, 100);
    const ring2Mat = new THREE.MeshBasicMaterial({
      color: 0x64748b,
      wireframe: true,
      transparent: true,
      opacity: 0.2,
      blending: THREE.AdditiveBlending,
    });
    const ring2 = new THREE.Mesh(ring2Geom, ring2Mat);
    ring2.rotation.x = Math.PI / 2.8;
    group.add(ring2);

    // 4. Soft Ambient Core Sphere
    const coreGeom = new THREE.SphereGeometry(30, 20, 20);
    const coreMat = new THREE.MeshBasicMaterial({
      color: 0x60a5fa,
      wireframe: true,
      transparent: true,
      opacity: 0.18,
      blending: THREE.AdditiveBlending,
    });
    const core = new THREE.Mesh(coreGeom, coreMat);
    group.add(core);

    // Mouse Interaction
    let mouseX = 0,
      mouseY = 0;
    const handleMouseMove = (e: MouseEvent) => {
      mouseX = (e.clientX / width) * 2 - 1;
      mouseY = -(e.clientY / height) * 2 + 1;
    };
    window.addEventListener("mousemove", handleMouseMove);

    const handleResize = () => {
      if (!container) return;
      width = container.clientWidth || window.innerWidth;
      height = container.clientHeight || window.innerHeight;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    };
    window.addEventListener("resize", handleResize);

    let animationId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animationId = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();

      // Continuous 3D Orbital Twisting: Slow, relaxing, eye-friendly flow
      group.rotation.x = elapsed * 0.07 + mouseY * 0.1;
      group.rotation.y = elapsed * 0.1 + mouseX * 0.12;
      group.rotation.z = elapsed * 0.03;

      ring1.rotation.z = -elapsed * 0.08;
      ring2.rotation.y = elapsed * 0.12;
      core.rotation.y = elapsed * 0.15;

      // Subtle breathing pulse (very slow and calming)
      const breathe = 1.0 + Math.sin(elapsed * 0.8) * 0.02;
      wireMesh.scale.set(breathe, breathe, breathe);

      renderer.render(scene, camera);
    };

    animate();

    return () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("resize", handleResize);
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 w-full h-full pointer-events-none transition-opacity duration-150"
      style={{ opacity }}
    />
  );
}
