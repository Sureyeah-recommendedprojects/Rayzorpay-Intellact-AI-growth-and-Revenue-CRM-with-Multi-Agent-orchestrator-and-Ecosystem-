import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "**.ipfs.io" },
      { protocol: "https", hostname: "assets.coingecko.com" },
    ],
  },
  env: {
    NEXT_PUBLIC_SITE_URL:
      process.env.NEXT_PUBLIC_SITE_URL ??
      (process.env.VERCEL_URL
        ? `https://${process.env.VERCEL_URL}`
        : "http://localhost:3000"),
  },
  reactStrictMode: false,

  // Silence MetaMask SDK + WalletConnect missing-module warnings
  webpack: (config, { isServer }) => {
    // --- Fix: "@react-native-async-storage/async-storage" not found ---
    // MetaMask SDK bundles a react-native import that doesn't exist in web.
    // --- Fix: "pino-pretty" not found ---
    // WalletConnect's pino logger optionally imports pino-pretty.
    config.resolve.fallback = {
      ...config.resolve.fallback,
      "@react-native-async-storage/async-storage": false,
      "pino-pretty": false,
    };

    // On the server side, stub out browser-only globals that
    // WalletConnect / MetaMask SDK try to access at import time
    // (fixes "indexedDB is not defined").
    if (isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        "fake-indexeddb": false,
        "fake-indexeddb/auto": false,
      };
    }

    // Ignore optional native modules that never exist in the browser
    config.externals = [
      ...(Array.isArray(config.externals) ? config.externals : config.externals ? [config.externals] : []),
    ];

    return config;
  },

  // Mark packages that should never be bundled for the server
  serverExternalPackages: ["pino-pretty"],
};

export default nextConfig;
