import type { Metadata, Viewport } from "next";
import Link from "next/link";
import "@fontsource/noto-serif-georgian/400.css";
import "@fontsource/noto-serif-georgian/600.css";
import "@fontsource/noto-serif-georgian/700.css";
import "katex/dist/katex.min.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "Modeling & Simulation — Exam Quiz",
  description: "Practice quiz built from the Modeling and Simulation midterm exam variants.",
};

export const viewport: Viewport = {
  themeColor: "#ffffff",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ka">
      <body>
        <header className="site-head">
          <Link href="/" className="brand">
            Modeling &amp; Simulation
          </Link>
          <nav className="site-nav" aria-label="Primary">
            <Link href="/variants">Variants</Link>
            <Link href="/practice">All questions</Link>
          </nav>
        </header>
        <main>{children}</main>
      </body>
    </html>
  );
}
