"use client";

import { PointerEvent, ReactNode, useRef } from "react";

/** Wraps children in a glass card that subtly tilts in 3D toward the pointer, for a tactile "Liquid Glass" feel. */
export function TiltCard({ children, className }: { children: ReactNode; className?: string }) {
  const ref = useRef<HTMLDivElement>(null);

  function onPointerMove(event: PointerEvent<HTMLDivElement>) {
    const node = ref.current;
    if (!node) return;
    const bounds = node.getBoundingClientRect();
    const x = (event.clientX - bounds.left) / bounds.width - 0.5;
    const y = (event.clientY - bounds.top) / bounds.height - 0.5;
    node.style.transform = `perspective(900px) rotateX(${(-y * 8).toFixed(2)}deg) rotateY(${(x * 10).toFixed(2)}deg) translateZ(0)`;
  }

  function onPointerLeave() {
    const node = ref.current;
    if (node) node.style.transform = "perspective(900px) rotateX(0deg) rotateY(0deg)";
  }

  return (
    <div ref={ref} className={`tilt-card${className ? ` ${className}` : ""}`} onPointerMove={onPointerMove} onPointerLeave={onPointerLeave}>
      {children}
    </div>
  );
}
