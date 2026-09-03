"use client";

import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";

const STORAGE_KEY = "allslate-theme";

/** Light/dark toggle for the Liquid Glass theme; persists choice and avoids a flash-of-wrong-theme on load. */
export function ThemeToggle() {
  const [theme, setTheme] = useState<"light" | "dark">("light");

  useEffect(() => {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    const initial = stored === "dark" || stored === "light" ? stored : document.documentElement.dataset.theme === "dark" ? "dark" : "light";
    setTheme(initial as "light" | "dark");
  }, []);

  function toggle() {
    const next = theme === "light" ? "dark" : "light";
    setTheme(next);
    document.documentElement.dataset.theme = next;
    window.localStorage.setItem(STORAGE_KEY, next);
  }

  return (
    <button type="button" className="theme-toggle" onClick={toggle} title="Toggle light / dark theme" aria-label="Toggle light / dark theme">
      {theme === "light" ? <Moon size={16} /> : <Sun size={16} />}
    </button>
  );
}
