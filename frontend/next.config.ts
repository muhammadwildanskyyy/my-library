import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactCompiler: true,

  // Enable standalone output for Docker — menghasilkan server.js minimal
  output: "standalone",
};

export default nextConfig;
