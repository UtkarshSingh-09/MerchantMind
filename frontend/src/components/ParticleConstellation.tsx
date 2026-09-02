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
    // 3. CHAPTER 4: THREE 3D VOLUMETRIC ISOLATED SILOS (Left-Stage Point Clouds)
    // =========================================================================
    const isolationGroup = new THREE.Group();
    scene.add(isolationGroup);
    isolationGroup.position.set(-360, 0, 0);

    // Silo 1: DISCOVERY (Rotating Icosahedron + Orbit Ring)
    const silo1 = new THREE.Group();
    silo1.position.set(-60, 280, 0);
    const silo1Geom = new THREE.IcosahedronGeometry(85, 4);
    const silo1Cloud = createParticleCloud(silo1Geom, new THREE.Color(0xf43f5e), 1.6, 0.9);
    silo1.add(silo1Cloud);
    const ring1Geom = new THREE.TorusGeometry(120, 2, 16, 64);
    const ring1Cloud = createParticleCloud(ring1Geom, colors.silver, 1.2, 0.45);
    ring1Cloud.rotation.x = Math.PI / 3;
    silo1.add(ring1Cloud);
    isolationGroup.add(silo1);

    // Silo 2: REVENUE ENGINE (Rotating Torus + Concentrated Core)
    const silo2 = new THREE.Group();
    silo2.position.set(60, 0, 0);
    const silo2Geom = new THREE.TorusGeometry(80, 28, 20, 70);
    const silo2Cloud = createParticleCloud(silo2Geom, colors.electricBlue, 1.8, 0.95);
    silo2.add(silo2Cloud);
    const silo2CoreGeom = new THREE.SphereGeometry(30, 16, 16);
    const silo2Core = createParticleCloud(silo2CoreGeom, colors.cyan, 2.0, 0.9);
    silo2.add(silo2Core);
    isolationGroup.add(silo2);

    // Silo 3: SETTLEMENT (Rotating Cylinder Monolith)
    const silo3 = new THREE.Group();
    silo3.position.set(-40, -280, 0);
    const silo3Geom = new THREE.CylinderGeometry(75, 75, 150, 32, 12, true);
    const silo3Cloud = createParticleCloud(silo3Geom, colors.cyan, 1.6, 0.85);
    silo3.add(silo3Cloud);
    isolationGroup.add(silo3);

    // =========================================================================
    // 4. AMBIENT STARFIELD (6,000 Stars with Hyperspace Warp capability)
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
    // 6. INTERACTION & CONTINUOUS MULTI-CHAPTER SCROLL ANIMATION LOOP
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

      // Scroll mapping across chapters:
      // Chapter 1: 0 - 0.45 * windowH
      // Chapter 2: 0.35 - 1.2 * windowH
      // Chapter 3: 1.1 - 2.0 * windowH
      // Chapter 4: 1.85 - 3.2 * windowH
      // Chapter 4 -> 5 Convergence Warp: 2.6 - 3.3 * windowH
      // Chapter 5: 3.1 - 5.0 * windowH
      const windowH = typeof window !== "undefined" ? window.innerHeight : 800;
      const ch1Progress = Math.min(scrollY / (windowH * 0.45), 1.0);
      const ch2Progress = Math.min(Math.max((scrollY - windowH * 0.3) / (windowH * 0.8), 0), 1.0);
      const ch3Progress = Math.min(Math.max((scrollY - windowH * 1.1) / (windowH * 0.8), 0), 1.0);
      const ch4Progress = Math.min(Math.max((scrollY - windowH * 1.85) / (windowH * 0.4), 0), 1.0);
      const ch4To5Warp = Math.min(Math.max((scrollY - windowH * 2.6) / (windowH * 0.6), 0), 1.0);

      // Camera Positioning: Smooth, gentle gliding with high damping
      const cameraPanX = (1.0 - ch4To5Warp) * ch4Progress * 160;
      const targetCamZ = 1200 - ch2Progress * 200 - ch3Progress * 200 - ch4Progress * 150 - ch4To5Warp * 50;
      camera.position.z += (targetCamZ - camera.position.z) * 0.035;
      camera.position.x += (targetX * 2.2 + cameraPanX - camera.position.x) * 0.03;
      camera.position.y += (-targetY * 2.2 - camera.position.y) * 0.03;
      camera.lookAt(scene.position);

      // Hero Sphere Expansion (Chapter 1): Slow, majestic orbit
      const heroScale = 1.0 + Math.pow(ch1Progress * 2.6, 2.2);
      heroGroup.scale.set(heroScale, heroScale, heroScale);
      heroGroup.rotation.y = time * 0.025;
      heroGroup.rotation.x = time * 0.012;

      if (ch1Progress < 0.7) {
        heroMaterial.opacity = 0.85;
      } else {
        heroMaterial.opacity = Math.max(0, 0.85 * (1.0 - (ch1Progress - 0.7) / 0.3));
      }

      // Radar Tunnel (Chapter 2 & 3 Expansion)
      if (scrollY < windowH * 0.15) {
        radarMainGroup.visible = false;
      } else {
        radarMainGroup.visible = true;
        const ch3Zoom = Math.min(Math.max((scrollY - windowH * 1.45) / (windowH * 0.65), 0), 1.0);
        const radarExpansion = 0.35 + ch2Progress * 0.65 + Math.pow(ch3Zoom * 2.2, 2.0);
        const radarZ = -500 + ch2Progress * 500 + Math.pow(ch3Zoom, 1.5) * 1200;
        
        radarMainGroup.position.z = radarZ;
        radarMainGroup.scale.set(radarExpansion, radarExpansion, radarExpansion);
        radarMainGroup.rotation.x = ch3Progress * 0.15 + ch3Zoom * 0.15;
        
        const radarFade = Math.max(0, 1.0 - Math.pow(ch3Zoom, 1.8) * 1.2);
        radarMainGroup.visible = radarFade > 0.01;
      }

      // Chapter 4: 3 Silos on the left, gentle drifting and smooth progressive expansion into Chapter 5
      const ch4SiloZoom = Math.min(Math.max((scrollY - windowH * 2.5) / (windowH * 0.65), 0), 1.0);
      
      if (ch4Progress > 0.01 && ch4SiloZoom < 0.99) {
        isolationGroup.visible = true;
        
        // Gentle progressive zoom expansion into camera
        const siloExpansion = 0.85 + ch4Progress * 0.15 + Math.pow(ch4SiloZoom * 2.2, 2.0);
        const siloZ = Math.pow(ch4SiloZoom, 1.5) * 1200;
        
        isolationGroup.position.z = siloZ;
        isolationGroup.scale.set(siloExpansion, siloExpansion, siloExpansion);
        
        // Gentle outward scatter
        isolationGroup.position.x = -360 - ch4SiloZoom * 240;
        silo1.position.y = 280 + ch4SiloZoom * 180 + Math.sin(time * 0.8) * 5;
        silo1.rotation.y += 0.005;
        silo1.rotation.x += 0.002;

        silo2.position.y = 0 + Math.sin(time * 0.9 + 1) * 6;
        silo2.rotation.x += 0.004;
        silo2.rotation.z += 0.003;

        silo3.position.y = -280 - ch4SiloZoom * 180 + Math.sin(time * 0.7 + 2) * 5;
        silo3.rotation.y += 0.005;
        silo3.rotation.z += 0.002;

        // Smooth fade out
        const siloFade = Math.max(0, 1.0 - Math.pow(ch4SiloZoom, 1.8) * 1.2);
        isolationGroup.visible = siloFade > 0.01;
      } else {
        isolationGroup.visible = false;
      }

      // Radar Rings: Calm, slow rotation
      radarRings.children.forEach((ring, i) => {
        ring.rotation.z += (ring.userData.speed || 0.0005) * 0.4;
        ring.rotation.y += 0.0001 * (i % 2 === 0 ? 1 : -1);
      });

      // Clusters rotation & gentle float
      clusters.children.forEach((cluster, i) => {
        cluster.rotation.y += 0.004;
        cluster.rotation.x += 0.002;
        cluster.position.y += Math.sin(time * 0.8 + i) * 0.1;
      });

      // Monoliths rotation: very slow
      monoliths.children.forEach((m) => {
        m.rotation.y += 0.0005;
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
        if (Math.abs(posArray[i * 3 + 1]) > 1000) posArray[i * 3] *= -0.95;
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
