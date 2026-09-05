import type { NextConfig } from "next";
import fs from "fs";

const isDocker = fs.existsSync("/.dockerenv") || process.env.RUNNING_IN_DOCKER === "1";
const backendHost =
  process.env.INTERNAL_BACKEND_URL || (isDocker ? "http://backend:8000" : "http://localhost:8000");

const nextConfig: NextConfig = {
  skipTrailingSlashRedirect: true,
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "images.unsplash.com",
      },
    ],
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendHost}/api/:path*`,
      },
      {
        source: "/api-proxy/:path*",
        destination: `${backendHost}/api/:path*`,
      },
      {
        source: "/pay/:path*",
        destination: `${backendHost}/pay/:path*`,
      },
    ];
  },
};

export default nextConfig;
