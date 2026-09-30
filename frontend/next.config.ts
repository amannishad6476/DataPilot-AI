import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Optional rewrites to proxy API requests to backend when BACKEND_URL is set
  async rewrites() {
    const backendUrl = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL;
    if (backendUrl && !backendUrl.startsWith('/') && !backendUrl.includes('localhost:8000')) {
      const target = backendUrl.replace(/\/api\/?$/, '');
      return [
        {
          source: '/api/:path*',
          destination: `${target}/api/:path*`,
        },
      ];
    }
    return [];
  },
};

export default nextConfig;
