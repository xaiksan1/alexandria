import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Link from "next/link";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Agentic-Ads | Alexandria Layer 8",
  description: "Autonomous advertising platform — THE ALL-SPARKS",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body className={`${inter.className} bg-gray-950 text-gray-100 min-h-screen`}>
        <nav className="border-b border-gray-800 px-6 py-3 flex gap-6 text-sm">
          <Link href="/" className="font-bold text-emerald-400">Agentic-Ads</Link>
          <Link href="/cache" className="text-gray-400 hover:text-white">Cache</Link>
          <Link href="/bids" className="text-gray-400 hover:text-white">Bids</Link>
          <Link href="/revenue" className="text-gray-400 hover:text-white">Revenue</Link>
          <Link href="/proof" className="text-gray-400 hover:text-white">Proof</Link>
        </nav>
        <main className="p-6">{children}</main>
      </body>
    </html>
  );
}
