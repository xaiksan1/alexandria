import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  reactCompiler: true,
  // standalone: pm2 tracks a single real server.js process instead of a
  // "next dev"/"next start" wrapper that hangs or forks an invisible child
  // (see ADAM/.claude/skills/nextjs-pm2-production-mode/SKILL.md).
  output: "standalone",
};

export default nextConfig;
