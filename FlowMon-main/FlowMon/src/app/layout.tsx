import type { Metadata } from "next";
import "./globals.css";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";

export const metadata: Metadata = {
  title: "RayzorFlow — Commerce Agent Orchestrator",
  description:
    "Visual multi-agent orchestration for commerce operations. Compose, govern, and run Razorpay-focused workflows in parallel.",
  icons: { icon: "/favicon.ico" },
  openGraph: {
    title: "RayzorFlow — Commerce Agent Orchestrator",
    description: "Parallel commerce workflows with governed agent hand-offs.",
    url: siteUrl,
    siteName: "RayzorFlow",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "RayzorFlow — Commerce Agent Orchestrator",
    description: "Parallel commerce workflows with governed agent hand-offs.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
