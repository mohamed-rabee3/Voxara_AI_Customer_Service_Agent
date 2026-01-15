import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // React strict mode for development
  reactStrictMode: true,

  // Environment variables exposed to the client
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
    NEXT_PUBLIC_LIVEKIT_URL: process.env.NEXT_PUBLIC_LIVEKIT_URL || "",
  },

  // Image optimization domains (if needed)
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**.livekit.cloud",
      },
    ],
  },

  // Webpack configuration for LiveKit
  webpack: (config) => {
    // Ensure proper resolution of ES modules
    config.resolve.extensionAlias = {
      ".js": [".ts", ".tsx", ".js", ".jsx"],
    };
    return config;
  },
};

export default nextConfig;
