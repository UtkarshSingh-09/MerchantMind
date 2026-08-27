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
    scene.fog = new THREE.FogExp2(0x000000, 0.0006);

    const camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 4000);
    camera.position.set(0, 0, 16);

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    const colorPrimary = new THREE.Color("#3395FF"); // Razorpay Electric Blue
    const colorSecondary = new THREE.Color("#E2E8F0"); // Luminescent Silver
    const colorAccent = new THREE.Color("#00C0F9"); // Ice Cyan

    // 1. Hero Particle Monogram Sphere (15,000 points)
    const particleCount = 15000;
    const positions = new Float32Array(particleCount * 3);
    const originalPositions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);
    const sizes = new Float32Array(particleCount);

    for (let i = 0; i < particleCount; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);
      const radius = 4.8 + Math.random() * 2.0;

      const px = radius * Math.sin(phi) * Math.cos(theta);
      const py = radius * Math.sin(phi) * Math.sin(theta);
      const pz = radius * Math.cos(phi);

      positions[i * 3] = px;
      positions[i * 3 + 1] = py;
      positions[i * 3 + 2] = pz;

      originalPositions[i * 3] = px;
      originalPositions[i * 3 + 1] = py;
      originalPositions[i * 3 + 2] = pz;

      const mixedColor =
        i % 3 === 0
          ? colorPrimary
          : i % 3 === 1
          ? colorSecondary
          : colorAccent;
      colors[i * 3] = mixedColor.r;
      colors[i * 3 + 1] = mixedColor.g;
      colors[i * 3 + 2] = mixedColor.b;

      sizes[i] = Math.random() * 1.8 + 0.6;
    }

    const heroGeometry = new THREE.BufferGeometry();
    heroGeometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    heroGeometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    heroGeometry.setAttribute("size", new THREE.BufferAttribute(sizes, 1));

    const heroMaterial = new THREE.PointsMaterial({
      size: 0.06,
      vertexColors: true,
      transparent: true,
      opacity: 0.85,
      blending: THREE.AdditiveBlending,
      sizeAttenuation: true,
    });

    const heroParticleSystem = new THREE.Points(heroGeometry, heroMaterial);
    scene.add(heroParticleSystem);

    // 2. Dense Starfield (8,000 background stars)
    const starCount = 8000;
    const starPos = new Float32Array(starCount * 3);
    for (let i = 0; i < starCount * 3; i++) {
      starPos[i] = (Math.random() - 0.5) * 3500;
    }
    const starGeo = new THREE.BufferGeometry();
    starGeo.setAttribute("position", new THREE.BufferAttribute(starPos, 3));
    const starMat = new THREE.PointsMaterial({
      color: 0xffffff,
      size: 0.8,
      transparent: true,
      opacity: 0.45,
      sizeAttenuation: true,
    });
    const starField = new THREE.Points(starGeo, starMat);
    scene.add(starField);

    // 3. Central Multi-Node Network (Hub, Orbital Rings, Wireframe Nodes)
    const hubGroup = new THREE.Group();
    hubGroup.position.set(0, 0, -60); // Starts deep behind
    hubGroup.scale.set(0.1, 0.1, 0.1);
    scene.add(hubGroup);

    // Central Icosahedron Hub
    const hubGeo = new THREE.IcosahedronGeometry(4.5, 2);
    const hubMat = new THREE.MeshPhongMaterial({
      color: 0x3395ff,
      emissive: 0x00c0f9,
      emissiveIntensity: 0.7,
      wireframe: true,
      transparent: true,
      opacity: 0.85,
    });
    const hub = new THREE.Mesh(hubGeo, hubMat);
    hubGroup.add(hub);

    // Inner Glowing Core
    const innerHubGeo = new THREE.SphereGeometry(2.0, 24, 24);
    const innerHubMat = new THREE.MeshBasicMaterial({ color: 0x3395ff });
    const innerHub = new THREE.Mesh(innerHubGeo, innerHubMat);
    hubGroup.add(innerHub);

    // Concentric Orbital Rings
    function createRing(radius: number, rx: number, rz: number, color: number, opacity: number) {
      const curve = new THREE.EllipseCurve(0, 0, radius, radius * 0.72, 0, 2 * Math.PI, false, 0);
      const points = curve.getPoints(180);
      const geometry = new THREE.BufferGeometry().setFromPoints(points);
      const material = new THREE.LineBasicMaterial({
        color,
        transparent: true,
        opacity,
      });
      const ring = new THREE.Line(geometry, material);
      ring.rotation.x = rx;
      ring.rotation.z = rz;
      return ring;
    }

    const rings = [
      createRing(14, Math.PI / 2.2, 0.1, 0x3395ff, 0.45),
      createRing(22, Math.PI / 2.15, -0.15, 0x4b5563, 0.35),
      createRing(30, Math.PI / 2.1, -0.2, 0x38bdf8, 0.3),
      createRing(38, Math.PI / 2.25, 0.3, 0x3395ff, 0.2),
      createRing(46, Math.PI / 2.3, 0.45, 0x38bdf8, 0.15),
    ];
    rings.forEach((r) => hubGroup.add(r));

    // Dynamic Wireframe Nodes
    const nodes = new THREE.Group();
    hubGroup.add(nodes);
    const nodeCount = 20;
    const connectors: THREE.Line[] = [];

    for (let i = 0; i < nodeCount; i++) {
      const angle = (i / nodeCount) * Math.PI * 2;
      const radius = 16 + (i % 3) * 8;
      const x = Math.cos(angle) * radius;
      const z = Math.sin(angle) * radius;
      const y = ((i % 4) - 1.5) * 3;

      const isPill = i % 3 === 0;
      const geo = isPill
        ? new THREE.SphereGeometry(0.7, 16, 16)
        : new THREE.BoxGeometry(1.2, 1.6, 1.2);

      const mat = new THREE.MeshPhongMaterial({
        color: i % 4 === 0 ? 0x3395ff : 0xe2e8f0,
        emissive: i % 4 === 0 ? 0x00c0f9 : 0x3395ff,
        emissiveIntensity: 0.5,
        wireframe: !isPill,
        transparent: true,
        opacity: 0.9,
      });

      const mesh = new THREE.Mesh(geo, mat);
      mesh.position.set(x, y, z);
      mesh.userData = { originalY: y, phase: Math.random() * Math.PI * 2 };
      nodes.add(mesh);

      const lineGeo = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(0, 0, 0),
        new THREE.Vector3(x, y, z),
      ]);
      const lineMat = new THREE.LineBasicMaterial({
        color: 0x3395ff,
        transparent: true,
        opacity: 0.22,
      });
      const line = new THREE.Line(lineGeo, lineMat);
      hubGroup.add(line);
      connectors.push(line);
    }

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
    scene.add(ambientLight);
    const pointLight = new THREE.PointLight(0x3395ff, 3, 300);
    pointLight.position.set(0, 5, 10);
    scene.add(pointLight);

    // Mouse & Scroll Tracking
    let mouseX = 0;
    let mouseY = 0;
    let targetMouseX = 0;
    let targetMouseY = 0;
    let scrollY = 0;

    const handleMouseMove = (e: MouseEvent) => {
      targetMouseX = (e.clientX / window.innerWidth) * 2 - 1;
      targetMouseY = -(e.clientY / window.innerHeight) * 2 + 1;
    };

    const handleScroll = () => {
      scrollY = window.scrollY || window.pageYOffset;
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("scroll", handleScroll, { passive: true });

    let animationFrameId: number;

    const animate = (t: number) => {
      animationFrameId = requestAnimationFrame(animate);
      const time = t * 0.0006;

      // Mouse easing
      mouseX += (targetMouseX - mouseX) * 0.05;
      mouseY += (targetMouseY - mouseY) * 0.05;

      // Scroll Progress Normalized (0 at top, 1 at full scroll depth)
      const windowH = typeof window !== "undefined" ? window.innerHeight : 800;
      const scrollProgress = Math.min(scrollY / (windowH * 0.9), 1.0);

      // =========================================================================
      // 1. HERO SPHERE: Expands "big, big, big, big, big" & opens up
      // =========================================================================
      const expansionFactor = 1.0 + Math.pow(scrollProgress * 2.8, 2.4);
      heroParticleSystem.scale.set(expansionFactor, expansionFactor, expansionFactor);

      // Hero rotation & breathing pulse
      heroParticleSystem.rotation.y = time * 0.12;
      heroParticleSystem.rotation.x = time * 0.06;

      // Hero Opacity: Stays solid initially, fades as it opens past the screen (progress > 0.45)
      if (scrollProgress < 0.45) {
        heroMaterial.opacity = 0.85;
      } else {
        const fadeOut = Math.max(0, 0.85 * (1.0 - (scrollProgress - 0.45) / 0.45));
        heroMaterial.opacity = fadeOut;
      }

      // =========================================================================
      // 2. MULTI-NODE NETWORK: Arrives into the center when hero sphere opens
      // =========================================================================
      if (scrollProgress < 0.2) {
        hubGroup.visible = false;
      } else {
        hubGroup.visible = true;
        // Smooth ease-in for the multi-node network (0 at 0.2, 1 at 1.0)
        const netProgress = Math.min(Math.max((scrollProgress - 0.2) / 0.8, 0), 1.0);

        // Position: Moves from depth z: -60 to z: 0, and lower down to y: -5.5
        const hubZ = -60 + netProgress * 60;
        const hubY = -5.5 * netProgress;
        hubGroup.position.set(0, hubY, hubZ);

        // Isometric tilt so the orbital rings spread horizontally like a planetary disc
        hubGroup.rotation.x = 0.45;

        // Scale: Scales up from 0.1 to 1.05
        const hubScale = 0.1 + netProgress * 0.95;
        hubGroup.scale.set(hubScale, hubScale, hubScale);
      }

      // Hub & Rings Rotation
      hub.rotation.y += 0.005;
      hub.rotation.z += 0.002;
      rings.forEach((r, i) => {
        r.rotation.z += 0.0008 * (i + 1);
      });

      // Animated floating nodes
      nodes.children.forEach((n, i) => {
        const mesh = n as THREE.Mesh;
        mesh.position.y =
          mesh.userData.originalY + Math.sin(time * 2 + mesh.userData.phase) * 1.0;
        mesh.rotation.y += 0.01;

        if (connectors[i]) {
          const linePos = connectors[i].geometry.attributes.position.array as Float32Array;
          linePos[3] = mesh.position.x;
          linePos[4] = mesh.position.y;
          linePos[5] = mesh.position.z;
          connectors[i].geometry.attributes.position.needsUpdate = true;
        }
      });

      // Camera parallax looking slightly down towards the horizon
      camera.position.x = mouseX * 2.0;
      camera.position.y = mouseY * 1.5 + 2.0;
      camera.lookAt(0, -1.5, 0);

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
