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
    scene.fog = new THREE.FogExp2(0x000000, 0.0004);

    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 3000);
    camera.position.z = 800;

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // --- State & Mouse Interaction ---
    const mouse = new THREE.Vector2();
    const targetRotation = new THREE.Vector2();

    const handleMouseMove = (e: MouseEvent) => {
      mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
      mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
    };
    window.addEventListener("mousemove", handleMouseMove);

    let scrollY = 0;
    const handleScroll = () => {
      scrollY = window.scrollY || window.pageYOffset;
    };
    window.addEventListener("scroll", handleScroll, { passive: true });

    // =========================================================================
    // 1. HERO PARTICLE MONOGRAM SPHERE (Top Scene)
    // =========================================================================
    const heroGroup = new THREE.Group();
    scene.add(heroGroup);

    const heroParticleCount = 15000;
    const heroPositions = new Float32Array(heroParticleCount * 3);
    const heroColors = new Float32Array(heroParticleCount * 3);
    const heroSizes = new Float32Array(heroParticleCount);

    const colorPrimary = new THREE.Color("#3395FF"); // Razorpay Electric Blue
    const colorSecondary = new THREE.Color("#E2E8F0"); // Luminescent Silver
    const colorAccent = new THREE.Color("#00C0F9"); // Ice Cyan

    for (let i = 0; i < heroParticleCount; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);
      const radius = 240 + Math.random() * 90;

      heroPositions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      heroPositions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      heroPositions[i * 3 + 2] = radius * Math.cos(phi);

      const mixedColor =
        i % 3 === 0
          ? colorPrimary
          : i % 3 === 1
          ? colorSecondary
          : colorAccent;
      heroColors[i * 3] = mixedColor.r;
      heroColors[i * 3 + 1] = mixedColor.g;
      heroColors[i * 3 + 2] = mixedColor.b;

      heroSizes[i] = Math.random() * 2.5 + 1.2;
    }

    const heroGeometry = new THREE.BufferGeometry();
    heroGeometry.setAttribute("position", new THREE.BufferAttribute(heroPositions, 3));
    heroGeometry.setAttribute("color", new THREE.BufferAttribute(heroColors, 3));
    heroGeometry.setAttribute("size", new THREE.BufferAttribute(heroSizes, 1));

    const heroMaterial = new THREE.PointsMaterial({
      size: 2.4,
      vertexColors: true,
      transparent: true,
      opacity: 0.85,
      blending: THREE.AdditiveBlending,
      sizeAttenuation: true,
    });

    const heroParticleSystem = new THREE.Points(heroGeometry, heroMaterial);
    heroGroup.add(heroParticleSystem);

    // =========================================================================
    // 2. RADAR TUNNEL & ARCHITECTURAL MONOLITHS (Stitch Scene 2)
    // =========================================================================
    const radarMainGroup = new THREE.Group();
    scene.add(radarMainGroup);

    const monolithGroup = new THREE.Group();
    const ringGroup = new THREE.Group();
    const clusterGroup = new THREE.Group();
    radarMainGroup.add(monolithGroup, ringGroup, clusterGroup);

    // --- 2A. Perimeter Architectural Monoliths ---
    function createMonolith(
      mWidth: number,
      mHeight: number,
      mDepth: number,
      color: number,
      x: number,
      y: number,
      z: number
    ) {
      const geo = new THREE.BoxGeometry(mWidth, mHeight, mDepth);
      const wireframe = new THREE.EdgesGeometry(geo);
      const mat = new THREE.LineBasicMaterial({
        color,
        transparent: true,
        opacity: 0.6,
      });
      const mesh = new THREE.LineSegments(wireframe, mat);
      mesh.position.set(x, y, z);

      // Particle points inside monolith
      const ptsCount = 1000;
      const ptsGeo = new THREE.BufferGeometry();
      const ptsPos = new Float32Array(ptsCount * 3);
      for (let i = 0; i < ptsCount; i++) {
        ptsPos[i * 3] = (Math.random() - 0.5) * mWidth;
        ptsPos[i * 3 + 1] = (Math.random() - 0.5) * mHeight;
        ptsPos[i * 3 + 2] = (Math.random() - 0.5) * mDepth;
      }
      ptsGeo.setAttribute("position", new THREE.BufferAttribute(ptsPos, 3));
      const ptsMat = new THREE.PointsMaterial({
        color,
        size: 1.6,
        transparent: true,
        opacity: 0.45,
      });
      const pts = new THREE.Points(ptsGeo, ptsMat);
      mesh.add(pts);

      return mesh;
    }

    // Left: Acquiring Bank
    monolithGroup.add(
      createMonolith(120, 600, 120, 0xffffff, -650, 0, 0)
    );
    // Right: Payment Processor
    monolithGroup.add(
      createMonolith(120, 700, 120, 0x3395ff, 650, 50, 0)
    );
    // Top: Issuing Bank
    monolithGroup.add(
      createMonolith(600, 80, 100, 0x00c0f9, 0, 450, -100)
    );
    // Bottom: Payment Gateway
    monolithGroup.add(
      createMonolith(500, 60, 100, 0x3395ff, 0, -450, -100)
    );

    // --- 2B. Concentric Tunnel Radar Orbit Rings ---
    for (let i = 0; i < 12; i++) {
      const radius = 200 + i * 80;
      const segments = 128;
      const ringGeometry = new THREE.BufferGeometry();
      const ringPositions = new Float32Array(segments * 3);
      for (let j = 0; j < segments; j++) {
        const theta = (j / segments) * Math.PI * 2;
        ringPositions[j * 3] = Math.cos(theta) * radius;
        ringPositions[j * 3 + 1] = Math.sin(theta) * radius;
        ringPositions[j * 3 + 2] = 0;
      }
      ringGeometry.setAttribute(
        "position",
        new THREE.BufferAttribute(ringPositions, 3)
      );
      const ringMaterial = new THREE.LineBasicMaterial({
        color: i % 2 === 0 ? 0x00c0f9 : 0x3395ff,
        transparent: true,
        opacity: 0.2 + (1 - i / 12) * 0.4,
      });
      const ring = new THREE.LineLoop(ringGeometry, ringMaterial);
      ring.rotation.x = Math.PI / 2.2;
      ring.userData = { speed: 0.001 * (i + 1) };
      ringGroup.add(ring);
    }

    // --- 2C. Four Inner Geometric Particle Clusters ---
    function createCluster(
      geo: THREE.BufferGeometry,
      color: number,
      x: number,
      y: number,
      z: number
    ) {
      const ptsCount = 2000;
      const ptsGeo = new THREE.BufferGeometry();
      const ptsPos = new Float32Array(ptsCount * 3);
      const posAttr = geo.attributes.position;
      for (let i = 0; i < ptsCount; i++) {
        const idx = Math.floor(Math.random() * posAttr.count);
        ptsPos[i * 3] = posAttr.getX(idx);
        ptsPos[i * 3 + 1] = posAttr.getY(idx);
        ptsPos[i * 3 + 2] = posAttr.getZ(idx);
      }
      ptsGeo.setAttribute("position", new THREE.BufferAttribute(ptsPos, 3));
      const ptsMat = new THREE.PointsMaterial({
        color,
        size: 2.2,
        transparent: true,
        opacity: 0.85,
        blending: THREE.AdditiveBlending,
      });
      const cluster = new THREE.Points(ptsGeo, ptsMat);
      cluster.position.set(x, y, z);
      return cluster;
    }

    const c1 = createCluster(new THREE.IcosahedronGeometry(40, 2), 0x00c0f9, 0, 150, 0); // Top (Cyan)
    const c2 = createCluster(new THREE.TorusGeometry(35, 12, 16, 100), 0xe2e8f0, 180, 80, 0); // Top-Right (Silver)
    const c3 = createCluster(new THREE.SphereGeometry(40, 32, 32), 0x3395ff, -180, -80, 0); // Bottom-Left (Blue)
    const c4 = createCluster(new THREE.SphereGeometry(45, 16, 16), 0xffffff, 180, -120, 0); // Bottom-Right (White)
    clusterGroup.add(c1, c2, c3, c4);

    // =========================================================================
    // 3. AMBIENT STARFIELD (5,000 background stars)
    // =========================================================================
    const starCount = 5000;
    const starGeo = new THREE.BufferGeometry();
    const starPos = new Float32Array(starCount * 3);
    for (let i = 0; i < starCount; i++) {
      starPos[i * 3] = (Math.random() - 0.5) * 3000;
      starPos[i * 3 + 1] = (Math.random() - 0.5) * 3000;
      starPos[i * 3 + 2] = (Math.random() - 0.5) * 2000 - 1000;
    }
    starGeo.setAttribute("position", new THREE.BufferAttribute(starPos, 3));
    const starMat = new THREE.PointsMaterial({
      color: 0xffffff,
      size: 1.2,
      transparent: true,
      opacity: 0.5,
    });
    const stars = new THREE.Points(starGeo, starMat);
    scene.add(stars);

    // =========================================================================
    // 4. ANIMATION LOOP & SCROLL EXPANSION
    // =========================================================================
    let animationFrameId: number;

    const animate = (t: number) => {
      animationFrameId = requestAnimationFrame(animate);
      const time = t * 0.001;

      // Mouse Parallax easing
      targetRotation.x += (mouse.y * 0.06 - targetRotation.x) * 0.05;
      targetRotation.y += (mouse.x * 0.06 - targetRotation.y) * 0.05;

      monolithGroup.rotation.x = targetRotation.x;
      monolithGroup.rotation.y = targetRotation.y;

      // Scroll interpolation (0 at top, 1 at full scroll depth)
      const windowH = typeof window !== "undefined" ? window.innerHeight : 800;
      const scrollProgress = Math.min(scrollY / (windowH * 0.85), 1.0);

      // Hero Sphere Expansion: expands "big, big, big, big, big" & disperses
      const heroScale = 1.0 + Math.pow(scrollProgress * 2.8, 2.5);
      heroGroup.scale.set(heroScale, heroScale, heroScale);
      heroGroup.rotation.y = time * 0.08;
      heroGroup.rotation.x = time * 0.04;

      if (scrollProgress < 0.35) {
        heroMaterial.opacity = 0.85;
      } else {
        heroMaterial.opacity = Math.max(
          0,
          0.85 * (1.0 - (scrollProgress - 0.35) / 0.45)
        );
      }

      // Radar Tunnel & Monoliths reveal as hero sphere opens
      if (scrollProgress < 0.15) {
        radarMainGroup.visible = false;
      } else {
        radarMainGroup.visible = true;
        const radarProgress = Math.min(
          Math.max((scrollProgress - 0.15) / 0.85, 0),
          1.0
        );

        // Zoom from depth z: -400 to z: 0
        radarMainGroup.position.z = -400 + radarProgress * 400;
        const radarScale = 0.3 + radarProgress * 0.7;
        radarMainGroup.scale.set(radarScale, radarScale, radarScale);
      }

      // Ring rotation at variable speeds
      ringGroup.children.forEach((ring) => {
        ring.rotation.z += ring.userData.speed;
      });

      // Cluster rotation on their own axes
      clusterGroup.children.forEach((c) => {
        c.rotation.y += 0.012;
        c.rotation.x += 0.006;
      });

      // Stars subtle rotation
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
