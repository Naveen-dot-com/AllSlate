import { fileURLToPath } from "node:url";
import path from "node:path";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const apiBaseUrl = process.env.ALLSLATE_API_URL ?? process.env.NEXT_PUBLIC_ALLSLATE_API_URL;

const nextConfig = {
  reactStrictMode: true,
  devIndicators: false,
  turbopack: {
    root: __dirname,
  },
  async rewrites() {
    if (!apiBaseUrl) {
      return [];
    }

    return [
      {
        source: "/api/:path*",
        destination: `${apiBaseUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;