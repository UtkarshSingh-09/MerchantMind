"use client";

import React, { useEffect, useRef } from "react";
import * as THREE from "three";

export function ParticleConstellation() {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    let width = container.clientWidth || window.innerWidth;
    let height = container.clientHeight || window.innerHeight;

    // Scene & Camera
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x000000, 0.00035);

    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 4000);
    camera.position.z = 1200;

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // --- Colors ---
    const colors = {
      electricBlue: new THREE.Color(0x3395ff),
      cyan: new THREE.Color(0x00c0f9),
      silver: new THREE.Color(0xe2e8f0),
      white: new THREE.Color(0xffffff),
    };

    // Helper: Create Particle Cloud from Geometry
    function createParticleCloud(
      geometry: THREE.BufferGeometry,
      color: THREE.Color,
      size: number,
      opacity: number = 0.8
    ) {
      const material = new THREE.PointsMaterial({
        color: color,
        size: size,
        transparent: true,
        opacity: opacity,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      });
      return new THREE.Points(geometry, material);
    }

    // =========================================================================
    // 1. HERO PARTICLE MONOGRAM SPHERE (Top Scene)
    // =========================================================================
    const heroGroup = new THREE.Group();
    scene.add(heroGroup);

    const heroParticleCount = 16000;
    const heroPositions = new Float32Array(heroParticleCount * 3);
    const heroColors = new Float32Array(heroParticleCount * 3);
    const heroSizes = new Float32Array(heroParticleCount);

    for (let i = 0; i < heroParticleCount; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);
      const radius = 340 + Math.random() * 120;

      heroPositions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      heroPositions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      heroPositions[i * 3 + 2] = radius * Math.cos(phi);

      const mixedColor =
        i % 3 === 0
          ? colors.electricBlue
          : i % 3 === 1
          ? colors.silver
          : colors.cyan;
      heroColors[i * 3] = mixedColor.r;
      heroColors[i * 3 + 1] = mixedColor.g;
      heroColors[i * 3 + 2] = mixedColor.b;

      heroSizes[i] = Math.random() * 2.8 + 1.2;
    }

    const heroGeometry = new THREE.BufferGeometry();
    heroGeometry.setAttribute("position", new THREE.BufferAttribute(heroPositions, 3));
    heroGeometry.setAttribute("color", new THREE.BufferAttribute(heroColors, 3));
    heroGeometry.setAttribute("size", new THREE.BufferAttribute(heroSizes, 1));

    const heroMaterial = new THREE.PointsMaterial({
      size: 2.8,
      vertexColors: true,
      transparent: true,
      opacity: 0.85,
      blending: THREE.AdditiveBlending,
      sizeAttenuation: true,
    });

    const heroParticleSystem = new THREE.Points(heroGeometry, heroMaterial);
    heroGroup.add(heroParticleSystem);

    // =========================================================================
    // 2. RADAR TUNNEL & ARCHITECTURAL MONOLITHS (Stitch Scene)
    // =========================================================================
    const radarMainGroup = new THREE.Group();
    scene.add(radarMainGroup);

    // 2A. Perimeter Architectural Monoliths
    const monoliths = new THREE.Group();

    // Left: Acquiring Bank
    const leftBoxGeom = new THREE.BoxGeometry(200, 700, 200, 15, 40, 15);
    const leftMonolith = createParticleCloud(leftBoxGeom, colors.silver, 1.4, 0.45);
    leftMonolith.position.set(-900, 0, -300);
    monoliths.add(leftMonolith);

    // Right: Payment Processor
    const rightBoxGeom = new THREE.BoxGeometry(250, 900, 250, 20, 50, 20);
    const rightMonolith = createParticleCloud(rightBoxGeom, colors.electricBlue, 1.6, 0.55);
    rightMonolith.position.set(950, 0, -300);
    monoliths.add(rightMonolith);

    // Top: Issuing Bank
    const topGeom = new THREE.CylinderGeometry(500, 500, 150, 64, 10, true);
    const topMonolith = createParticleCloud(topGeom, colors.cyan, 1.3, 0.35);
    topMonolith.rotation.x = Math.PI / 2;
    topMonolith.position.set(0, 600, -400);
    monoliths.add(topMonolith);

    // Bottom: Payment Gateway
    const bottomGeom = new THREE.CylinderGeometry(500, 500, 150, 64, 10, true);
    const bottomMonolith = createParticleCloud(bottomGeom, colors.white, 1.3, 0.35);
    bottomMonolith.rotation.x = Math.PI / 2;
    bottomMonolith.position.set(0, -600, -400);
    monoliths.add(bottomMonolith);

    radarMainGroup.add(monoliths);

    // 2B. Concentric Radar Rings (Dynamic 12 Concentric Orbits)
    const radarRings = new THREE.Group();
    for (let i = 0; i < 12; i++) {
      const radius = 300 + i * 120;
      const segments = 128;
      const ringGeom = new THREE.BufferGeometry();
      const vertices: number[] = [];
      for (let j = 0; j <= segments; j++) {
        const theta = (j / segments) * Math.PI * 2;
        vertices.push(radius * Math.cos(theta), radius * Math.sin(theta), 0);
      }
      ringGeom.setAttribute("position", new THREE.Float32BufferAttribute(vertices, 3));
      const ringMaterial = new THREE.LineBasicMaterial({
        color:
          i % 3 === 0
            ? colors.cyan
            : i % 3 === 1
            ? colors.electricBlue
            : colors.white,
        transparent: true,
        opacity: 0.16 + (1 - i / 12) * 0.25,
      });
      const ring = new THREE.Line(ringGeom, ringMaterial);
      ring.rotation.x = (Math.random() - 0.5) * 0.3;
      ring.rotation.y = (Math.random() - 0.5) * 0.3;
      ring.userData = { speed: 0.0006 * (i + 1) };
      radarRings.add(ring);
    }
    radarMainGroup.add(radarRings);

    // 2C. Four Inner Geometric Particle Clusters
    const clusters = new THREE.Group();

    const icoGeom = new THREE.IcosahedronGeometry(70, 5);
    const cluster1 = createParticleCloud(icoGeom, colors.cyan, 1.5, 0.85);
    cluster1.position.set(0, 350, 100);
    clusters.add(cluster1);

    const torusGeom = new THREE.TorusGeometry(60, 25, 20, 100);
    const cluster2 = createParticleCloud(torusGeom, colors.silver, 1.5, 0.85);
    cluster2.position.set(450, 250, 100);
    clusters.add(cluster2);

    const sphereGeom1 = new THREE.SphereGeometry(70, 32, 32);
    const cluster3 = createParticleCloud(sphereGeom1, colors.electricBlue, 1.6, 0.85);
    cluster3.position.set(-450, -250, 100);
    clusters.add(cluster3);

    const sphereGeom2 = new THREE.SphereGeometry(80, 32, 32);
    const cluster4 = createParticleCloud(sphereGeom2, colors.white, 1.5, 0.85);
    cluster4.position.set(450, -250, 100);
    clusters.add(cluster4);

    radarMainGroup.add(clusters);

    // 2D. Interactive Mouse-Responsive Particles (2,000 live floating particles)
    const particleCount = 2000;
    const particleGeometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const velocities = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 2000;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 2000;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 1000;

      velocities[i * 3] = (Math.random() - 0.5) * 1.5;
      velocities[i * 3 + 1] = (Math.random() - 0.5) * 1.5;
      velocities[i * 3 + 2] = (Math.random() - 0.5) * 1.5;
    }

    particleGeometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    const particleMaterial = new THREE.PointsMaterial({
      color: colors.cyan,
      size: 2.0,
      transparent: true,
      opacity: 0.6,
      blending: THREE.AdditiveBlending,
    });
    const interactiveParticles = new THREE.Points(particleGeometry, particleMaterial);
    radarMainGroup.add(interactiveParticles);

    // =========================================================================
    // 3. AMBIENT STARFIELD (6,000 Stars)
    // =========================================================================
    const starGeom = new THREE.BufferGeometry();
    const starPositions: number[] = [];
    for (let i = 0; i < 6000; i++) {
      starPositions.push(
        (Math.random() - 0.5) * 5000,
        (Math.random() - 0.5) * 5000,
        (Math.random() - 0.5) * 4000
      );
    }
    starGeom.setAttribute("position", new THREE.Float32BufferAttribute(starPositions, 3));
    const stars = new THREE.Points(
      starGeom,
      new THREE.PointsMaterial({ color: 0xffffff, size: 0.8, transparent: true, opacity: 0.35 })
    );
    scene.add(stars);

    // =========================================================================
    // 4. INTERACTION & SCROLL ANIMATION LOOP
    // =========================================================================
    let mouseX = 0,
      mouseY = 0;
    let targetX = 0,
      targetY = 0;
    let scrollY = 0;

    const handleMouseMove = (e: MouseEvent) => {
      targetX = (e.clientX - width / 2) / 80;
      targetY = (e.clientY - height / 2) / 80;
      mouseX = (e.clientX / width) * 2 - 1;
      mouseY = -(e.clientY / height) * 2 + 1;
    };
    window.addEventListener("mousemove", handleMouseMove);

    const handleScroll = () => {
      scrollY = window.scrollY || window.pageYOffset;
    };
    window.addEventListener("scroll", handleScroll, { passive: true });

    let animationFrameId: number;

    const animate = (t: number) => {
      animationFrameId = requestAnimationFrame(animate);
      const time = t * 0.001;

      // Total scroll range mapping
      const windowH = typeof window !== "undefined" ? window.innerHeight : 800;
      const totalScrollRange = windowH * 2.2;
      const scrollRatio = Math.min(scrollY / totalScrollRange, 1.2);

      // Smooth Camera Parallax
      camera.position.x += (targetX * 3 - camera.position.x) * 0.05;
      camera.position.y += (-targetY * 3 - camera.position.y) * 0.05;
      camera.lookAt(scene.position);

      // Hero Sphere Expansion: expands "big, big, big, big, big" & disperses
      const heroProgress = Math.min(scrollY / (windowH * 0.5), 1.0);
      const heroScale = 1.0 + Math.pow(heroProgress * 3.2, 2.5);
      heroGroup.scale.set(heroScale, heroScale, heroScale);
      heroGroup.rotation.y = time * 0.08;
      heroGroup.rotation.x = time * 0.04;

      if (heroProgress < 0.25) {
        heroMaterial.opacity = 0.85;
      } else {
        heroMaterial.opacity = Math.max(0, 0.85 * (1.0 - (heroProgress - 0.25) / 0.5));
      }

      // Radar Tunnel & Monoliths reveal as hero sphere opens and travels forward
      if (scrollY < windowH * 0.15) {
        radarMainGroup.visible = false;
      } else {
        radarMainGroup.visible = true;
        const radarProgress = Math.min(Math.max((scrollY - windowH * 0.15) / (windowH * 0.85), 0), 1.0);
        const deepProgress = Math.max(0, (scrollY - windowH * 1.2) / (windowH * 1.0));
        
        // Moves from z: -600 to 0 (Chapter 2) to +200 (Chapter 3 deep flight)
        radarMainGroup.position.z = -600 + radarProgress * 600 + deepProgress * 200;
        const radarScale = 0.35 + radarProgress * 0.65 + deepProgress * 0.15;
        radarMainGroup.scale.set(radarScale, radarScale, radarScale);
      }

      // Radar Rings rotation
      radarRings.children.forEach((ring, i) => {
        ring.rotation.z += (ring.userData.speed || 0.0005);
        ring.rotation.y += 0.0002 * (i % 2 === 0 ? 1 : -1);
      });

      // Clusters rotation & float
      clusters.children.forEach((cluster, i) => {
        cluster.rotation.y += 0.014;
        cluster.rotation.x += 0.007;
        cluster.position.y += Math.sin(time * 2 + i) * 0.2;
      });

      // Monoliths rotation
      monoliths.children.forEach((m) => {
        m.rotation.y += 0.0015;
      });

      // Interactive Particles Repulsion Logic
      const posArray = interactiveParticles.geometry.attributes.position.array as Float32Array;
      for (let i = 0; i < particleCount; i++) {
        posArray[i * 3] += velocities[i * 3];
        posArray[i * 3 + 1] += velocities[i * 3 + 1];
        posArray[i * 3 + 2] += velocities[i * 3 + 2];

        // Repel from mouse cursor
        const dx = posArray[i * 3] - mouseX * 1000;
        const dy = posArray[i * 3 + 1] - mouseY * 1000;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < 220) {
          posArray[i * 3] += dx * 0.02;
          posArray[i * 3 + 1] += dy * 0.02;
        }

        // Space Boundaries wrapping
        if (Math.abs(posArray[i * 3]) > 1000) posArray[i * 3] *= -0.95;
        if (Math.abs(posArray[i * 3 + 1]) > 1000) posArray[i * 3 + 1] *= -0.95;
        if (Math.abs(posArray[i * 3 + 2]) > 500) posArray[i * 3 + 2] *= -0.95;
      }
      interactiveParticles.geometry.attributes.position.needsUpdate = true;

      stars.rotation.y = time * 0.01;

      renderer.render(scene, camera);
    };

    animationFrameId = requestAnimationFrame(animate);

    const handleResize = () => {
      if (!container) return;
      width = container.clientWidth || window.innerWidth;
      height = container.clientHeight || window.innerHeight;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    };

    window.addEventListener("resize", handleResize);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("scroll", handleScroll);
      window.removeEventListener("resize", handleResize);
      if (container && renderer.domElement) {
        container.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="fixed inset-0 z-0 pointer-events-none w-full h-full"
      style={{ background: "transparent" }}
    />
  );
}
