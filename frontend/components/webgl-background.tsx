"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

function resolvePalette() {
  const theme = document.documentElement.dataset.theme ?? "light";
  return theme === "dark"
    ? [0x5dd2ba, 0x8ab4f8, 0xf3c98b]
    : [0x7fd8c4, 0x8ab4f8, 0xe7b779];
}

export function WebGLBackground() {
  const mountRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const mountNode = mountRef.current;
    if (!mountNode || !("WebGLRenderingContext" in window)) {
      return;
    }

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: "low-power",
    });

    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
    renderer.setClearColor(0x000000, 0);
    mountNode.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(30, window.innerWidth / window.innerHeight, 0.1, 100);
    camera.position.set(0, 0, 8);

    const group = new THREE.Group();
    scene.add(group);

    const palette = resolvePalette();
    const materials = [
      new THREE.MeshPhysicalMaterial({
        color: palette[0],
        emissive: palette[0],
        emissiveIntensity: 0.18,
        transparent: true,
        opacity: 0.6,
        roughness: 0.24,
        metalness: 0.12,
        transmission: 0.12,
        thickness: 0.8,
      }),
      new THREE.MeshPhysicalMaterial({
        color: palette[1],
        emissive: palette[1],
        emissiveIntensity: 0.16,
        transparent: true,
        opacity: 0.55,
        roughness: 0.28,
        metalness: 0.1,
        transmission: 0.1,
        thickness: 0.7,
      }),
      new THREE.MeshPhysicalMaterial({
        color: palette[2],
        emissive: palette[2],
        emissiveIntensity: 0.14,
        transparent: true,
        opacity: 0.5,
        roughness: 0.3,
        metalness: 0.1,
        transmission: 0.08,
        thickness: 0.7,
      }),
    ];

    const orbA = new THREE.Mesh(new THREE.IcosahedronGeometry(1.7, 1), materials[0]);
    orbA.position.set(-2.5, 0.8, 0.2);

    const orbB = new THREE.Mesh(new THREE.OctahedronGeometry(1.9, 0), materials[1]);
    orbB.position.set(1.8, -0.8, -0.8);

    const orbC = new THREE.Mesh(new THREE.DodecahedronGeometry(1.5, 0), materials[2]);
    orbC.position.set(0.4, 2.1, 0.5);

    group.add(orbA, orbB, orbC);

    const particles = new THREE.Group();
    const particleGeometry = new THREE.SphereGeometry(0.045, 12, 12);
    const particleMaterial = new THREE.MeshBasicMaterial({ color: palette[1], transparent: true, opacity: 0.7 });

    for (let i = 0; i < 28; i += 1) {
      const particle = new THREE.Mesh(particleGeometry, particleMaterial.clone());
      particle.position.set(
        (Math.random() - 0.5) * 12,
        (Math.random() - 0.5) * 8,
        (Math.random() - 0.5) * 8
      );
      particle.scale.setScalar(0.9 + Math.random() * 1.6);
      particles.add(particle);
    }

    group.add(particles);

    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const resize = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    };

    const updatePalette = () => {
      const nextPalette = resolvePalette();
      materials[0].color.setHex(nextPalette[0]);
      materials[1].color.setHex(nextPalette[1]);
      materials[2].color.setHex(nextPalette[2]);
      materials[0].emissive.setHex(nextPalette[0]);
      materials[1].emissive.setHex(nextPalette[1]);
      materials[2].emissive.setHex(nextPalette[2]);
      particleMaterial.color.setHex(nextPalette[1]);
    };

    const themeObserver = new MutationObserver(updatePalette);
    themeObserver.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-theme"],
    });

    resize();
    window.addEventListener("resize", resize);

    let animationId = 0;
    const tick = (time: number) => {
      const seconds = time * 0.001;

      if (!prefersReducedMotion) {
        group.rotation.x = Math.sin(seconds * 0.55) * 0.4;
        group.rotation.y = seconds * 0.32;
        group.rotation.z = Math.cos(seconds * 0.38) * 0.3;

        orbA.position.x = -2.5 + Math.sin(seconds * 0.9) * 0.8;
        orbB.position.y = -0.8 + Math.cos(seconds * 1.1) * 0.7;
        orbC.position.x = 0.4 + Math.sin(seconds * 1.3) * 0.8;
        particles.rotation.y = -seconds * 0.18;
      }

      renderer.render(scene, camera);
      animationId = window.requestAnimationFrame(tick);
    };

    animationId = window.requestAnimationFrame(tick);

    return () => {
      window.cancelAnimationFrame(animationId);
      window.removeEventListener("resize", resize);
      themeObserver.disconnect();
      mountNode.removeChild(renderer.domElement);
      renderer.dispose();
      materials.forEach((material) => material.dispose());
      particleMaterial.dispose();
    };
  }, []);

  return <div ref={mountRef} className="webgl-background" aria-hidden="true" />;
}
