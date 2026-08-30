import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AllSlate",
  description: "A grounded workspace for your documents and questions.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}