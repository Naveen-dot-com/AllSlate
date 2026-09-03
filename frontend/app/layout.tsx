import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AllSlate",
  description: "A grounded workspace for your documents and questions.",
};

// Inline, blocking script: applies the saved theme before first paint so there is no flash-of-wrong-theme.
const THEME_INIT_SCRIPT = `
  (function () {
    try {
      var stored = window.localStorage.getItem("allslate-theme");
      var prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      var theme = stored === "light" || stored === "dark" ? stored : prefersDark ? "dark" : "light";
      document.documentElement.dataset.theme = theme;
    } catch (e) {}
  })();
`;

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
      </head>
      <body>{children}</body>
    </html>
  );
}